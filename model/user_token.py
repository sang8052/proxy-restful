from sqlmodel import Field, SQLModel,Relationship,select,Session,func
from typing import List, cast,Annotated
import sqlalchemy
import config ,utils,g
sqlEngine = sqlalchemy.engine.base.Engine
import logging
from model import paginate_query
import redis

class user_token(SQLModel,table=True):
    id: int = Field(primary_key=True)
    user_id: int = Field(description="用户的id")
    auth_token: str = Field(description="请求token",unique=True)
    extend: str = Field(description="备注信息")
    create_time: int = Field()
    update_time: int = Field(nullable=True)

def create_user_token(user_id:int,auth_token:str,extend:str=""):
    with g.get_session() as session:
        token = user_token(
            user_id = user_id ,
            auth_token = auth_token,
            extend = extend ,
            create_time = utils.get_timestamp('s')
        )
        session.add(token)
        session.commit()
        session.refresh(token)
        return token.id 

def query_token_by_id(id:int):
    with g.get_session() as session:
        query = select(user_token).where(user_token.id == id)
        token = session.exec(query).one_or_none()
        return token

def update_user_token_extend(id:int,extend:str=""):
    with g.get_session() as session:
        query = select(user_token).where(user_token.id == id)
        token = session.exec(query).one_or_none()
        token.extend = extend 
        session.add(token)
        session.commit()
        session.refresh(token)
    



def query_tokens_by_user(user_id:int):
    with g.get_session() as session:
        query = select(user_token).where(user_token.user_id == user_id)
        tokens = session.exec(query).all()
        return tokens 

def query_token_nums_by_user(user_id:int):

    with g.get_session() as session:
        count = session.exec(
            select(func.count()).where(user_token.user_id == user_id)
        ).one_or_none()
        return count


def query_token_info(token:str):
    with g.get_session() as session:
        query = select(user_token).where(user_token.auth_token == token)
        info = session.exec(query).one_or_none()
        return info 

def delete_token(id:int):
    with g.get_session() as session:
        query = select(user_token).where(user_token.auth_token == token)
        token = session.exec(query).one_or_none()
        if token:
            session.delete(token)
            session.commit()
        client:redis.Redis = g.xcache.get_client()
        client.delete(config.cache_proxy_token_prefix + token.auth_token)


