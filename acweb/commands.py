import os
import shutil

import click

from acweb import app, db
from acweb.models import CloudFile, User


@app.cli.command()
@click.option('--drop', is_flag=True, help='Create after drop.')
def initdb(drop):
    """Initialize the database."""
    if drop:
        db.drop_all()
    db.create_all()
    click.echo('Initialized database.')


@app.cli.command()
def forge():
    """生成虚拟测试数据 & 创建用户 CUCer"""

    # 如果数据库中已经有数据，先删除
    db.drop_all()
    db.create_all()

    # 删除 uploads 文件夹中的所有文件
    for file_name in os.listdir(app.config['UPLOAD_FOLDER']):
        upload_file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_name)
        if os.path.isfile(upload_file_path):
            os.remove(upload_file_path)

    # 新建默认用户
    username = 'CUCer'
    user = User(username=username)
    user.set_password('123456')
    db.session.add(user)
    db.session.commit()

    # 将测试文件复制到 uploads 文件夹中
    example_file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'example_files')
    for root, dirs, files in os.walk(example_file_path):
        for file_name in files:
            file_path = os.path.join(root,file_name)
            with open(file_path, 'rb') as f:
                file_content = f.read()
                cloud_file = CloudFile.save_encrypt_commit(file_name, file_content)

    click.echo('Done.')


@app.cli.command()
@click.option('--username', prompt=True, help='The username used to login.')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='The password used to login.')
def create_user(username, password):
    """Create user."""
    db.create_all()

    user = User.query.first()
    if user is not None:
        click.echo('Updating user...')
        user.username = username
        user.set_password(password)
    else:
        click.echo('Creating user...')
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)

    db.session.commit()
    click.echo('Done.')
