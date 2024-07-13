import os 
from flask import Flask


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    
    app.config.from_mapping(
        SECRET_KEY='needchangeyoursecretkey',  # セッションやクッキーのセキュリティ用の秘密鍵
        # python3 -c 'import secrets; print(secrets.token_hex())' を利用して新しいキーを作成して貼り付ける
        DATABASE=os.path.join(app.instance_path, 'project.sqlite'), 
    )

    app.config.from_pyfile('config.py', silent=True)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    app.config.update(
        PERMANENT_SESSION_LIFETIME= 60 * 60,
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
    )

    from . import db
    db.init_app(app)

    from . import auth
    app.register_blueprint(auth.bp)

    from . import meeting
    app.register_blueprint(meeting.bp)
    app.add_url_rule('/', endpoint='index')

    from . import room
    app.register_blueprint(room.bp)

    return app 
