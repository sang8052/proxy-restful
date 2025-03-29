import log 
from log import logging
import redis 
import config,model,json 

class xcache():

    pool:redis.ConnectionPool = None
    def __init__(self):
        self.connect_server()

    def connect_server(self):
        logging.info("连接Redis服务器[%s:%d],db:%d..." % (config.redis_hostname,config.redis_port,config.redis_index))
        self.pool = redis.ConnectionPool(host=config.redis_hostname,port=config.redis_port,db=config.redis_index,password=config.redis_password, decode_responses=True,max_connections=8)

    def get_client(self) -> redis.Redis:
        client = redis.Redis(connection_pool=self.pool)
        return client

    def get_version(self):
        client = self.get_client()
        info = client.info()
        return info["redis_version"]



    def query_token_info(self,token):
        client = self.get_client()
        if client.exists(config.cache_proxy_token_prefix + token):
            return json.loads(client.get(config.cache_proxy_token_prefix + token))
        else:
            info = model.user_token.query_token_info(token)
            if info:
                info_dict = dict(info)
                client.set(config.cache_proxy_token_prefix + token,json.dumps(info_dict))
                return info_dict
            return None 
    
    def query_user_session(self,session_id):
        client = self.get_client()
        if client.exists(config.cache_proxy_session_prefix + session_id):
            session_text = client.get(config.cache_proxy_session_prefix + session_id)
            return json.loads(session_text)
        else:
            return None 

    def update_user_session(self,session_id,ttl=600):
        client = self.get_client()
        if client.exists(config.cache_proxy_session_prefix + session_id):
            client.expire(config.cache_proxy_session_prefix + session_id,600)

    def delete_user_session(self,session_id):
        client = self.get_client()
        client.delete(config.cache_proxy_session_prefix + session_id)

    
            

    
    
        
