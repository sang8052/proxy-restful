

system_name = "Proxy RestFul"
system_version = "1.0.beta"

server_out_ips = ["1.1.1.1","2.2.2.2","3.3.3.3"]

# API 接口配置
fastapi_http_port = 12580
fastapi_enable_swagger = True 
fastapi_swagger_site_name = system_name

fastapi_nologin_rules = ["/api/user/login","/api/admin/login","/docs","/openapi.json"]
fastapi_admin_rules = ["/api/account*","/api/admin*"]

db_hostname = "127.0.0.1"
db_port =  3306
db_database = "you-database-name"
db_username = "username"
db_password = "password"

redis_hostname = "127.0.0.1"
redis_port = 6379
redis_password = "password"
redis_index = 5

cache_proxy_token_prefix = "proxy_restful:user_api_token:"
cache_proxy_session_prefix = "proxy_restful_user_session:"


