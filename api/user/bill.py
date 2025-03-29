from .. import app,get_client_ip
from typing import Annotated
from fastapi import  Query,Header,Body,Path,HTTPException,Request
import model
from .. import schemas
import utils



@app.get("/api/user/bill",summary="分页查询用户账单",tags=["用户账单"])
async def user_bill_query(headers: Annotated[schemas.SessionHeader,Header()],  
         page: int = Query(description="分页页号",default=1),
         row:  int  = Query(description="每页数量",default=10)):
    session_id = headers.session_id
    session = g.xcache.query_user_session(session_id)
    data = model.user_bill.query_user_bill_paginate(session["user_id"],page,row)
    return {"code":0,"msg":"操作成功","data":data}