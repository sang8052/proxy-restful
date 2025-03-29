
from log import logging
import time, traceback, utils, config, model, json
from fastapi import WebSocket,WebSocketDisconnect
from fastapi import FastAPI, Request, Response,Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import iterate_in_threadpool
from fastapi.openapi.docs import get_swagger_ui_html
import os
import g

description = """
一个基于FastApi 构建的 Proxy-Server 

支持使用Request,Cloudscraper两种方案代理请求

mail: mail@szhcloud.cn
"""
app = FastAPI(
    title=config.fastapi_swagger_site_name,
    description=description,
    version=config.system_version,
    docs_url =  "/docs" if config.fastapi_enable_swagger  else False
)


if  config.fastapi_enable_swagger:
    logging.warning("注意: 已开启swagger 文档,请勿在生产环境下使用!")

    



def check_url_rules(base_url,rules):
    for rule in rules:
        if base_url == rule:
            return True
        else:
            if rule.endswith("*"):
                rule = rule[0:-1]
                if base_url.startswith(rule):
                    return True
    return False


@app.exception_handler(Exception)
async def http_exception_handle(request,exc):
    if not hasattr(request,"env"):
        env = {
        "request_starttime":int(time.time() * 1000),
        "request_id": utils.get_uuid_v4(),
        "request_user_agent":request.headers.get("user-agent",None)
        }
        request.env = env
    try:
        request_body =  await request.body()
        request_body = request_body.decode("utf-8")
    except:
        request_body = "[multipart/form-data]"
    request_payload = {"headers":dict(request.headers),"body":request_body,"query":dict(request.query_params)}
    data = request_payload
    data["error"] = traceback.format_exc()
    data["request_id"] = request.env["request_id"]
    return await response_exception_json(request,{"code":500,"msg":"未知异常","data":data})

@app.middleware("http")
async def faskapi_http_middleware(request:Request, call_next):
    if not hasattr(request,"env"):
        env = {
            "request_starttime":int(time.time() * 1000),
            "request_id": utils.get_uuid_v4(),
            "request_user_agent":request.headers.get("user-agent",None)
        }
        request.env = env
    user_session = None
    session_id = ""
    if request.method != "OPTIONS":
        # 如果请求的是代理接口,要求header 中有 x-proxy-token
        base_url = str(request.url.path)
        if base_url.startswith("/api/proxy/requests") or base_url.startswith("/api/proxy/cloudscraper"):
            x_proxy_token = request.headers.get("x-proxy-token")
            if not x_proxy_token or not g.xcache.query_token_info(x_proxy_token):
                return await response_exception_json(request,{"code":403,"msg":"proxy-token 不存在!"},403)
        else:
            session_id = request.headers.get("x-session-id")
            if not session_id:
                session_id = ""
            user_session = g.xcache.query_user_session(session_id)
            # 判断请求的接口是否需要登录
            if not check_url_rules(base_url,config.fastapi_nologin_rules) and not user_session:
                return await response_exception_json(request,{"code":403,"msg":"请先登录!","data":{"path":base_url,"session_id":session_id,"no_login_rules":config.fastapi_nologin_rules}},403)

            # 判断是否访问的是管理员的接口
            if user_session:
                if check_url_rules(base_url,config.fastapi_admin_rules) and not user_session["is_admin"]:
                    return await response_exception_json(request,{"code":403,"msg":"无权限访问!"},403)

    # 更新session 的有效期
    if user_session:
        g.xcache.update_user_session(session_id)

    response = await call_next(request)
    
    using_time = int(time.time() * 1000) - env["request_starttime"]
    request_time = int(request.env["request_starttime"] / 1000)

    response.headers["X-Request-Id"] = env["request_id"]
    response.headers["X-Using-Time"] = str(using_time)


    return response

async def response_exception_json(request,exception,status_code=500):
    env = request.env
    try:
        request_body =  await request.body()
        request_body = request_body.decode("utf-8")
    except:
        request_body = "[multipart/form-data]"
    request_payload = {"headers":dict(request.headers),"body":request_body,"query":dict(request.query_params)}

    using_time = int(time.time() * 1000) - env["request_starttime"]
    request_time = int(request.env["request_starttime"] / 1000)
    response_content = json.dumps(exception,ensure_ascii=False)
    response_size = len(response_content)
    response = Response(response_content,status_code)
    response.headers["X-Request-Id"] = env["request_id"]
    response.headers["X-Using-Time"] = str(using_time)
    response.headers["Content-Type"] = "application/json;charset=utf-8"
    return response

def get_client_ip(request: Request) -> str:
    # 尝试从 X-Forwarded-For 中获取（适用于多级代理）
    x_forwarded_for = request.headers.get("X-Forwarded-For", "")
    if x_forwarded_for:
        # 取第一个非空 IP（格式：client, proxy1, proxy2）
        ip = x_forwarded_for.split(",")[0].strip()
        if ip:
            return ip

    # 尝试从其他常见代理头获取
    headers_to_check = [
        "X-Client-IP",  # 单级代理
        "X-Real-IP",     # Nginx 默认传递的真实 IP
    ]
    for header in headers_to_check:
        ip = request.headers.get(header, "")
        if ip:
            return ip

    # 直接获取连接的客户端 IP（不经过代理时生效）
    return request.client.host if request.client else "unknown"

from . import schemas
from . import server
from . import admin
from . import user 
from . import proxy

