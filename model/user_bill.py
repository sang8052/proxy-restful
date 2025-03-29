from sqlmodel import Field, SQLModel,Relationship,select,Session,func
from typing import List, cast,Annotated
import sqlalchemy
import config ,utils,g
sqlEngine = sqlalchemy.engine.base.Engine
import logging
from model import paginate_query
import redis

class user_bill(SQLModel,table=True):
    id: int = Field(primary_key=True)
    user_id: int = Field(description="用户的id")
    cash: int = Field(description="消费的金额")
    balance:int = Field(description="用户的余额")
    log_id:str = Field(description="关联的请求id",nullable=True)
    title: str = Field(description="账单标题信息",nullable=True)
    extend: str = Field(description="备注信息",nullable=True)
    create_time: int = Field()
    update_time: int = Field(nullable=True)


def create_user_bill(user_id:int,cash:int,balance:int,title:str,log_id:int="",extend:str=""):
    with g.get_session() as session:
        bill = user_bill(
            user_id = user_id,
            cash = cash ,
            balance = balance, 
            title = title,
            create_time = utils.get_timestamp('s'),
            log_id = log_id,
            extend = extend 
        )
        session.add(bill)
        session.commit()
        session.refresh(bill)
        return bill.id 

def query_user_bill_paginate(user_id:int,page:int,row:int):
    with config.get_session() as session:
        query = select(user_bill).where(user_bill.user_id == user_id).order_by(user_bill.create_time)
        return paginate_query(session, query,page,row)