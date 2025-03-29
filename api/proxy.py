from . import app,get_client_ip
from typing import Annotated
from fastapi import  Query,Header,Body,Path,HTTPException,Request,Response
import model
from . import schemas
import utils
import g,config
import requests,cloudscraper
from urllib.parse import urlparse
import traceback
import random,json 
from log import logging
from requests.adapters import HTTPAdapter
import math 

class SourceAddressAdapter(HTTPAdapter):
    """支持指定出口IP的自定义适配器"""
    def __init__(self, source_address, **kwargs):
        self.source_address = source_address
        super().__init__(**kwargs)

    def init_poolmanager(self, *args, **kwargs):
        kwargs["source_address"] = self.source_address
        super().init_poolmanager(*args, **kwargs)


def do_proxy_engine_request(headers,body,request,engine):
    # 通过token 获取用户信息
    proxy_token = headers.proxy_token
    token = g.xcache.query_token_info(proxy_token)
    user_id = token["user_id"]
    user = model.sys_user.query_sys_user_by_user_id(user_id)
    if user.balance <= 0:
        response_content = json.dumps({"code":503,"msg":"余额不足!","data":{"token":token,"user_id":user_id}})
        response = Response(response_content,503)
        response.headers["X-Porxy-User-Id"] = str(user_id)
        response.headers["X-Porxy-Token"] = proxy_token
        response.headers["X-Porxy-Balance"] = str(user.balance)
        response.headers["content-type"] = "application/json"

        return response
    else:
        body_header = utils.format_dict_key_lower(body.header)
        if "user-agent" not in body_header.keys():
            try:
                body_header["user-agent"] = body.user_agent
            except:
                pass 
        if "content_type" not in body_header.keys():
            try:
                content_type = body.content_type
                if content_type:
                    body_header["content-type"] = content_type
            except:
                pass 
        request_size = len(body.url) + len(body.method) + len(body.params) + len(body_header)
      
        request_init_time = utils.get_timestamp('ms')
        log_id = model.user_log.create_request_log(user_id,proxy_token,base_host,base_url,engine,body.method,get_client_ip(request))

        try:
            
            if engine == "requests":
                # 创建带出口IP绑定的Session
                out_ip = ""
                if body.out_ip:
                    out_ip = body.out_ip
                if out_ip not in config.server_out_ips:
                    index =random.randint(0,len(config.server_out_ips)-1)
                    out_ip = config.server_out_ips[index]
                session = requests.Session()
                adapter = SourceAddressAdapter(source_address=(out_ip, 0))
                session.mount('http://', adapter)
                session.mount('https://', adapter)
                client = session

            elif engine == "cloudscraper":
                client = cloudscraper.create_scraper() 

            resp = client.request(
                    method=body.method.upper(),
                    url=body.url,
                    headers=body_header,
                    params=body.params,
                    data=body.body,
                    timeout=30,
                    allow_redirects=body.allow_redirects
            )

        except Exception as error:
            error_content = {"code":500,"msg":"代理请求时发生异常","data":{"payload":dict(body),"exception":str(traceback.format_exc())}}
            logging.warning(error_content["data"]["exception"])
            response = Response(json.dumps(error_content) ,500)
            response.headers["X-Porxy-User-Id"] = str(user_id)
            response.headers["X-Porxy-Token"] = proxy_token
            response.headers["X-Porxy-Balance"] = str(user.balance)
            response.headers["content-type"] = "application/json"
            response.headers["X-Proxy-LogId"] = log_id

            return response

        request_end_time = utils.get_timestamp("ms")
        request_using_time = request_end_time - request_init_time

        response_size = len(resp.content) +  len(str(resp.headers).encode("utf-8"))
        total_size = request_size + response_size
        response = Response(resp.content,resp.status_code)
        for key in resp.headers.keys():
            new_key = "X-Response-" + key 
            response.headers[new_key] = resp.headers[key]
        parsed = urlparse(body.url)
        base_host = parsed.hostname 
        base_url = parsed.path 
        using_cash = math.ceil(total_size / 1024)

        # 计算请求花费的费用
        response.headers["X-Porxy-User-Id"] = str(user_id)
        response.headers["X-Porxy-Token"] = str(proxy_token)
        response.headers["X-Proxy-LogId"] = log_id
        response.headers["X-Proxy-UsingTime"] = str(request_using_time)
        response.headers["X-Proxy-DataSize"] = str(total_size)
        response.headers["X-Proxy-Cash"] = str(using_cash)
        try:
            response.headers["X-Proxy-OutIP"] = out_ip
        except:
            pass
        model.user_log.update_request_log(log_id,total_size,request_using_time,resp.status_code)
        model.sys_user.update_user_balance(user_id,using_cash,"代理请求访问[模式:%s]" % (engine),log_id)
        user = model.sys_user.query_sys_user_by_user_id(user.id)
        response.headers["X-Porxy-Balance"] = str(user.balance)
        response.headers["content-type"] = resp.headers['content-type']
        return response

@app.post("/api/proxy/requests",summary="使用Requests 代理请求",tags=["代理请求"])
async def user_proxy_requests(headers: Annotated[schemas.ProxyHeader,Header()],body:schemas.RequestBody,request:Request):
    return do_proxy_engine_request(headers,body,request,"requests")


"""
1.建议非必要不要在header 中传入 user-agent 
2.建议非必要少传header 参数 
3.此模式下不支持使用 out_ip 固定出网ip
"""
@app.post("/api/proxy/cloudscraper",summary="使用Cloudscraper 代理请求",tags=["代理请求"])
async def user_proxy_cloudscraper(headers: Annotated[schemas.ProxyHeader,Header()],body:schemas.RequestCloudScraperBody,request:Request):
    return do_proxy_engine_request(headers,body,request,"cloudscraper") 
