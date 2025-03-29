from sqlmodel import Field, SQLModel,Relationship,select,Session,func,Column
from typing import List, cast,Annotated
from sqlalchemy.dialects.mysql import LONGTEXT,TEXT

from sqlalchemy.sql import and_
import sqlalchemy
import config ,utils,g
sqlEngine = sqlalchemy.engine.base.Engine
import logging
from model import paginate_query
import redis

class user_log(SQLModel,table=True):
    uuid: str = Field(primary_key=True,unique=True)
    user_id: int = Field(description="用户的id")
    auth_token:str = Field(description="请求使用的token")
    base_host:str = Field(description="请求的域名")
    base_url: str = Field(description="请求的url",sa_column=Column(TEXT))
    base_engine: str = Field(description="请求的模块")
    request_method: str = Field(description="请求的method")
    request_client_ip: str = Field(description="请求的客户端的ip地址")
    data_size:float = Field(description="响应的数据包大小,单位kb",nullable=True)
    using_time:int = Field(description="请求花费的时间,单位ms",nullable=True)
    response_code:int = Field(description="响应的代码",nullable=True)
    create_time: int = Field()
    update_time: int = Field(nullable=True)


def create_request_log(user_id:int,auth_token:str,base_host:str,base_url:str,base_engine:str,request_method:str,request_client_ip:str):
    with g.get_session() as session:
        log = user_log(
            uuid = utils.get_uuid_v4(),
            user_id=user_id,
            auth_token=auth_token,
            base_host = base_host,
            base_url = base_url,
            base_engine= base_engine,
            request_method = request_method,
            request_client_ip = request_client_ip,
            create_time = utils.get_timestamp('s')
        )
        session.add(log)
        session.commit()
        session.refresh(log)
        return log.uuid

def update_request_log(uuid:str,data_size:float,using_time:int,response_code:int):
    with g.get_session() as session:
        query = select(user_log).where(user_log.uuid == uuid)
        log = session.exec(query).one_or_none()
        log.data_size = data_size 
        log.using_time =using_time 
        log.response_code = response_code 
        log.update_time = utils.get_timestamp('s')
        session.add(log)
        session.commit()
        
def query_user_log_paginate(user_id:int,page:int,row:int):
    with config.get_session() as session:
        query = select(user_log).where(user_log.user_id == user_id).order_by(user_log.create_time)
        return paginate_query(session, query,page,row)


def query_user_log_id(user_id:int,uuid:str):
    with config.get_session() as session:
        query = select(user_log).where(and_(user_log.user_id == user_id,user_log.uuid == uuid) )
        log = session.exex(query).one_or_none()
        return log



