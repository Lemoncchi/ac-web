import os
from io import BytesIO

from flask import (abort, flash, redirect, render_template, request, send_file,
                   url_for)
from flask_login import current_user, login_required, login_user, logout_user

from acweb import app, db
from acweb.models import CloudFile, SharedFileInfo, User


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

        if user is None:  
            # 均返回 'Invalid username or password.' 避免暴力搜索该用户名是否存在
            flash('Invalid username or password.')
            return redirect(url_for('login'))

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
    
    # 身份验证
    if current_user.id != cloud_file.user_id:
        flash('Forbidden.')
        abort(403)

    from datetime import datetime
    from sqlalchemy import and_, or_, not_

    current_file_shared_file_info_list = SharedFileInfo.query.filter(
        and_(
            SharedFileInfo.cloud_file_id == cloud_file_id,
            SharedFileInfo.expiry_time < datetime.utcnow(),
        )
    )

    if request.method == 'GET':
        if current_file_shared_file_info_list:
            flash(f'File {cloud_file.file_name} already shared.\n')
            flash('You will crate a seperate new share settings.')
            # return redirect(url_for('index'))  # 不允许重复分享
            # flash('You will update the share settings.')
        return render_template('share.html', cloud_file=cloud_file)

    elif request.method == 'POST':
        # print(request.form)
        # print(request.form['share_type'])

        expired_in = request.form['expired_in']
        customed_expired_in = request.form['customed_expired_in']
        allowed_download_times = request.form['allowed_download_times']
        customed_allowed_download_times = request.form['customed_allowed_download_times']

        if expired_in and customed_expired_in:
            flash('In "Expiration Date", You both select the option and input the "Customed Input!"\nInvalid!')
            return redirect(url_for('share', cloud_file_id=cloud_file_id))
        if allowed_download_times and customed_allowed_download_times:
            flash('In "Maximum download times", You both select the option and input the "Customed Input!"\nInvalid!')
            return redirect(url_for('share', cloud_file_id=cloud_file_id))

        expired_in_int = int(expired_in or customed_expired_in)

        allowed_download_times_int = int(
            allowed_download_times
            or customed_allowed_download_times
        )

        from datetime import datetime, timedelta
        expiry_time = datetime.utcnow() + timedelta(days=expired_in_int)

        shared_file_info = SharedFileInfo(cloud_file_id=cloud_file_id, owner_id=cloud_file.user_id, expiry_time=expiry_time, allowed_download_count=allowed_download_times_int)

        db.session.add(shared_file_info)

        db.session.commit()
        flash('Item shared.')
        # print(shared_file_info)
        return redirect(url_for('index'))
        
    return render_template('share.html', cloud_file=cloud_file)


@app.route('/share/download/<int:shared_file_info_id>', methods=['GET', 'POST'])
def shared_file_download(shared_file_info_id: int):
    shared_file_info = db.session.get(SharedFileInfo, shared_file_info_id)
    share_page_access_token = request.args.get('share_page_access_token')

    if shared_file_info is None:
        abort(404)
    if share_page_access_token is None:
        flash('None share code access token.')
        abort(403)  # 可根据 `安全性要求` 不提供此信息，并返回 404

    if not shared_file_info.validate_share_page_access_token(share_page_access_token=share_page_access_token):  # 验证分享码失败
        flash('Invalid share code.')  # 可根据 `安全性要求` 不提供此信息，并返回 404
        abort(403)


    cloud_file = db.session.get(CloudFile, shared_file_info.cloud_file_id)

    return render_template('shared_file_download.html', cloud_file=cloud_file, shared_file_info=shared_file_info)