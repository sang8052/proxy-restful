from .. import app,get_client_ip
from typing import Annotated
from fastapi import  Query,Header,Body,Path,HTTPException,Request
import model
from .. import schemas
import utils

@app.get("/api/admin/account",summary="分页列出用户",tags=["用户管理"])
async def account_list(headers: Annotated[schemas.SessionHeader, Header()],
        page: int = Query(description="分页页号",default=1),
        row:  int  = Query(description="每页数量",default=10)
    ):
    session_id = headers.session_id
    paginate = model.sys_user.query_sys_user_paginate(page,row)
    data = []
    for record in paginate.data:
        record = dict(record)
        record["user_id"] = record["id"]
        del record["password"]
        del record["id"]
        del record["salt"]
        data.append(record)
    paginate.data = data 
    return {"code":0,"msg":"操作成功","data":paginate.dict()}

@app.get("/api/admin/account/{user_id}",summary="用户详情",tags=["用户管理"])
async def account_detail(headers: Annotated[schemas.SessionHeader, Header()],
        user_id: int = Path(description="用户id")
    ):
    session_id = headers.session_id
    user = model.sys_user.query_sys_user_by_user_id(user_id)
    if not user:
        return {"code": 500, "msg": "用户不存在!", "data": {"user_id": user_id}}
    user = dict(user)
    del user["password"]
    del user["salt"]
    user["user_id"] = user["id"]
    del user['id']
    return {"code":0,"msg":"操作成功","data":user}

@app.delete("/api/admin/account/{user_id}",summary="删除用户",tags=["用户管理"])
async def account_delete(headers: Annotated[schemas.SessionHeader, Header()],
        user_id: int = Path(description="用户id")
    ):
    session_id = headers.session_id
    has_user = model.sys_user.query_sys_user_by_user_id(user_id)
    if not has_user:
        return {"code": 500, "msg": "用户不存在!", "data": {"user_id": user_id}}

    db_model.mail_rule.delete_mail_rule_by_user_id(user_id)
    db_model.mail_verify.delete_mail_verify_by_user_id(user_id)
    db_model.sys_user.delete_sys_user_by_user_id(user_id)

    return {"code":0,"msg":"操作成功","data":{"user_id":user_id}}

@app.post("/api/admin/account/{user_id}",summary="修改用户",tags=["用户管理"])
async def account_update(headers: Annotated[schemas.SessionHeader, Header()],
        body:schemas.AccountUpdate,
        user_id: int = Path(description="用户id"), 
    ):
    session_id = headers.session_id
    model.sys_user.update_sys_user_by_user_id(user_id,body.nickname,body.is_admin,body.password)
    return {"code":0,"msg":"操作成功","data":{"user_id":user_id}}

@app.post("/api/admin/account/{user_id}/recharge",summary="给用户充值",tags=["用户管理"])
async def account_recharge(headers: Annotated[schemas.SessionHeader, Header()],
        body:schemas.AccountRecharge,
        user_id: int = Path(description="用户id"), 
    ):
    session_id = headers.session_id
    model.sys_user.update_user_balance(user_id,body.cash,"管理员充值",None,body.extend)
    user = model.sys_user.query_sys_user_by_user_id(user_id)
    return {"code":0,"msg":"操作成功","data":{"user_id":user_id,"balance":user.balance}}

@app.post("/api/admin/account",summary="新增用户",tags=["用户管理"])
async def account_create(headers: Annotated[schemas.SessionHeader, Header()],
        body:schemas.AccountCreate,
    ):
    session_id = headers.session_id
    has_user = model.sys_user.query_user_by_username(body.username)
    if has_user:
        return {"code":500,"msg":"指定的用户已经存在","data":{"username":body.username}}
    user_id = model.sys_user.create_user(body.username,body.password,body.nickname,body.is_admin)
    return {"code":0,"msg":"操作成功","data":{"user_id":user_id}}