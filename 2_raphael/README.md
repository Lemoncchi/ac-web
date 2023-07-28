# Raphael 个人报告
## 负责内容

- 密钥管理体系设计
- 项目的部署及https绑定证书
- 代码整合及debug~~最后演变成了彻底重写~~
    重构内容包括：
    - index，cloud_file_list等html模板
    - views.py中index，download，upload，register
    - models.py中的文件上传与加解密方法



## 密钥管理体系设计

具体内容及前后区别已在畅课上发贴。

## 部署项目并配置https
1. 部署项目到服务器，并使用nginx设置反向代理。
    1. 在服务器端安装nginx，在`/etc/nginx/sites-available`下新建配置文件`myflaskapp``

        ```perl
        server {
        listen 443 ssl;
        server_name myflaskapp.com;
        if ($host != 'myflaskapp.com') {
            return 403;
        }

        ssl_certificate /root/certificate.crt;
        ssl_certificate_key /root/private_key.key;

        location / {
            proxy_pass http://localhost:5001;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            }
        }
        ```

    2. 链接到`../site-enabled`，并重启nginx

    3. 启动flask，在本地访问myflaskapp.com。同时可以测试无法通过IP地址访问。

    4. 将自己签的证书添加到浏览器的信任列表中。（后来发现这样做还是会有不安全提示，因为没有签一条完整的证书链，只有服务器证书）



## 问题日志

- 7/23： 合并代码时讨论，认为当前密钥管理体系不能很好应对预设的风险场景，故重新设计了密钥管理体系。（新旧密钥管理框架已在畅课上发帖讨论）

- 7/24：
    - load_user函数里面的abort无故被调用导致报错，此函数是我们参照的开源项目自带的，研究后没有发现实际用处，注释掉abort代码后暂时解决，没有发现后续影响
    - 解密并下载时，解密内容错误。后来发现是采用了CFB工作模式但没有保证IV一致导致的，换用EAX工作模式后解决。

- 7/25：本地git信息误删，重新从远端获取git信息

- 7/26: 生成私钥存在换行导致传递出现问题，在js中使用原数据字符串解决

- 7/28：
    - github移除了使用密码进行验证的方法，导致在服务器端部署时pull不下来仓库。换用ssh后解决
    - 发现部署到云服务器，即使是通过hosts来访问域名也会要求备案。所以又折腾到虚拟机上。


## 参考文献

- [url_for() 与 自定义动态路由过滤器](https://blog.csdn.net/Drifter_Galaxy/article/details/116106315)

- [使用openssl创建自签名的证书链](使用openssl创建自签名的证书链)

- [flask入门教程](https://read.helloflask.com/)

- [jinja2 Documention](https://docs.jinkan.org/docs/jinja2/)

- [Javascript 菜鸟教程](https://www.runoob.com/js/js-tutorial.html)

- [nginx Documention](https://nginx.org/en/docs/)