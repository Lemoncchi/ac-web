import os
from io import BytesIO

from flask import (abort, flash, redirect, render_template, request, send_file,
                   url_for)
from flask_login import current_user, login_required, login_user, logout_user

from acweb import app, db
from acweb.models import CloudFile, User


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if not current_user.is_authenticated:
            return redirect(url_for('index'))

        file_name = request.form['file_name']
        year = request.form['year']

        if not file_name or not year or len(year) != 4 or len(file_name) > 60:
            flash('Invalid input.')
            return redirect(url_for('index'))

        cloud_file = CloudFile(file_name=file_name, year=year)
        db.session.add(cloud_file)
        db.session.commit()
        flash('Item created.')
        return redirect(url_for('index'))

    if current_user.is_authenticated:
        ueser_cloud_files = CloudFile.query.filter_by(user_id=current_user.id).order_by(CloudFile.timestamp.desc()).all()
        return render_template('index.html', user_cloud_files=ueser_cloud_files)
    else:
        return render_template('index.html')


@app.route('/uploads', methods=['POST'])
@login_required
def uploads():
    import os
    if request.method == 'POST':
        f = request.files.get('file')
        if f is None:
            flash('No file part')
            return redirect(url_for('index'))
        else:
            file_name = f.filename

            # TODO: 检查文件类型（后缀）

            content_bytes = f.read()

            cloud_file = CloudFile.save_encrypt_commit(current_user.id,file_name, content_bytes)

            flash('Your file has been uploaded successfully.')
            return redirect(url_for('index'))

    return redirect(url_for('index'))

@app.route('/cloud_file/edit/<int:cloud_file_id>', methods=['GET', 'POST'])
@login_required
def edit(cloud_file_id):
    # cloud_file = CloudFile.query.get_or_404(cloud_file_id)
    cloud_file = db.session.get(CloudFile, cloud_file_id)
    if cloud_file is None:
        abort(404)

    if request.method == 'POST':
        file_name = request.form['file_name']
        year = request.form['year']

        if not file_name or not year or len(year) != 4 or len(file_name) > 60:
            flash('Invalid input.')
            return redirect(url_for('edit', cloud_file_id=cloud_file_id))

        cloud_file.file_name = file_name
        cloud_file.year = year
        db.session.commit()
        flash('Item updated.')
        return redirect(url_for('index'))

    return render_template('edit.html', cloud_file=cloud_file)


@app.route('/cloud_file/delete/<int:cloud_file_id>', methods=['GET', 'POST'])
@login_required
def delete(cloud_file_id):
    if CloudFile.delete_uncommit(cloud_file_id):
        flash('Item deleted.')
    else:
        flash('Error! Item not found.')
    return redirect(url_for('index'))


@app.route("/cloud_file/downloads/content/<int:cloud_file_id>", methods=["GET", "POST"])
def download_content(cloud_file_id: int):
    """下载文件内容"""
    cloud_file = db.session.get(CloudFile, cloud_file_id)
    if cloud_file is None:
        abort(404)

    if cloud_file.is_shared:
        # TODO: 检查是否过期
        if cloud_file.is_expired:
            flash('Expired! Forbidden.')
            abort(403)  # Forbidden

    else: # 私人非共享文件
        if current_user.is_authenticated:
            if current_user.id != cloud_file.user_id:
                flash('Forbidden.')
                abort(403)  # Forbidden
        else:
            redirect(url_for('login'))

    cloud_file.decrypt()

    return send_file(
        path_or_file=BytesIO(cloud_file.decrypted_content_bytes),
        download_name=cloud_file.file_name,
        as_attachment=True,
    )

@app.route("/cloud_file/downloads/hash/<int:cloud_file_id>", methods=["GET", "POST"])
def download_hash(cloud_file_id: int):
    """下载文件 hash"""
    cloud_file = db.session.get(CloudFile, cloud_file_id)
    if cloud_file is None:
        abort(404)
    
    if cloud_file.is_shared:
        # TODO: 检查是否过期
        if cloud_file.is_expired:
            flash('Expired! Forbidden.')
            abort(403)  # Forbidden

    else: # 私人非共享文件
        if current_user.is_authenticated:
            if current_user.id != cloud_file.user_id:
                flash('Forbidden.')
                abort(403)  # Forbidden
        else:
            redirect(url_for('login'))

    return send_file(
        path_or_file=BytesIO(bytes(cloud_file.file_hash, 'ascii')),
        download_name=cloud_file.file_name,
        as_attachment=True,
    )


@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        username = request.form['username']

        if not username or len(username) > 20:
            flash('Invalid input.')
            return redirect(url_for('settings'))

        user = User.query.first()
        user.username = username
        db.session.commit()
        flash('Settings updated.')
        return redirect(url_for('index'))

    return render_template('settings.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            flash('Invalid input.')
            return redirect(url_for('login'))

        user = User.query.filter_by(username=username).first()

        if username == user.username and user.validate_password(password):
            login_user(user)
            flash('Login success.')
            return redirect(url_for('index'))

        flash('Invalid username or password.')
        return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':

        username = request.form['username']
        password = request.form['psw']
        password_repeated = request.form['psw-repeat']

        if not username or not password:
            flash('Invalid input.')
            return redirect(url_for('register'))
        
        if password != password_repeated:
            flash('Password not match.')
            return redirect(url_for('register'))

        if User.query.filter_by(username=username).first():
            flash('Username already exists.')
            return redirect(url_for('register'))

        if len(username) > app.config['MAX_USERNAME_LENGTH']:
            flash('Username too long.')
            return redirect(url_for('register'))
        if len(password) > app.config['MAX_PASSWORD_LENGTH']:
            flash('Password too long.')
            return redirect(url_for('register'))

        # TODO: 密码强度校验

        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('Registration success.')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Goodbye.')
    return redirect(url_for('index'))


@app.route('/share/<int:cloud_file_id>', methods=['GET', 'POST'])
@login_required
def share(cloud_file_id):
    cloud_file = db.session.get(CloudFile, cloud_file_id)
    if cloud_file is None:
        abort(404)

    if current_user.id != cloud_file.user_id:
        flash('Forbidden.')
        abort(403)

    if request.method == 'POST':
        cloud_file.is_shared = True
        db.session.commit()
        flash('Item shared.')
        return redirect(url_for('index'))

    return render_template('share.html', cloud_file=cloud_file)