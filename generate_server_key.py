import os
import sys
from pathlib import Path

# 生成服务器的公私钥对，将私钥保存到环境变量中，将公钥保存到文件中
server_private_key: bytes = "TODO: 生成服务器的私钥并保存到环境变量中".encode()  # TODO
server_public_key: bytes = "TODO: 生成服务器的公钥并保存到文件中".encode()  # TODO

print("请妥善保管服务器私钥, 请勿泄露")
print(f"server_private_key: {server_private_key.hex()}")

server_secrets_folder = os.path.join(Path(__file__).parent.absolute(), "acweb", "secrets")

if not os.path.exists(server_secrets_folder):
    os.mkdir(server_secrets_folder)

with open(os.path.join(server_secrets_folder, "server_public_key.pub"), "wb") as f:
    f.write(server_public_key)

with open(os.path.join(server_secrets_folder, "server_private_key"), "wb") as f:
    f.write(server_private_key)

# WIN = sys.platform.startswith("win")
# if WIN:
#     print("请在命令行中执行以下命令, 将服务器私钥保存到环境变量中")
#     print(f"set SERVER_PRIVATE_KEY={server_private_key.hex()}")
# else:
#     print("请在命令行中执行以下命令, 将服务器私钥保存到环境变量中")
#     print(f"export SERVER_PRIVATE_KEY={server_private_key.hex()}")
