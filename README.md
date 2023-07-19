# 中传放心传

![example workflow](https://github.com/Mr-Nobodyl/ac-web/actions/workflows/ac-web_CI.yaml/badge.svg)

> 本仓库为密码学应用实践课程的课程项目 `中传放心传`，fork 自开源项目 [helloflask/watchlist](https://github.com/helloflask/watchlist)

> 对比与原开源项目的差异，可参考 https://github.com/Mr-Nobodyl/ac-web/compare/master...dev

## 功能清单

> 列表形式说明逐个功能要点。

- [ ] 基于网页的用户注册与登录系统（60 分）
  - [ ] 使用 https 绑定证书到域名而非 IP 地址 【 _PKI_ _X.509_ 】
  - [x] 允许用户注册到系统
    - [ ] 用户名的合法字符集范围：中文、英文字母、数字
      - [ ] 类似：-、\_、.等合法字符集范围之外的字符不允许使用
    - [x] 用户口令长度限制在 36 个字符之内
    - [ ] 对用户输入的口令进行强度校验，禁止使用弱口令
  - [x] 使用合法用户名和口令登录系统
  - [x] 禁止使用明文存储用户口令 【 _PBKDF2_ _散列算法_ _慢速散列_ _针对散列算法（如 MD5、SHA1 等）的攻击方法_ 】
    - [x] 存储的口令即使被公开，也无法还原/解码出原始明文口令
  - [ ] （可选）安全的忘记口令 / 找回密码功能
  - [ ] （可选）微信/微博/支付宝的 OAuth 授权登录 / 注册绑定
  - [ ] （可选）双因素认证
    - [ ] OTP: Google Authenticator
    - [ ] Email
    - [ ] SMS
    - [ ] 扫码登录
- [ ] 基于网页的文件上传加密与数字签名系统（20 分）
  - [ ] 已完成《基于网页的用户注册与登录系统》所有要求
  - [ ] 限制文件大小：小于 10MB
  - [ ] 限制文件类型：office 文档、常见图片类型
  - [x] 匿名用户禁止上传文件
  - [ ] 对文件进行对称加密存储到文件系统，禁止明文存储文件 【 _对称加密_ _密钥管理（如何安全存储对称加密密钥）_ _对称加密密文的 PADDING 问题_ 】
  - [ ] 系统对加密后文件进行数字签名 【 _数字签名（多种签名工作模式差异）_ 】
  - [ ] （可选）文件秒传：服务器上已有的文件，客户端可以不必再重复上传了
- [ ] 基于网页的加密文件下载与解密（20 分）
  - [ ] 已完成《基于网页的文件上传加密与数字签名系统》所有要求
  - [ ] 提供匿名用户加密后文件和关联的数字签名文件的下载
    - [ ] 客户端对下载后的文件进行数字签名验证 【 _非对称（公钥）加密_ _数字签名_ 】
    - [ ] 客户端对下载后的文件可以解密还原到原始文件 【 _对称解密_ _密钥管理_ 】
  - [ ] 提供已登录用户解密后文件下载
  - [ ] 下载 URL 设置有效期（限制时间或限制下载次数），过期后禁止访问 【 _数字签名_ _消息认证码_ _Hash Extension Length Attack_ _Hash 算法与 HMAC 算法的区别与联系_ 】
  - [ ] 提供静态文件的散列值下载，供下载文件完成后本地校验文件完整性 【 _散列算法_ 】

## 本项目用到的关键技术

> 本作品中包含的密码学理论与技术示范应用要点说明，列表形式、逐个要点说明。

## 快速上手体验

> 快速安装与使用方法说明。

clone:

```
$ git clone https://github.com/Mr-Nobodyl/ac-web.git
$ cd ac-web
```

激活虚拟环境 & 安装依赖:

```
$ python3 -m venv env  # use `python ...` on Windows
$ source env/bin/activate  # use `env\Scripts\activate` on Windows
(env) $ pip install -r requirements.txt
```

初始化数据库并生成测试数据:

```
(env) $ flask forge  # 初始用户名为: CUCer 密码: 123456
(env) $ flask run
* Running on http://127.0.0.1:5001/
```

## 演示

> 课程结题报告与系统功能操作视频演示地址。

## License

This project is licensed under the MIT License (see the
[LICENSE](LICENSE) file for details).
