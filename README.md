# Flask_brainstor_meeting_Webapp

Flaskを用いたWebアプリの開発を行いました。以下のファイル構成、システム構成図、コマンド、実行画像などを示したいと思います。

### ファイル構成
```
brainstor_meeting
├── project/
│   ├── static/
│   │   ├── img/
│   │   │   ├── icon.png
│   │   │   ├── logout.png
│   │   │   └── user.png
│   │   ├── sc/
│   │   ├── main.js
│   │   └── style.css
│   ├── templates/
│   │   ├── auth/
│   │   │   ├── login.html
│   │   │   ├── register.html
│   │   │   └── auth.html
│   │   ├── user/
│   │   │   ├── delete.html
│   │   │   ├── nickname.html
│   │   │   ├── password.html
│   │   │   ├── login.html
│   │   │   ├── register.html
│   │   │   └── user.html
│   │   ├── meeting/
│   │   │   ├── brainstorm/
│   │   │   │   ├── meeting.html
│   │   │   │   └── post.html
│   │   │   ├── update.html
│   │   │   ├── auth.html
│   │   │   └── index.html
│   │   ├── room/
│   │   │   ├── create.html
│   │   │   ├── delete.html
│   │   │   └── update.html
│   │   └── base.html
│   ├── __init__.py
│   ├── auth.py
│   ├── db.py
│   ├── functions.py
│   ├── meeting.py
│   ├── room.py
│   └── schema.sql
└── .venv/
    ├── ...
    └── ...
```

### コマンド
projectフォルダを作成し、そこで仮想環境を作り実行してください。
```
brainstor_meeting　$ python3 -m venv .venv
brainstor_meeting　$ source .venv/bin/activate
brainstor_meeting　$ pip install Flask
brainstor_meeting　$ flask --app project run --debug
```
また、キーを生成して、SECRET_KEYに貼り付けてください。
```
$ python3 -c 'import secrets; print(secrets.token_hex())'
```

### 構成


### 画像


### 注意事項
scの画像はアップロードしていません。