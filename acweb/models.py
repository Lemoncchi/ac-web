import os
from datetime import datetime
from acweb import app
import werkzeug.datastructures
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from acweb import db


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, index=True)
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256:600000', salt_length=16)  # 禁止使用明文存储用户口令
        # pbkdf2:sha256:600000 ——> 600000 次 sha256 迭代
        # 其中 hash 中也包含了一个 salt，所以可以正确验证密码
        # Why is the output of werkzeugs `generate_password_hash` not constant?
        # https://stackoverflow.com/questions/23432478/why-is-the-output-of-werkzeugs-generate-password-hash-not-constant
        # 摘要：Because the salt is randomly generated each time you call the function, the resulting password hash is also different. The returned hash includes the generated salt so that can still correctly verify the password.


    def validate_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f"<User id: {self.id}, username: {self.username}, password_hash: {self.password_hash}>"


class CloudFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # 外键
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)  # 默认设置为当前 UTC 时间
    file_name = db.Column(db.String(60))
    file_save_name = db.Column(db.String(60))
    file_hash = db.Column(db.String(128))
    file_size = db.Column(db.Integer)


    def __repr__(self):
        return f'<CloudFile id: {self.id}, user_id: {self.user_id}, timestamp: {self.timestamp}, file_name: {self.file_name}, file_save_name: {self.file_save_name}, file_hash: {self.file_hash}, file_size: {self.file_size}>'


    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp,
            'file_name': self.file_name,
            'file_save_name': self.file_save_name,
            'file_hash': self.file_hash,
            'file_size': self.file_size,
        }
    
    @staticmethod
    def save_encrypt_commit(user_id, file_name_, content_bytes_:bytes):
        """保存文件元数据到数据库 & 保存加密后的文件到本地
        """
        file_save_name = file_name_  # TODO: 后面需要对文件名进行处理

        file_size_ = len(content_bytes_)

        file_hash_ = None  # TODO: 需要对文件进行安全 hash

        encrypted_content_bytes = content_bytes_  # TODO: 需要对文件进行加密

        save_path = os.path.join(app.config['UPLOAD_FOLDER'], file_save_name)

        cloud_file = CloudFile(user_id=user_id, file_name=file_name_, file_save_name=file_save_name, file_hash=file_hash_, file_size=file_size_)
        db.session.add(cloud_file)
        db.session.commit()

        with open(save_path, 'wb') as f:  # 保存 文件 & 加密后的文件
            f.write(encrypted_content_bytes)

        return cloud_file
    

    @staticmethod
    def delete_uncommit(cloud_file_id_:int):
        """删除数据库中的文件元数据 & 删除本地的加密后的文件
        """
        cloud_file = db.session.get(CloudFile, cloud_file_id_)
        if cloud_file is None:
            return False
        
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], cloud_file.file_save_name)
        if os.path.exists(save_path):
            os.remove(save_path)
        
        db.session.delete(cloud_file)
        db.session.commit()

        return True


    def decrypt(self) -> bytes:
        """对文件内容进行解密"""
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], self.file_save_name)

        with open(file_path, "rb") as f:
            encrypted_content_bytes = f.read()

        # TODO: 对文件进行解密
        self.decrypted_content_bytes = encrypted_content_bytes

        return self.decrypted_content_bytes


    def get_size_str(self) -> str:
        import math
        if self.file_size == 0:
            return "0B"
        size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
        i = int(math.floor(math.log(self.file_size, 1024)))
        p = math.pow(1024, i)
        s = round(self.file_size / p, 2)
        return f"{s} {size_name[i]}"


    def get_beijing_time(self) -> str:
        from datetime import datetime
        return datetime.fromtimestamp(self.timestamp.timestamp() + 8 * 60 * 60).strftime("%Y-%m-%d %H:%M:%S")

class SharedFileInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cloud_file_id = db.Column(db.Integer, db.ForeignKey('cloud_file.id'))  # 外键
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # 外键
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)  # 设置为分享的 UTC 时间，默认设置为当前 UTC 时间
    share_code_hash = db.Column(db.String(128))

    expiry_time = db.Column(db.DateTime)  # UTC 过期时间，None 表示永不过期

    allowed_download_count = db.Column(db.Integer, default=0)  # 允许下载次数，0 表示无限制
    used_download_count = db.Column(db.Integer, default=0)  # 已经下载次数

    share_page_access_token_hash = db.Column(db.String(128))  # 分享页面访问令牌的「哈希」

    def __repr__(self):
        return f'<SharedFileInfo id: {self.id}, cloud_file_id: {self.cloud_file_id}, owner_id: {self.owner_id}, timestamp: {self.timestamp}, share_code_hash: {self.share_code_hash}, expiry_time: {self.expiry_time}, allowed_download_count: {self.allowed_download_count}, used_download_count: {self.used_download_count}>'


    def is_expired(self) -> bool:
        from datetime import datetime
        if self.expiry_time is None:  # 永不过期
            return False
        if datetime.utcnow() > self.expiry_time:
            return True
        return False
    

    def _generate_random_string(self, length) -> str:
        import random
        import string

        letters = (
            string.ascii_lowercase + string.digits
        )
        random_string = "".join(random.choice(letters) for i in range(length))
        return random_string


    def set_share_code(self, share_code_length: int = 16, share_page_access_token_hash_length: int = 16) -> str:
        """生成 `分享码` 并保存 `分享码哈希` 到数据库，生成并保存 `share_page_access_token`，返回 `分享码字符串`"""

        assert share_code_length >= 8, "share_code_length must >= 8"
        assert share_code_length <= 32, "share_code_length must <= 32"
        assert self.share_code_hash is None, "Error! share_code_hash must have not been set before"

        share_code = self._generate_random_string(share_code_length)

        self.share_code_hash = generate_password_hash(
            share_code,
            method="pbkdf2:sha256:600000",
            salt_length=16,
        )

        self.share_page_access_token_hash = generate_password_hash(
            self._generate_random_string(share_page_access_token_hash_length),
            method="pbkdf2:sha256:600000",
            salt_length=16,
        )

        return share_code


    def validate_share_code(self, share_code: str) -> bool:
        """验证 `分享码`"""
        return check_password_hash(self.share_code_hash, share_code)
    

    def validate_share_page_access_token(self, share_page_access_token: str) -> bool:
        """验证 `分享页面访问令牌`"""
        return check_password_hash(self.share_page_access_token_hash, share_page_access_token)