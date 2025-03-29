from pydantic import BaseModel,Field
from fastapi import  Header





class SessionHeader(BaseModel):
    session_id:str = Header(description="当前会话的session_id",default="",alias="x-session-id")

class UserLogin(BaseModel):
    username:str = Field(description="用户名",default="admin")
    password:str = Field(description="密码")
    
class UserInfoUpdate(BaseModel):
    nickname:str = Field(description="用户的昵称",default="")
    new_password:str = Field(description="修改用户的密码",default="")
    old_password:str = Field(description="旧的用户的密码",default="")


class AccountCreate(BaseModel):
    username:str = Field(description="用户名")
    password:str = Field(description="密码")
    nickname:str = Field(description="昵称")
    is_admin:bool = Field(description="是否管理员")

class AccountUpdate(BaseModel):
    password:str = Field(description="密码,为空不修改密码",default="")
    nickname:str = Field(description="昵称")
    is_admin:bool = Field(description="是否管理员")


class AccountRecharge(BaseModel):
    cash:int = Field(description="充值的金额")
    extend:str = Field(description="充值的备注信息",default="")


class TokenCreate(BaseModel):
    extend:str = Field(description="备注信息",default="")


class ProxyHeader(BaseModel):
    proxy_token:str = Header(description="请求的token",default="",alias="x-proxy-token")

class RequestBody(BaseModel):
    url:str = Field(description="请求的url")
    method:str = Field(description="请求的方式",default="GET")
    body:str = Field(description="请求的内容",default="")
    params:str = Field(description="请求的GET参数",default="")
    header:dict = Field(description="请求的header",default={})
    user_agent:str = Field(description="请求的user_agent,不传且header中没有user_agent时默认",default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36")
    out_ip:str = Field(description="服务器的出口ip,不传随机",default="")
    allow_redirects:bool = Field(description="是否运行重定向,不传默认为True",default=True)

class RequestCloudScraperBody(BaseModel):
    url:str = Field(description="请求的url")
    method:str = Field(description="请求的方式",default="GET")
    body:str = Field(description="请求的内容",default="")
    params:str = Field(description="请求的GET参数",default="")
    header:dict = Field(description="请求的header,建议非必要不传",default={})
    content_type:str = Field(description="请求编码格式,附加到header")
    allow_redirects:bool = Field(description="是否运行重定向,不传默认为True",default=True)
