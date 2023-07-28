from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Signature import pkcs1_15
import pickle

def tuple_to_bytes(data):
    # 使用pickle将元组转化为字节流
    bytes_data = pickle.dumps(data)
    return bytes_data

def bytes_to_tuple(bytes_data):
    # 使用pickle将字节流转化为原始的元组对象
    tuple_data = pickle.loads(bytes_data)
    return tuple_data

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

def symmetric_generate():
    key = get_random_bytes(32)
    return key


def symmetric_encode(data, key):
    cipher = AES.new(key, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(data)
    return (ciphertext, cipher.nonce, tag)


def symmetric_decode(ciphertext,key):
    cipher = AES.new(key, AES.MODE_EAX, ciphertext[1])
    data = cipher.decrypt_and_verify(ciphertext[0], ciphertext[2])
    return data

if __name__ == "__main__":
    """
    #RSA测试

    public_key, private_key_string = encrypt_generate()

    # 待加密的数据
    original_data = b"Hello, World!"

    # 加密数据
    encrypted_data = RSA_encode(original_data, public_key)

    # 解密数据
    decrypted_data = RSA_decode(encrypted_data, private_key_string)

    # 验证解密后的数据与原始数据匹配
    if original_data == decrypted_data:
        print("RSA加密解密功能验证成功！")
    else:
        print("RSA加密解密功能验证失败！")
    """
    #AES加密测试
    symmetric_key = symmetric_generate()

    # 待加密的数据
    original_data = b"Hello, World!"

    # 加密数据
    ciphertext = symmetric_encode(original_data, symmetric_key)

    # 解密数据
    decrypted_data = symmetric_decode(ciphertext, symmetric_key)

    # 验证解密后的数据与原始数据匹配
    if original_data == decrypted_data:
        print("AES加密解密功能验证成功！")
    else:
        print("AES加密解密功能验证失败！")