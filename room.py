from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for,
)
from project.functions import (
    secure_response_headers, token_check, form_validation, 
)
from project.auth import login_required
from project.db import get_db 
from werkzeug.security import check_password_hash, generate_password_hash 

bp = Blueprint('room', __name__, url_prefix='/room')  




def get_room_owner(user_id):
    room_num = get_db().execute(
            'SELECT COUNT(*) as room_num FROM rooms WHERE create_user_id = ?', (user_id,)
        ).fetchone()

    if int(room_num['room_num']) > 0:
        g.owner = get_db().execute(
        'SELECT * FROM rooms WHERE create_user_id = ?', (user_id,)
        ).fetchone()
    else:
        g.owner = None




@bp.route('/create', methods=('GET', 'POST'))
@login_required 
def create():
    
    room_limit = 9
    room_num = get_db().execute(
        'SELECT COUNT(*) AS cnt'
        ' FROM rooms'
    ).fetchone() 
    if int(room_num['cnt']) > room_limit:
        message = '現在アクセスが集中しているため、新規Room作成はできません。２時間ほど時間を置いて再度アクセスしてください。'
        flash(message)
    
    
    if request.method == 'POST':
        # フォームがPOSTされた場合、フォームデータを取得
        room_id = request.form.get('room_id', default=None, type=str)
        password = request.form.get('password', default=None, type=str)
        confirm = request.form.get('confirm', default=None, type=str)
        post_token = request.form.get('token', default=None, type=str)

        get_room_owner(g.user['id'])
        error = None

        error = form_validation(room_id, error, "ルームID", rex = True, hidden = False,
                                len_check = True, len_min = 8, len_max = 48,)
        error = form_validation(password, error, "パスワード", rex = True, hidden = False,
                                len_check = True, len_min = 8, len_max = 48,)
        error = form_validation(confirm, error, "確認用パスワード", rex = True, hidden = False,
                                len_check = True, len_min = 8, len_max = 48,)
        error = form_validation(post_token, error, "", rex = False, hidden = True,
                                len_check = False, len_min = 0, len_max = 0,)

        if error is None and int(room_num['cnt']) > room_limit:
            error = '現在アクセスが集中しているため、新規Room作成はできません。２時間ほど時間を置いて再度アクセスしてください。'
        elif  error is None and password == room_id:
            error = 'ERROR:「パスワード」と「ルームID」を同じにすることはできません'

        elif  error is None and password != confirm:
            error = 'ERROR:「パスワード」と「確認用パスワード」が一致していません'

        elif  error is None and g.owner is not None:
            error = 'ERROR: 同じアカウントでMeeting Roomを、同時に複数作成することはできません'
            
        elif  error is None and token_check('check', post_token) == False:
            error = 'もう一度入力してください'

        if error is None:
            db = get_db()  # データベース接続を取得

            user_id = g.user["id"]

            try:
                db.execute(
                    "INSERT INTO rooms (create_user_id, room_name, password) VALUES (?, ?, ?)",
                    ( user_id, room_id, generate_password_hash(password)), 
                )
                db.commit() 
            except db.IntegrityError:
                error = f"ERROR: ルームID、 {room_id} は既に使用されています"
            else:
                response_data = redirect(url_for("meeting.auth"))
                return secure_response_headers(response_data)

        # エラーがある場合、フラッシュメッセージを表示
        flash(error)

    token = token_check('set')
    response_data =  render_template('room/create.html', token = token)
    return secure_response_headers(response_data)




@bp.route('/update', methods=('GET', 'POST'))
@login_required 
def update():
    get_room_owner(g.user['id'])
    if g.owner is None:
        response_data = redirect(url_for('index'))
        return secure_response_headers(response_data)
    else:
        if request.method == 'POST':
        # フォームがPOSTされた場合、フォームデータを取得
            password = request.form.get('password', default=None, type=str)
            new_password = request.form.get('new_password', default=None, type=str)
            confirm = request.form.get('confirm', default=None, type=str)
            post_token = request.form.get('token', default=None, type=str)

            error = None

            # フォームの検証
            error = form_validation(password, error, "パスワード", rex = True, hidden = False,
                                len_check = True, len_min = 8, len_max = 48,)
            error = form_validation(new_password, error, "新しいパスワード", rex = True, hidden = False,
                                len_check = True, len_min = 8, len_max = 48,)
            error = form_validation(confirm, error, "確認用パスワード", rex = True, hidden = False,
                                len_check = True, len_min = 8, len_max = 48,)
            error = form_validation(post_token, error, "", rex = False, hidden = True,
                                len_check = False, len_min = 0, len_max = 0,)
            
            if  error is None and password == g.owner["room_name"]:
                error = 'ERROR:「パスワード」と「ルームID」を同じにすることはできません'

            elif  error is None and password == new_password:
                error = 'ERROR: 新しいパスワードを入力してください'

            elif  error is None and not check_password_hash(g.owner['password'], password):
                error = 'ERROR:「現在のパスワード」が間違っています'

            elif  error is None and new_password != confirm:
                error = 'ERROR:「新しいパスワード」と「確認用の新しいパスワード」が一致していません'

            elif  error is None and token_check('check', post_token) == False:
                error = 'もう一度入力してください'

            if error is None:
                id = g.owner["id"]
                db = get_db()
                db.execute(
                'UPDATE rooms SET password = ?'
                ' WHERE id = ?',
                (generate_password_hash(new_password), id)
                )  
                db.commit()    
                response_data = redirect(url_for('index'))
                return secure_response_headers(response_data)
            else:
                flash(error)  

        token = token_check('set')
        response_data =  render_template('room/update.html', token = token)
        return secure_response_headers(response_data)




@bp.route('/delete', methods=('GET', 'POST'))
@login_required  
def delete():
    get_room_owner(g.user['id'])
    if g.owner is None:
        response_data = redirect(url_for('index'))
        return secure_response_headers(response_data)
    else:
        if request.method == 'POST':
            room_id = request.form.get('room_id', default=None, type=str)
            password = request.form.get('password', default=None, type=str)
            post_token = request.form.get('token', default=None, type=str)

            error = None

            error = form_validation(room_id, error, "ルームID", rex = True, hidden = False,
                                len_check = True, len_min = 8, len_max = 48,)
            error = form_validation(password, error, "パスワード", rex = True, hidden = False,
                                len_check = True, len_min = 8, len_max = 48,)
            error = form_validation(post_token, error, "", rex = False, hidden = True,
                                len_check = False, len_min = 0, len_max = 0,)

            if  error is None and g.owner['room_name'] != room_id:
                error = 'ERROR: 「ルームID」もしくは「パスワード」が間違っています'
            elif  error is None and not check_password_hash(g.owner['password'], password):
                error = 'ERROR:「パスワード」が間違っています'
            elif  error is None and token_check('check', post_token) == False:
                error = 'もう一度入力してください'

            if error is None:
                id = g.owner['id']
                db = get_db() 
                db.execute('DELETE FROM rooms WHERE id = ?', (id,))  
                db.commit()  
                delete_chats(id)

                g.owner = None
                response_data = redirect(url_for('index'))  
                return secure_response_headers(response_data)
            else:
                flash(error) 

        token = token_check('set')
        response_data =  render_template('room/delete.html', token = token)
        return secure_response_headers(response_data)




def delete_chats(room_id):
    db = get_db()
    db.execute('DELETE FROM posts WHERE room_id = ?', (room_id,)) 
    db.commit()  

    db = get_db()  
    db.execute('DELETE FROM votes WHERE room_id = ?', (room_id,))  
    db.commit() 




def time_limit_delete(room_id):
    db = get_db()  
    db.execute('DELETE FROM posts WHERE room_id = ?', (room_id,)) 
    db.commit()  