import os
from datetime import datetime
from acweb import app
import werkzeug.datastructures
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from acweb import db


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20))
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def validate_password(self, password):
        return check_password_hash(self.password_hash, password)


class CloudFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)  # 默认设置为当前时间
    file_name = db.Column(db.String(60))
    file_save_name = db.Column(db.String(60))
    file_hash = db.Column(db.String(128))
    file_size = db.Column(db.Integer)
    is_shared = db.Column(db.Boolean, default=False)
    # year = db.Column(db.String(4))

    def __repr__(self):
        return f'<CloudFile {self.file_name}, {self.file_save_name}, {self.cloud_file.file_hash}, {self.cloud_file.file_size}>'


    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp,
            'file_name': self.file_name,
            'file_save_name': self.file_save_name,
            'file_hash': self.file_hash,
            'file_size': self.file_size,
            'is_shared': self.is_shared
        }
    
    @classmethod
    def save_encrypt_commit(cls, file_name_, content_bytes_:bytes, is_shared_=False):
        """保存文件元数据到数据库 & 保存加密后的文件到本地
        """
        file_save_name = file_name_  # TODO: 后面需要对文件名进行处理

        file_size_ = len(content_bytes_)

        file_hash_ = None  # TODO: 需要对文件进行安全 hash

        encrypted_content_bytes = content_bytes_  # TODO: 需要对文件进行加密

        save_path = os.path.join(app.config['UPLOAD_FOLDER'], file_save_name)

        cloud_file = CloudFile(file_name=file_name_, file_save_name=file_save_name, file_hash=file_hash_, file_size=file_size_, is_shared=is_shared_)
        db.session.add(cloud_file)
        db.session.commit()

        with open(save_path, 'wb') as f:  # 保存 文件 & 加密后的文件
            f.write(encrypted_content_bytes)

        return cloud_file
