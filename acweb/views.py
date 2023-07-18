from flask import abort, flash, redirect, render_template, request, url_for
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

    cloud_files = CloudFile.query.all()
    return render_template('index.html', cloud_files=cloud_files)


@app.route('/uploads', methods=['POST'])
@login_required
def uploads():
    import os
    if request.method == 'POST':
        f = request.files.get('file')
        if f is None:
            flash('No file part')
        else:
            file_name = f.filename

            # TODO: 检查文件类型（后缀）

            content_bytes = f.read()

            cloud_file = CloudFile.save_encrypt_commit(file_name, content_bytes)

            flash('Your file has been uploaded successfully.')
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


@app.route('/cloud_file/delete/<int:cloud_file_id>', methods=['POST'])
@login_required
def delete(cloud_file_id):
    if CloudFile.delete_uncommit(cloud_file_id):
        flash('Item deleted.')
    else:
        flash('Error! Item not found.')
    return redirect(url_for('index'))


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

        user = User.query.first()

        if username == user.username and user.validate_password(password):
            login_user(user)
            flash('Login success.')
            return redirect(url_for('index'))

        flash('Invalid username or password.')
        return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Goodbye.')
    return redirect(url_for('index'))
