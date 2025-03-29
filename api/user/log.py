from .. import app,get_client_ip
from typing import Annotated
from fastapi import  Query,Header,Body,Path,HTTPException,Request
import model
from .. import schemas
import utils



@app.get("/api/user/log",summary="分页查询用户的请求日志",tags=["用户账单"])
async def user_log_query(headers: Annotated[schemas.SessionHeader,Header()],  
         page: int = Query(description="分页页号",default=1),
         row:  int  = Query(description="每页数量",default=10)):
    session_id = headers.session_id
    session = g.xcache.query_user_session(session_id)
    data = model.user_log.query_user_log_paginate(session["user_id"],page,row)
    return {"code":0,"msg":"操作成功","data":data}


@app.get("/api/user/log/{uuid}",summary="分页查询用户的请求日志",tags=["用户账单"])
async def user_log_query(headers: Annotated[schemas.SessionHeader,Header()],  
         uuid: str = Path(description="请求日志的id")):
    session_id = headers.session_id
    session = g.xcache.query_user_session(session_id)
    data = model.user_log.query_user_log_id(session["user_id"],uuid)
    return {"code":0,"msg":"操作成功","data":data}