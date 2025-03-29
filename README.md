# proxy-restful
基于FastAPI 开发的 restful 风格的代理服务器, 内置集成了计费功能，支持 requests,cloudscraper 两种请求引擎

#如何使用
pip install -r requirement.ini

修改config.py 中的数据库,Redis 配置,修改config.py 中的server_out_ips, 配置服务器支持的多张网卡的ip地址

python main.py, 即可启动服务器,默认运行在 12580端口, 可以访问http://127.0.0.1:12580/docs 来查看接口文档 

注意:初始用户名为admin,密码将会保存到当前目录下的 admin_default_password 文件中,请及时修改密码。 

建议使用https 反向代理来增强安全性,
