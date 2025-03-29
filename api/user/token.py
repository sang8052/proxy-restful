from fastapi import  Query,Header,Body,Path,HTTPException,Request
import time
from sqlalchemy.exc import IntegrityError
import model
from .. import app,get_client_ip,schemas
import utils
from typing import Annotated
import g 

@app.get("/api/user/token", summary="获取用户的所有Token", tags=["Token管理"])
async def get_user_tokens(headers: Annotated[schemas.SessionHeader, Header()]):
    """查询当前用户的所有Token"""
    session_data = g.xcache.query_user_session(headers.session_id)
    user_id = session_data["user_id"]
    tokens = model.user_token.query_tokens_by_user(user_id)
    return {"code": 0, "msg": "成功", "data": tokens}

@app.post("/api/user/token", summary="创建新的Token", tags=["Token管理"])
async def create_user_token(
    headers: Annotated[schemas.SessionHeader, Header()],
       body:schemas.TokenCreate
):
    """创建新Token（每个用户最多5个）"""
    # 获取用户信息
    session_data = g.xcache.query_user_session(headers.session_id)
    user_id = session_data["user_id"]
    
    token_nums = model.user_token.query_token_nums_by_user(user_id)
    if token_nums > 5:
        return {"code": 500, "msg": "每个用户最多只能创建5个token", "data": None}

    auth_token = utils.get_uuid_v4()
    token = model.user_token.create_user_token(user_id,auth_token,body.extend)
    return {"code": 0, "msg": "创建成功", "data": {"id":token.id,"token":auth_token}}

@app.put("/api/user/token/{token_id}", summary="更新Token备注", tags=["Token管理"])
async def update_user_token(
    headers: Annotated[schemas.SessionHeader, Header()],
    body:schemas.TokenCreate,
    token_id: Annotated[int, Path(..., description="要修改的Token ID")],
):
    """修改Token的备注信息"""
    # 获取用户信息
    session_data = g.xcache.query_user_session(headers.session_id)
    user_id = session_data["user_id"]
    token = model.user_token.query_token_by_id(token_id)
    if token.user_id != user_id:
        return {"code": 500, "msg": "无权限修改该token", "data": None}
    model.user_token.update_user_token_extend(token_id,body.extend)
    return {"code": 0, "msg": "更新成功", "data": token}

@app.delete("/api/user/token/{token_id}", summary="删除Token", tags=["Token管理"])
async def delete_user_token(
    headers: Annotated[schemas.SessionHeader, Header()],
    token_id: Annotated[int, Path(..., description="要删除的Token ID")]
):
    """删除指定Token"""
    # 获取用户信息
    session_data = g.xcache.query_user_session(headers.session_id)
    user_id = session_data["user_id"]
    session_data = g.xcache.query_user_session(headers.session_id)
    user_id = session_data["user_id"]
    token = model.user_token.query_token_by_id(token_id)
    if token.user_id != user_id:
        return {"code": 500, "msg": "无权限修改该token", "data": None}

    model.user_token.delete_token(token_id)
    return {"code": 0, "msg": "删除成功"}