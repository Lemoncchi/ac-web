from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Signature import pkcs1_15


# 对称密钥生成
def symmetric_generate():
    key = get_random_bytes(32)
    return key


# 对称加密
def symmetric_encode(data, key):
    cipher = AES.new(key,AES.MODE_CFB)
    return cipher.encrypt(data)


# 对称解密
def symmetric_decode(data_encode, key):
    cipher = AES.new(key,AES.MODE_CFB)
    return cipher.decrypt(data_encode)


# 哈希
def hash_code(data):
    data_hash = SHA256.new(data)
    s_data = data_hash.hexdigest()
    return s_data


# 非对称公私钥对生成
def encrypt_generate():
    key = RSA.generate(2048)
    private_key_string = key.export_key().decode('utf-8')
    public_key = key.publickey().export_key()
    return public_key, private_key_string


# RSA加密
def RSA_encode(data, public_key):
    publicKey = RSA.import_key(public_key)
    cipher = PKCS1_OAEP.new(publicKey)
    data_encode = cipher.encrypt(data)
    return data_encode


# RSA解密
def RSA_decode(data_encode, private_key_string):
    privateKey = RSA.import_key(private_key_string)
    cipher = PKCS1_OAEP.new(privateKey)
    data = cipher.decrypt(data_encode)
    return data


# RSA签名
def RSA_sign(data, private_key_string):
    pri_key = RSA.import_key(private_key_string)
    data_hash = SHA256.new(data)
    signature = pkcs1_15.new(pri_key).sign(data_hash)
    return signature


# 签名检验
def verify(signature, public_key, data):
    pub_key = RSA.import_key(public_key)
    data_hash = SHA256.new(data)
    return pkcs1_15.new(public_key).verify(data_hash, signature)
