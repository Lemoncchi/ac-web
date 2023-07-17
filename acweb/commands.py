import click

from acweb import app, db
from acweb.models import User, CloudFile


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
    db.drop_all()
    db.create_all()

    username = 'CUCer'
    cloud_files = [
        {'file_name': 'My Neighbor Totoro', 'year': '1988'},
        {'file_name': 'Dead Poets Society', 'year': '1989'},
        {'file_name': 'A Perfect World', 'year': '1993'},
        {'file_name': 'Leon', 'year': '1994'},
        {'file_name': 'Mahjong', 'year': '1996'},
        {'file_name': 'Swallowtail Butterfly', 'year': '1996'},
        {'file_name': 'King of Comedy', 'year': '1999'},
        {'file_name': 'Devils on the Doorstep', 'year': '1999'},
        {'file_name': 'WALL-E', 'year': '2008'},
        {'file_name': 'The Pork of Music', 'year': '2012'},
    ]

    user = User(username=username)
    user.set_password('123456')
    db.session.add(user)
    for m in cloud_files:
        cloud_file = CloudFile(file_name=m['file_name'], year=m['year'])
        db.session.add(cloud_file)

    db.session.commit()
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
