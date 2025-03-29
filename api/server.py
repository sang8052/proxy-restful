
from . import app,get_client_ip,schemas
from typing import Annotated
from fastapi import  Query,Header,Body,Path,HTTPException,Request
import model
import utils
import sys,fastapi,uvicorn,requests,cloudscraper
import config

@app.get("/api/system/server",summary="获取当前服务器的各个组件的版本",tags=["服务器信息"])
async def system_server_info(headers: Annotated[schemas.SessionHeader, Header()]):
    session_id = headers.session_id
    sys_info = {
        "os":utils.get_system_version(),
        "python":sys.version,
        "fastapi":fastapi.__version__,
        "uvicorn":uvicorn.__version__,
        "mysql":config.db_mysql_version,
        "requests":requests.__version__,
        "cloudscraper":cloudscraper.__version__,
        "version":config.system_version
    }
    return {"code":0,"msg":"操作成功","data":sys_info}


@app.get("/api/system/outips",summary="获取当前服务器的外网ip",tags=["服务器信息"])
async def system_server_info(headers: Annotated[schemas.SessionHeader, Header()]):
    session_id = headers.session_id
    outips = config.server_out_ips
    return {"code":0,"msg":"操作成功","data":outips}



