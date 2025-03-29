

system_name = "Proxy RestFul"
system_version = "1.0.beta"

server_out_ips = ["154.40.45.43","75.127.89.244"]

# API 接口配置
fastapi_http_port = 12580
fastapi_enable_swagger = True 
fastapi_swagger_site_name = system_name

fastapi_nologin_rules = ["/api/user/login","/api/admin/login","/docs","/openapi.json"]
fastapi_admin_rules = ["/api/account*","/api/admin*"]

db_hostname = "127.0.0.1"
db_port =  3306
db_database = "proxy-restful"
db_username = "proxy-restful"
db_password = "dbkWTYjrececKdNK"

redis_hostname = "127.0.0.1"
redis_port = 6379
redis_password = "P%to&3dk&ddHZv#W"
redis_index = 5


cache_proxy_token_prefix = "proxy_restful:user_api_token:"
cache_proxy_session_prefix = "proxy_restful_user_session:"


