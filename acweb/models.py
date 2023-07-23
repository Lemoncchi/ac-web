import os
import typing
from datetime import datetime
import hmac
import hashlib
import werkzeug.datastructures
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from acweb import app, db
#from acweb.admin_locker import admin_locker
import security_code

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    public_key = db.Column(db.LargeBinary(2048))

    # 为用户生成一个随机公私钥对
    def generate_public_private_key(self):
        self.public_key, private_key = security_code.encrypt_generate()
        return private_key #  私钥传出，存储在配置文件
    

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
    
    @staticmethod
    def password_check(password):
        """
        Verify the strength of 'password'
        Returns a dict indicating the wrong criteria
        A password is considered strong if:
            8 characters length or more
            1 digit or more
            1 symbol or more
            1 uppercase letter or more
            1 lowercase letter or more
        """
        import re
        # calculating the length
        length_error = len(password) < 8

        # searching for digits
        digit_error = re.search(r"\d", password) is None

        # searching for uppercase
        uppercase_error = re.search(r"[A-Z]", password) is None

        # searching for lowercase
        lowercase_error = re.search(r"[a-z]", password) is None

        # searching for symbols
        symbol_error = re.search(r"[ !#$%&'()*+,-./[\\\]^_`{|}~"+r'"]', password) is None

        # overall result
        password_ok = not ( length_error or digit_error or uppercase_error or lowercase_error or symbol_error )

        return {
            'password_ok' : password_ok,
            'length_error' : length_error,
            'digit_error' : digit_error,
            'uppercase_error' : uppercase_error,
            'lowercase_error' : lowercase_error,
            'symbol_error' : symbol_error,
        }
    
    @staticmethod
    def is_valid_username(username) -> typing.Tuple[bool, str]:
        """
        Check if the given username only contains Chinese characters, English letters, and numbers.
        """
        if len(username) > app.config['MAX_USERNAME_LENGTH']:
            return False, "Username is too long."
        import re
        pattern_Chinese = re.compile(r'^[\u4e00-\u9fa5a-zA-Z0-9]+$')
        if not bool(pattern_Chinese.match(username)):
            return False, "Username can only contain Chinese characters, English letters, and numbers."
        return True, "Valid username."



class CloudFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # 外键
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)  # 默认设置为当前 UTC 时间
    file_name = db.Column(db.String(app.config['MAX_FILE_NAME_LENGTH']))
    file_save_name = db.Column(db.String(128))
    file_hash = db.Column(db.String(128))
    file_size = db.Column(db.Integer)
    encrypted_symmetric_key = db.Column(db.String(128)) #每个文件生成对称密钥


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
    
    def generate_save_symmetric_key(self,public_key) -> None:
        """生成对称密钥 & 保存其加密后的密文"""
        symmetric_key = security_code.symmetric_generate()  #  生成对称密钥
        self.encrypted_symmetric_key = security_code.RSA_encode(symmetric_key,public_key).hex()
        db.session.commit()

    def encrypt(self, private_key,content_: bytes) -> bytes:
        """使用文件对称密钥加密 content_"""
        symmetric_key = security_code.RSA_decode(bytes.fromhex(self.encrypted_symmetric_key),private_key)

        encrypted_content = security_code.symmetric_encode(content_,symmetric_key)  #  使用用户对称密钥 symmetric_key 加密 content_
        return encrypted_content
    
    def decrypt(self, private_key,content_: bytes) -> bytes:
        """使用用户对称密钥解密 content_"""
        symmetric_key = security_code.RSA_decode(bytes.fromhex(self.encrypted_symmetric_key),private_key)
        decrypted_content = security_code.symmetric_decode(content_,symmetric_key)#  使用用户对称密钥 symmetric_key 解密 content_
        
        return decrypted_content

    
    @staticmethod
    def save_encrypt_commit(user_id, file_name_, content_bytes_:bytes) -> "CloudFile":
        """保存文件元数据到数据库 & 保存加密后的文件到本地

        return: CloudFile
        """
        file_size_ = len(content_bytes_)

        import hashlib

        file_hash_ = hashlib.sha256(content_bytes_).hexdigest()
        # 对文件进行安全 hash

        file_save_name = file_hash_ # 保存文件时的文件名

        user = db.session.get(User, user_id)

        assert user is not None, "Error! user_id must be valid"

        private_key = None # TODO: 需要引入私钥配置文件

        #encrypted_content_bytes = CloudFile.encrypt(CloudFile(),private_key,content_bytes_)  # 对文件进行加密

        save_path = os.path.join(app.config['UPLOAD_FOLDER'], file_save_name)

        cloud_file = CloudFile(user_id=user_id, file_name=file_name_, file_save_name=file_save_name, file_hash=file_hash_, file_size=file_size_)
        db.session.add(cloud_file)
        db.session.commit()

        with open(save_path, 'wb') as f:  # 保存 文件 & 加密后的文件
            f.write(content_bytes_)#encrypted_content_bytes)  #TODO: 这里由于没有加密，使用未加密文件代替加密文件

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


    def file_decrypt(self) -> bytes:
        """对文件内容进行解密"""
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], self.file_save_name)

        with open(file_path, "rb") as f:
            encrypted_content_bytes = f.read()

        user = db.session.get(User, self.user_id)

        assert user is not None, "Error! user_id must be valid"

        # 对文件进行解密
        private_key = None # TODO: 需要引入私钥配置文件

        self.decrypted_content_bytes = encrypted_content_bytes #TODO:需要引入私钥，暂时以原文件代替 self.decrypt(private_key,encrypted_content_bytes)

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
    share_page_access_token_hash = db.Column(db.String(128), index=True)  # 分享页面访问令牌的「哈希」

    expiry_time = db.Column(db.DateTime)  # UTC 过期时间，None 表示永不过期

    allowed_download_count = db.Column(db.Integer, default=0)  # 允许下载次数，0 表示无限制
    used_download_count = db.Column(db.Integer, default=0)  # 已经下载次数

    

    def __repr__(self):
        return f'<SharedFileInfo id: {self.id}, cloud_file_id: {self.cloud_file_id}, owner_id: {self.owner_id}, timestamp: {self.timestamp}, share_code_hash: {self.share_code_hash}, share_page_access_token_hash: {self.share_page_access_token_hash},expiry_time: {self.expiry_time}, allowed_download_count: {self.allowed_download_count}, used_download_count: {self.used_download_count}>'


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


    def generate_save_share_code_and_access_token(
        self, share_code_length: int = 16, share_page_access_token_hash_length: int = 32
    ) -> typing.Tuple[str, str]:
        """生成 `share_code` & `share_page_access` 并保存其哈希到数据库

        返回 `share_code` & `share_page_access_token字符串`"""

        assert share_code_length >= 8, "share_code_length must >= 8"
        assert share_code_length <= 32, "share_code_length must <= 32"
        assert (
            self.share_code_hash is None
        ), "Error! share_code_hash must have not been set before"

        share_code = self._generate_random_string(share_code_length)

        self.share_code_hash = generate_password_hash(
            share_code,
            method="pbkdf2:sha256:600000",
            salt_length=16,
        )

        share_page_access_token = self._generate_random_string(
            share_page_access_token_hash_length
        )

        # 由于 share_page_access_token_hash 是索引，我们既需要保证其唯一性
        # 服务器端还能够计算其 hash 值，这里我们需要服务器端保存其盐值

        self.share_page_access_token_salt = self._generate_random_string(16)

        self.share_page_access_token_hash = hmac.new(
            app.config['HMAC_KEY'].encode("utf-8"),
            share_page_access_token.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        db.session.commit()

        return share_code, share_page_access_token  # 不会存储，妥善保存


    def validate_share_code(self, share_code: str) -> bool:
        """验证 `分享码`"""
        return check_password_hash(self.share_code_hash, share_code)
    

    def validate_share_page_access_token(self, share_page_access_token: str) -> bool:
        """验证 `分享页面访问令牌`"""
        return check_password_hash(self.share_page_access_token_hash, share_page_access_token)

    
    @staticmethod
    def get_by_share_page_access_token(
        share_page_access_token: str,
    ) -> typing.Optional["SharedFileInfo"]:
        share_page_access_token_hash = hmac.new(
            app.config["HMAC_KEY"].encode("utf-8"),
            share_page_access_token.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        return SharedFileInfo.query.filter_by(
            share_page_access_token_hash=share_page_access_token_hash
        ).first()


    