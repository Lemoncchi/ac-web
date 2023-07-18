import os
import sys

from flask import Flask, abort
from flask_dropzone import Dropzone
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy


# SQLite URI compatible
WIN = sys.platform.startswith('win')
if WIN:
    prefix = 'sqlite:///'
else:
    prefix = 'sqlite:////'


app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev')

default_sqlite_database_URL = prefix + os.path.join(os.path.dirname(app.root_path), os.getenv('DATABASE_FILE', 'data.db'))

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', default_sqlite_database_URL)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', os.path.join(app.root_path,'uploads'))
app.config["ALLOWED_FILE_EXTENSIONS"] = os.getenv(
    "ALLOWED_FILE_EXTENSIONS",
    [
        "jpg",
        "jpeg",
        "png",
        "bmp",
        "gif",
        "doc",
        "docx",
        "xls",
        "xlsx",
        "ppt",
        "pptx",
        "pdf",
    ],
)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
dropzone = Dropzone(app)

@login_manager.user_loader
def load_user(user_id):
    from acweb.models import User
    # user = User.query.get(int(user_id))
    user = db.session.get(User, int(user_id))
    if user is None:
        abort(404)
    return user


login_manager.login_view = 'login'
# login_manager.login_message = 'Your custom message'


@app.context_processor
def inject_user():
    from acweb.models import User
    user = User.query.first()
    return dict(user=user)


from acweb import commands, errors, views
