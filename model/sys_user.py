from sqlmodel import Field, SQLModel,Relationship,select,Session,func
from typing import List, cast,Annotated
import sqlalchemy,json 
import config ,utils,g 
sqlEngine = sqlalchemy.engine.base.Engine
import logging
from model import paginate_query
from model import user_token,user_bill

class sys_user(SQLModel,table=True):

    id: int = Field(primary_key=True)
    username: str = Field(description="用户名",unique=True)
    password: str = Field(description="密码")
    salt: str = Field(description="加密用的盐")
    nickname: str = Field(description="用户的昵称/姓名")
    last_login_ip: str = Field(description="上一次登录的时间",nullable=True)
    last_login_time: int = Field(description="上一次登录的时间",nullable=True)
    balance: int = Field(description="用户的余额",default=0)
    is_admin: bool = Field(description="是否管理员",default=False)
    create_time: int = Field()
    update_time: int = Field(nullable=True)



def query_user_by_username(username: str):
    with g.get_session() as session:
        query = select(sys_user).where(sys_user.username == username)
        user = session.exec(query).one_or_none()
        return user
    
def query_exist_admin_user():
    with g.get_session() as session:
        query = select(func.count()).where(sys_user.is_admin == True)
        user = session.exec(query).one()
        if user == 0:
            return False
        return True

def verify_user_login(username:str,password:str):
    with g.get_session() as session:
        query = select(sys_user).where(sys_user.username == username)
        user = session.exec(query).one_or_none()
        if not user:
            logging.debug("尝试登录的用户[%s]不存在" % (username))
            return None
        _password = utils.hash_text(user.salt + ":" + password,"sha256")
        if _password != user.password:
            logging.debug("尝试登录的用户[%s]错误,传入密码:%s,数据库中密码:%s" % (username,_password,user.password))
            return None
        return user
        
def update_user_password(user_id:str,password:str):
    with g.get_session() as session:
        query = select(sys_user).where(sys_user.id == user_id)
        user = session.exec(query).one_or_none()
        salt = utils.get_uuid_v4()
        user.salt = salt
        user.password = utils.hash_text(salt + ":" + password,"sha256")
        user.update_time = utils.get_timestamp('s')
        session.add(user)
        session.commit()
        session.refresh(user)

def update_user_nickname(user_id:str,nickname:str):
    with g.get_session() as session:
        query = select(sys_user).where(sys_user.id == user_id)
        user = session.exec(query).one_or_none()
        user.nickname = nickname
        user.update_time = utils.get_timestamp('s')
        session.add(user)
        session.commit()
        session.refresh(user)


def create_user(username:str,password:str,nickname:str,is_admin=False):
    with g.get_session() as session:
        salt = utils.get_uuid_v4()
        user = sys_user(
            username=username,
            salt=salt,
            nickname=nickname,
            password=utils.hash_text(salt + ":" + password,"sha256"),
            is_admin = is_admin,
            create_time=utils.get_timestamp('s')
        )
        session = cast(Session,session)
        session.add(user)
        session.commit()
        session.refresh(user)
        return user.id


def query_system_user_info():
    with g.get_session() as session:
        query = select(func.count()).select_from(sys_user)
        total_user = session.exec(query).one()
        query = select(func.count()).select_from(sys_user).where(sys_user.last_login_time > utils.get_timestamp('today'))
        total_today_login = session.exec(query).one()
        return total_user, total_today_login

def query_sys_user_paginate(page=1,row=10):
    with g.get_session() as session:
        query = select(sys_user)
        return paginate_query(session, query,page,row)

def query_sys_user_by_user_id(user_id:int):
    with g.get_session() as session:
        query = select(sys_user).where(sys_user.id == user_id)
        user = session.exec(query).one_or_none()
        return user
    
def update_sys_user_by_user_id(user_id:int,nickname:str,is_admin:bool,password:str=""):
    with g.get_session() as session:
        user = query_sys_user_by_user_id(user_id)
        user.nickname = nickname
        if user.password:
            user.salt = utils.get_uuid_v4()
            user.password = utils.hash_text(user.salt + ":" + password,'sha256')
        user.is_admin = is_admin
        user.update_time = utils.get_timestamp('s')
        session.add(user)
        session.commit()
        session.refresh(user)


def delete_sys_user_by_user_id(user_id:int):
    with g.get_session() as session:
        user = query_sys_user_by_user_id(user_id)
        session.delete(user)
        session.commit()
        # 查询这个用户的所有token 
        tokens = user_token.query_tokens_by_user(user_id)
        for token in tokens:
            g.xcache.delete_token(token.auth_token)
            session.delete(token)
            session.commit()
        

def login_with_user_id(user_id:int,client_ip:str):
    user = query_sys_user_by_user_id(user_id)
    user.last_login_ip = client_ip
    user.last_login_time =  utils.get_timestamp('s')
    session_id = utils.get_uuid_v4()
    session = {"user_id":user.id,"username":user.username,"is_admin":user.is_admin}
    g.xcache.get_client().set(config.cache_proxy_session_prefix + session_id,json.dumps(session),600)
    return session_id


def update_user_balance(user_id:int,cash:int,title:str,log_id:int="",extend:str=""):
    with g.get_session() as session:
        with session.begin():
            user = session.execute(
                select(sys_user)
                .where(sys_user.id == user_id)
                .with_for_update()
            ).scalar_one_or_none()
            user.balance = user.balance + cash
            # 插入账单信息
            user_bill.create_user_bill(user_id,cash,user.balance,title,log_id,extend)
            session.add(user)
        return user
            
    



