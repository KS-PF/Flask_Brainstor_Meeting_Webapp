import functools
from project.functions import (
    secure_response_headers, token_check,
    form_validation, int_check, replace_str,
)
from project.room import get_room_owner
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for,
)
from werkzeug.exceptions import abort
from project.auth import login_required 
from project.db import get_db 
from werkzeug.security import check_password_hash 


bp = Blueprint('meeting', __name__) 




def auth_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if session.get('session_room_id') is None or session.get('session_room_name') is None:
            session['session_room_id'] = None
            session['session_room_name'] = None
            response_data =   redirect(url_for('meeting.auth'))
            return secure_response_headers(response_data)

        return view(**kwargs)

    return wrapped_view




def get_post(id, check_author=True, check_room=True, check_vote=False):

    try:
        id = int(id)  
    except ValueError:
        abort(404, f"「Post ID」には数値を入力してだくさい。")
    else:
        post = get_db().execute(
            'SELECT p.id, author_id, room_id, created, main, edit, public'
            ' FROM posts p JOIN users u ON p.author_id = u.id'
            ' WHERE p.id = ?',
            (id,)
        ).fetchone()

        if post is None:
            abort(404, f"「Post ID {id}」は存在しません。")  # 投稿が存在しない場合404エラー

        if check_author and post['author_id'] != g.user['id']:
            abort(403, "現在のログイン中のユーザーはこのポストの編集権限を持ちません")  # 投稿の著者が現在のユーザーでない場合403エラー

        if check_vote and post['author_id'] == g.user['id']:
            abort(403, "自分の投稿に投票することはできません")  # 投稿の著者が現在のユーザーと同じ場合403エラー
    
        if check_room and post['room_id'] != session.get('session_room_id'):
            session['session_room_id'] = None
            session['session_room_name'] = None
            abort(401, f"「Room ID {post['room_id']}」への参加権限がありません")  # Unauthorized
            
        return post  # 投稿を返す




def room_id_check(param):
    if param != session['session_room_name']:
        session['session_room_id'] = None
        session['session_room_name'] = None
        abort(401, f"「Room ID {param}」への参加権限がありません")




@bp.route('/')
def index():
    id = session.get('id')  # セッションからユーザーIDを取得
    user_id = session.get('user_id')  # セッションからユーザーIDを取得
    if id is not None and user_id is not None:
        get_room_owner(g.user['id'])

    session['session_room_id'] = None
    session['session_room_name'] = None
    response_data =  render_template('meeting/index.html') 
    return secure_response_headers(response_data)




@bp.route('/room/auth', methods=('GET', 'POST'))
@login_required  # ログインが必要なルート
def auth():
    if request.method == 'POST':
        # フォームがPOSTされた場合、フォームデータを取得
        room_id = request.form.get('room_id', default=None, type=str)
        password = request.form.get('password', default=None, type=str)
        post_token = request.form.get('token', default=None, type=str)

        error = None
        # フォームの検証
        error = form_validation(room_id, error, "ルームID", rex = True, hidden = False,
                                len_check = True, len_min = 8, len_max = 48,)
        error = form_validation(password, error, "パスワード", rex = True, hidden = False,
                                len_check = True, len_min = 8, len_max = 48,)
        error = form_validation(post_token, error, "", rex = False, hidden = True,
                                len_check = False, len_min = 0, len_max = 0,)

        if error is None:
            db = get_db()  # データベース接続を取得
            # データベースからユーザーを取得
            data = db.execute(
                'SELECT * FROM rooms WHERE room_name = ?', (room_id,)
            ).fetchone()

        if error is None and token_check('check', post_token) == False:
            error = 'もう一度入力してください'
        elif error is None and data is None:
            error = 'ERROR:ルームID、もしくはパスワードが間違っています'
        elif error is None and not check_password_hash(data['password'], password):
            error = 'ERROR:ルームID、もしくはパスワードが間違っています'

        if error is None:
            # エラーがない場合、セッションをクリアして新しいルームIDを設定
            session['session_room_id'] = data['id']
            session['session_room_name'] = data['room_name']
            response_data =   redirect(url_for('meeting.meeting', room_id=room_id))  
            return secure_response_headers(response_data)# インデックスページにリダイレクト

        flash(error)  # エラーメッセージを表示

    token = token_check('set')
    response_data = render_template('meeting/auth.html', token = token)
    return secure_response_headers(response_data)




@bp.route('/room/<string:room_id>', methods=('GET', 'POST'))
@login_required  # ログインが必要なルート
@auth_required
def meeting(room_id):
    room_id_check(room_id)
    
    db = get_db()  # データベース接続を取得
    rooms_id = session.get('session_room_id')
    user_id = g.user['id']
    posts = db.execute(
        'SELECT p.id, author_id, room_id, created, main, edit, public,u.nickname,'
        '(SELECT COUNT(*) FROM votes v WHERE v.post_id = p.id) AS vote_count,'
        '(SELECT COUNT(*) FROM votes v WHERE v.post_id = p.id AND v.user_id = ?) AS vote_user'
        ' FROM posts p JOIN users u ON p.author_id = u.id'
        ' WHERE room_id = ?'
        ' ORDER BY created DESC',
        (user_id,rooms_id,)
    ).fetchall()  # 投稿を取得、ユーザー情報と結合して作成日の降順で並べ替え
    response_data =  render_template('meeting/brainstorm/meeting.html', posts=posts, room_id=room_id)  # テンプレートに投稿を渡してレンダリング
    return secure_response_headers(response_data)




@bp.route('/room/<string:room_id>/post', methods=('GET', 'POST'))
@login_required  # ログインが必要なルート
@auth_required
def post(room_id):
    room_id_check(room_id)
    if request.method == 'POST':
        main = request.form.get('main', default=None, type=str)  # フォームからタイトルを取得
        post_token = request.form.get('token', default=None, type=str)

        error = None

        error = form_validation(main, error, "投稿内容", rex = False, hidden = False,
                                len_check = True, len_min = 3, len_max = 148,)
        error = form_validation(post_token, error, "", rex = False, hidden = True,
                                len_check = False, len_min = 0, len_max = 0,)
        
        main = replace_str(main)
        
        if error is None and token_check('check', post_token) == False:
            error = 'もう一度入力してください'

        if error is not None:
            flash(error)  # エラーメッセージを表示     
        else:
            author_id = g.user['id']
            rooms_id = session.get('session_room_id')
            db = get_db()  # データベース接続を取得
            db.execute(
                'INSERT INTO posts (author_id, room_id, main, edit, public)'
                ' VALUES (?, ?, ?, ?, ?)',
                (author_id, rooms_id, main, 0, 0,)
            )  # 新しい投稿をデータベースに挿入
            db.commit()  # 変更をコミット
            response_data =   redirect(url_for('meeting.meeting', room_id=room_id))  
            return secure_response_headers(response_data)# インデックスページにリダイレクト

    token = token_check('set')
    response_data =  render_template('meeting/brainstorm/post.html', room_id=room_id, token = token)  # 作成ページをレンダリング
    return secure_response_headers(response_data)




@bp.route('/room/<string:room_id>/update/<int:post_id>', methods=('GET', 'POST'))
@login_required  # ログインが必要なルート
@auth_required
def update(room_id,post_id):
    room_id_check(room_id)
    post = get_post(post_id)  # 投稿を取得

    if request.method == 'POST':
        post_id = int_check(post_id)
        main = request.form.get('main', default=None, type=str) # フォームからタイトルを取得
        post_token = request.form.get('token', default=None, type=str)

        error = None

        error = form_validation(main, error, "投稿内容", rex = False, hidden = False,
                                len_check = True, len_min = 3, len_max = 148,)
        error = form_validation(post_token, error, "", rex = False, hidden = True,
                                len_check = False, len_min = 0, len_max = 0,)
        
        main = replace_str(main)
        
        if error is None and token_check('check', post_token) == False:
            error = 'もう一度入力してください'

        if error is not None:
            flash(error)  # エラーメッセージを表示
        else:
            db = get_db()  # データベース接続を取得
            db.execute(
                'UPDATE posts SET  main = ?, edit = 1 '
                ' WHERE id = ?',
                (main, post_id)
            )  # 投稿を更新
            db.commit()  # 変更をコミット

            id_num = "#" + str(post_id)

            response_data =   redirect(url_for('meeting.meeting', room_id=room_id) + id_num)  
            return secure_response_headers(response_data)# インデックスページにリダイレクト

    token = token_check('set')
    response_data =  render_template('meeting/brainstorm/update.html', post=post, room_id =room_id, post_id = post_id, token = token)  # 更新ページをレンダリング
    return secure_response_headers(response_data)




@bp.route('/room/<string:room_id>/delete/<int:post_id>', methods=('POST',))
@login_required  # ログインが必要なルート
@auth_required
def delete(room_id, post_id):
    post_id = int_check(post_id)
    room_id_check(room_id)
    get_post(post_id)  # 投稿を取得
    db = get_db() 
    db.execute('DELETE FROM posts WHERE id = ?', (post_id,))
    db.commit()  # 変更をコミット
    response_data =   redirect(url_for('meeting.meeting', room_id=room_id))  
    return secure_response_headers(response_data)# インデックスページにリダイレクト




@bp.route('/room/<string:room_id>/vote/<int:post_id>', methods=('POST','GET'))
@login_required  # ログインが必要なルート
@auth_required
def vote(room_id, post_id):
    post_id = int_check(post_id)
    room_id_check(room_id)
    get_post(post_id, check_author=False, check_vote=True)

    user_id = g.user['id']

    vote = get_db().execute(
        'SELECT COUNT(*) AS cnt'
        ' FROM votes'
        ' WHERE post_id = ? AND user_id = ?',
        (post_id,user_id)
    ).fetchone() 

    cnt = int(vote['cnt'])

    if cnt == 0:
        db = get_db()  # データベース接続を取得
        db.execute(
                'INSERT INTO votes (post_id, user_id, room_id)'
                ' VALUES (?, ?, ?)',
                (post_id, user_id, room_id)
            ) 
        db.commit()  # 変更をコミット
    else:
        db = get_db()  # データベース接続を取得
        db.execute(
                'DELETE FROM votes '
                'WHERE post_id = ? AND user_id = ? AND room_id  = ?', 
                (post_id, user_id, room_id)
            ) 
        db.commit()  # 変更をコミット

    id_num = "#" + str(post_id)

    response_data =   redirect(url_for('meeting.meeting', room_id=room_id) + id_num)  
    return secure_response_headers(response_data)# インデックスページにリダイレクト




@bp.route('/room/<string:room_id>/public/<int:post_id>', methods=('POST','GET'))
@login_required  # ログインが必要なルート
@auth_required
def post_public(room_id, post_id):
    post_id = int_check(post_id)
    room_id_check(room_id)
    get_post(post_id)

    user_id = g.user['id']

    post = get_db().execute(
        'SELECT public'
        ' FROM posts'
        ' WHERE id = ? AND author_id = ?',
        (post_id,user_id)
    ).fetchone() 

    cnt = int(post['public'])

    if cnt == 0:
        db = get_db()  # データベース接続を取得
        db.execute(
                'UPDATE posts SET public = 1'
                ' WHERE id = ? AND author_id = ?',
                (post_id,user_id,)
            )
        db.commit()  # 変更をコミット
    else:
        db = get_db()  # データベース接続を取得
        db.execute(
                'UPDATE posts SET  public = 0 '
                ' WHERE id = ? AND author_id = ?',
                (post_id,user_id,)
            )  
        db.commit()  # 変更をコミット
    
    id_num = "#" + str(post_id)

    response_data =   redirect(url_for('meeting.meeting', room_id=room_id) + id_num)  
    return secure_response_headers(response_data)# インデックスページにリダイレクト