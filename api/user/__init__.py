from .. import app,get_client_ip
from typing import Annotated
from fastapi import  Query,Header,Body,Path,HTTPException,Request
import model
from .. import schemas
import utils
import g 

@app.post("/api/user/login",summary="用户登录接口",tags=["用户信息"])
async def user_login(body:schemas.UserLogin,request:Request):
    user = model.sys_user.verify_user_login(body.username,body.password)
    if not user:
        return {"code":403,"msg":"用户名或密码不正确","data":None}
    else:
        last_login_ip = user.last_login_ip
        last_login_time = user.last_login_time
        session_id = model.sys_user.login_with_user_id(user.id,get_client_ip(request))
    return {"code":0,"msg":"操作成功","data":{"user_id":user.id,"session_id":session_id,"last_login_ip":last_login_ip,"last_login_time":last_login_time}}

@app.get("/api/user",summary="查询当前用户的信息",tags=["用户信息"])
async def user_info(headers: Annotated[schemas.SessionHeader, Header()]):
    session_id = headers.session_id
    session = g.xcache.query_user_session(session_id)
    user = model.sys_user.query_sys_user_by_user_id(session["user_id"])
    user = dict(user)
    del user["password"]
    del user["salt"]
    user["user_id"] = user["id"]
    del user["id"]
    return {"code":0,"msg":"操作成功","data":{"user":user,"session_id":session_id}}

@app.delete("/api/user",summary="退出登录",tags=["用户信息"])
async def user_delete(headers: Annotated[schemas.SessionHeader,Header()]):
    session_id = headers.session_id
    g.xcache.delete_user_session(session_id)
    return {"code":0,"msg":"操作成功","data":None}

@app.post("/api/user",summary="修改当前用户的信息",tags=["用户信息"])
async def user_update(headers: Annotated[schemas.SessionHeader,Header()],body: schemas.UserInfoUpdate):
    session_id = headers.session_id
    session = g.xcache.query_user_session(session_id)
    user = model.sys_user.query_sys_user_by_user_id(session["user_id"])
    if body.old_password:
        verify = db_model.sys_user.verify_user_login(user.username,body.old_password)
        if not verify:
            return {"code": 403, "msg": "原密码不正确", "data": None}
        else:
            db_model.sys_user.update_user_password(user.id,body.new_password)
    if body.nickname:
        db_model.sys_user.update_user_nickname(user.id,body.nickname)
    return {"code":0,"msg":"操作成功","data":{"session_id":session_id}}




from . import bill
from . import log 
from . import token






