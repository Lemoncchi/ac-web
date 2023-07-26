#import os
#import pathlib
#
#secret_folder = os.path.join(pathlib.Path(__file__).parent.absolute(), "secrets")
#
#class AdminLocker:
#    """代表服务器, 管理服务器的 `公私钥对`"""
#
#    def __init__(self):
#        self._private_key: bytes = b""  # 服务器私钥（二进制）
#        self._public_key: bytes = b""
#
#        # 从环境变量中读取服务器私钥
#        # self._private_key = bytes.fromhex(os.getenv('SERVER_PRIVATE_KEY'))
#        # if self._private_key is None:
#        #     raise ValueError('服务器私钥环境变量不存在, 请先运行 `generate_server_key.py` 生成公私钥对')
#
#        # 从文件中读取服务器私钥
#        try:
#            with open(os.path.join(secret_folder, 'server_private_key'), 'rb') as f:
#                self._public_key = f.read()
#        except FileNotFoundError:
#            raise ValueError('服务器私钥文件不存在, 请先运行 `generate_server_key.py` 生成公私钥对')
#
#        # 从文件中读取服务器公钥
#        try:
#            with open(os.path.join(secret_folder, 'server_public_key.pub'), 'rb') as f:
#                self._public_key = f.read()
#        except FileNotFoundError:
#            raise ValueError('服务器公钥文件不存在, 请先运行 `generate_server_key.py` 生成公私钥对')
#    
#
#    def sign(self, content_: bytes) -> bytes:
#        """对 content_ 进行签名"""
#        pass  # TODO
#
#    def verify(self, content_: bytes, signature: bytes) -> bool:
#        """验证签名是否正确"""
#        return True  # TODO: 验证签名是否正确
#
#    def encrypt(self, content_: bytes) -> bytes:
#        """对 content_ 使用私钥进行加密"""
#        encrypted_content = content_  # TODO: 使用私钥加密 content_
#        return encrypted_content
#
#    def decrypt(self, content_: bytes) -> bytes:
#        """对 content_ 使用公钥进行解密"""
#        decrypted_content = content_  # TODO: 使用公钥解密 content_
#        return decrypted_content
#
#admin_locker = AdminLocker()
