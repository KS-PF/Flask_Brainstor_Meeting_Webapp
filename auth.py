import functools 
from project.functions import (
    secure_response_headers, token_check,
    form_validation, int_check, replace_str,
)
import random
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)  
from werkzeug.security import check_password_hash, generate_password_hash  
from project.db import get_db  


bp = Blueprint('auth', __name__, url_prefix='/auth') 




def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            response_data = redirect(url_for('auth.login'))
            return secure_response_headers(response_data)

        return view(**kwargs)

    return wrapped_view




@bp.before_app_request
def load_logged_in_user():
    # リクエストの前にログインしているユーザーを読み込む関数
    id = session.get('id')  # セッションからユーザーIDを取得
    user_id = session.get('user_id')  # セッションからユーザーIDを取得

    if id is None or user_id is None:
        # ユーザーIDがセッションにない場合、g.userをNoneに設定
        g.user = None
        g.owner = None
    else:
        # ユーザーIDがセッションにある場合、データベースからユーザー情報を取得し、g.userに設定
        g.user = get_db().execute(
            'SELECT * FROM users WHERE id = ?', (id,)
        ).fetchone()




@bp.route('/register', methods=('GET', 'POST'))
def register():
    # ユーザー登録のためのビュー関数
    num = random.randint(1,6)
    sc_path = f"sc/s{num}.jpg"

    if request.method == 'POST':
        # フォームがPOSTされた場合、フォームデータを取得
        user_id = request.form.get('user_id', default=None, type=str)
        nickname = request.form.get('nickname', default=None, type=str)
        password = request.form.get('password', default=None, type=str)
        confirm = request.form.get('confirm', default=None, type=str)
        sc_text = request.form.get('sc_text', default=None, type=str)
        sc_num = request.form.get('sc_num', default=None, type=int)
        post_token = request.form.get('token', default=None, type=str)

        sc_num = int_check(sc_num)

        sc_list = ["BnmCWs","xzcUUKii","vbHyyPLa",
                "MnWeQa","QawpYss","EHzXaAv",]
        
        error = None

        error = form_validation(user_id, error, "ユーザーID", rex = True, hidden = False,
                                len_check = True, len_min = 8, len_max = 48,)
        error = form_validation(nickname, error, "ユーザー名", rex = False, hidden = False,
                                len_check = True, len_min = 3, len_max = 24,)
        error = form_validation(password, error, "パスワード", rex = True, hidden = False,
                                len_check = True, len_min = 8, len_max = 48,)
        error = form_validation(confirm, error, "確認用パスワード", rex = True, hidden = False,
                                len_check = True, len_min = 8, len_max = 48,)
        error = form_validation(sc_num, error, "", rex = False, hidden = True,
                                len_check = False, len_min = 0, len_max = 0,)
        error = form_validation(post_token, error, "", rex = False, hidden = True,
                                len_check = False, len_min = 0, len_max = 0,)
        
        nickname = replace_str(nickname)

        if error is None and password == user_id:
            error = 'ERROR:「パスワード」と「ユーザーID」を同じにすることはできません'

        elif error is None and (1 > sc_num or sc_num > 6):
            error = 'ERROR(s)'

        elif  error is None and password != confirm:
            error = 'ERROR:「パスワード」と「確認用パスワード」が一致していません'

        elif  error is None and sc_text != sc_list[sc_num - 1]:
            error = 'ERROR:「画像のテクスト」が間違っています'

        elif  error is None and token_check('check', post_token) == False:
            error = 'もう一度入力してください'

        if error is None:
            db = get_db()  # データベース接続を取得
            try:
                # 新しいユーザーをデータベースに挿入
                db.execute(
                    "INSERT INTO users (user_id, nickname, password) VALUES (?, ?, ?)",
                    (user_id, nickname, generate_password_hash(password)),  # パスワードをハッシュ化して保存
                )
                db.commit()  # 変更をコミット
            except db.IntegrityError:
                # ユーザー名が既に登録されている場合のエラー処理
                error = f"ERROR: ユーザーID、 {user_id} は既に使用されています"
            else:
                # 成功した場合、ログインページにリダイレクト
                response_data = redirect(url_for("auth.login"))
                return secure_response_headers(response_data)

        # エラーがある場合、フラッシュメッセージを表示
        flash(error)

    # GETリクエストの場合、登録ページを表示
    token = token_check('set')
    response_data = render_template('auth/register.html', sc_path = sc_path, num = num, token = token)
    return secure_response_headers(response_data)




@bp.route('/login', methods=('GET', 'POST'))
def login():
    # ログインのためのビュー関数
    if request.method == 'POST':
        # フォームがPOSTされた場合、フォームデータを取得
        user_id = request.form.get('user_id', default=None, type=str)
        password = request.form.get('password', default=None, type=str)
        post_token = request.form.get('token', default=None, type=str)

        error = None

        # フォームの検証
        error = form_validation(user_id, error, "ユーザーID", rex = True, hidden = False,
                                len_check = True, len_min = 8, len_max = 48,)
        error = form_validation(password, error, "パスワード", rex = True, hidden = False,
                                len_check = True, len_min = 8, len_max = 48,)
        error = form_validation(post_token, error, "", rex = False, hidden = True,
                                len_check = False, len_min = 0, len_max = 0,)
        

        if error is None and token_check('check', post_token) == False:
            error = 'もう一度入力してください'

        if error is None:
            db = get_db()  # データベース接続を取得

            # データベースからユーザーを取得
            user = db.execute(
                'SELECT * FROM users WHERE user_id = ?', (user_id,)
            ).fetchone()

            if not user:
                error = 'ERROR:ユーザーID、もしくはパスワードが間違っています'
            elif not check_password_hash(user['password'], password):
                error = 'ERROR:ユーザーID、もしくはパスワードが間違っています'

        if error is None:
            # エラーがない場合、セッションをクリアして新しいユーザーIDを設定
            session.clear()
            session['id'] = user['id']
            session['user_id'] = user['user_id']
            response_data = redirect(url_for('index'))  
            return secure_response_headers(response_data)# インデックスページにリダイレクト

        flash(error)  # エラーメッセージを表示

    token = token_check('set')
    response_data = render_template('auth/login.html', token = token)  # GETリクエストの場合、ログインページを表示
    return secure_response_headers(response_data)




@bp.route('/logout')
def logout():
    # ログアウトのためのビュー関数
    session.clear()  # セッションをクリアしてユーザーのログイン情報を削除
    response_data = redirect(url_for('index'))  
    return secure_response_headers(response_data)# インデックスページにリダイレクト




@bp.route('/user', methods=('GET', 'POST'))
@login_required  # ログインが必要なルート
def user():
    response_data = render_template('auth/user.html')
    return secure_response_headers(response_data)




@bp.route('/nickname', methods=('GET', 'POST'))
@login_required  # ログインが必要なルート
def nickname():
    if request.method == 'POST':
        # フォームがPOSTされた場合、フォームデータを取得
        nickname = request.form.get('nickname', default=None, type=str)
        post_token = request.form.get('token', default=None, type=str)

        error = None

        error = form_validation(nickname, error, "ユーザー名", rex = False, hidden = False,
                                len_check = True, len_min = 3, len_max = 24,)
        error = form_validation(post_token, error, "", rex = False, hidden = True,
                                len_check = False, len_min = 0, len_max = 0,)

        if  error is None and g.user['nickname'] == nickname:
            error = 'ERROR: 新しい「ユーザー名」を入力してください'
        elif  error is None and token_check('check', post_token) == False:
            error = 'もう一度入力してください'

        nickname = replace_str(nickname)

        if error is None:
            id = session.get('id')
            db = get_db()  # データベース接続を取得
            db.execute(
                'UPDATE users SET nickname = ?'
                ' WHERE id = ?',
                (nickname, id)
            )  # 投稿を更新
            db.commit()  # 変更をコミット  
            response_data = redirect(url_for('auth.user'))
            return secure_response_headers(response_data)
        else:
            flash(error)  # エラーメッセージを表示

    name = g.user['nickname']
    token = token_check('set')
    response_data = render_template('auth/user/nickname.html', token = token, name = name)
    return secure_response_headers(response_data)




@bp.route('/password', methods=('GET', 'POST'))
@login_required  # ログインが必要なルート
def password():
    if request.method == 'POST':
        # フォームがPOSTされた場合、フォームデータを取得
        password = request.form.get('password', default=None, type=str)
        new_password = request.form.get('new_password', default=None, type=str)
        confirm = request.form.get('confirm', default=None, type=str)
        post_token = request.form.get('token', default=None, type=str)

        error = None

        error = form_validation(password, error, "パスワード", rex = True, hidden = False,
                                len_check = True, len_min = 8, len_max = 48,)
        error = form_validation(new_password, error, "新しいパスワード", rex = True, hidden = False,
                                len_check = True, len_min = 8, len_max = 48,)
        error = form_validation(confirm, error, "確認用パスワード", rex = True, hidden = False,
                                len_check = True, len_min = 8, len_max = 48,)
        error = form_validation(post_token, error, "", rex = False, hidden = True,
                                len_check = False, len_min = 0, len_max = 0,)

        if  error is None and new_password == g.user['user_id']:
            error = 'ERROR:「パスワード」と「ユーザーID」を同じにすることはできません'

        elif  error is None and token_check('check', post_token) == False:
            error = 'もう一度入力してください'

        elif  error is None and password == new_password:
            error = 'ERROR: 新しいパスワードを入力してください'

        elif  error is None and not check_password_hash(g.user['password'], password):
            error = 'ERROR:「現在のパスワード」が間違っています'

        elif  error is None and new_password != confirm:
            error = 'ERROR:「新しいパスワード」と「確認用の新しいパスワード」が一致していません'

        if error is None:
            id = session.get('id')
            db = get_db()  # データベース接続を取得
            db.execute(
                'UPDATE users SET password = ?'
                ' WHERE id = ?',
                (generate_password_hash(new_password), id)
            )  # 投稿を更新
            db.commit()  # 変更をコミット  
            response_data = redirect(url_for('auth.user'))
            return secure_response_headers(response_data)
        else:
            flash(error)  # エラーメッセージを表示

    token = token_check('set')
    response_data = render_template('auth/user/password.html', token = token)
    return secure_response_headers(response_data)




@bp.route('/delete', methods=('GET', 'POST'))
@login_required  # ログインが必要なルート
def delete():
    if request.method == 'POST':
        user_id = request.form.get('user_id', default=None, type=str)
        password = request.form.get('password', default=None, type=str)
        post_token = request.form.get('token', default=None, type=str)

        error = None

        # フォームの検証
        error = form_validation(user_id, error, "ユーザーID", rex = True, hidden = False,
                                len_check = True, len_min = 8, len_max = 48,)
        error = form_validation(password, error, "パスワード", rex = True, hidden = False,
                                len_check = True, len_min = 8, len_max = 48,)
        error = form_validation(post_token, error, "", rex = False, hidden = True,
                                len_check = False, len_min = 0, len_max = 0,)

        if  error is None and token_check('check', post_token) == False:
            error = 'もう一度入力してください'

        elif  error is None and g.user['user_id'] != user_id:
            error = 'ERROR:「ユーザーID」が間違っています'
        elif  error is None and not check_password_hash(g.user['password'], password):
            error = 'ERROR:「パスワード」が間違っています'

        if error is None:
            id = session.get('id')
            db = get_db()  # データベース接続を取得
            db.execute('DELETE FROM users WHERE id = ?', (id,))  # 投稿を削除
            db.commit()  # 変更をコミット

            session.clear()  # セッションをクリアしてユーザーのログイン情報を削除
            response_data = redirect(url_for('index'))  
            return secure_response_headers(response_data)# インデックスページにリダイレクト
        else:
            flash(error)  # エラーメッセージを表示

    token = token_check('set')
    response_data = render_template('auth/user/delete.html', token = token)
    return secure_response_headers(response_data)