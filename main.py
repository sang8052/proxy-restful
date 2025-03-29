import os, log, signal, time 
import sqlmodel, sys, config, utils, uvicorn
from log import logging
from sqlmodel import create_engine, SQLModel,text
from sqlalchemy.pool import QueuePool
from typing import  cast
import traceback 
import g,xcache
import api,model


def signal_handler(signal, handle):
    if signal == 2:
        logging.error("收到程序终止信号")
        pid = os.getpid()
        logging.warning("关闭进程[pid:" + str(pid) + "]")
        utils.kill_pid(pid)

if __name__ == "__main__":
    
    signal.signal(signal.SIGINT, signal_handler)

   
    logging.info("连接MYSQL数据库{ host:%s, port:%d, database: %s}" % (config.db_hostname,config.db_port,config.db_database))
    database_url = "mysql+pymysql://%s:%s@%s:%d/%s?charset=utf8mb4" % (config.db_username,config.db_password,config.db_hostname,config.db_port,config.db_database)
    g.db_engine = create_engine(database_url,pool_recycle=3600, pool_pre_ping=True,pool_size=8,poolclass=QueuePool,echo=False)
    try:
        g.db_engine.connect()
    except Exception as err:
        logging.error("数据库连接失败,请检查配置参数!ERROR:" + traceback.format_exc())
        sys.exit(0)

    SQLModel.metadata.create_all(g.db_engine)

    # 获得MYSQL 的版本号
    with g.get_session() as session:
        result = session.exec(text("SELECT VERSION()"))
        config.db_mysql_version = result.scalar()
        logging.info("数据库连接成功,版本:" + config.db_mysql_version)



    g.xcache = xcache.xcache()
    logging.info("Redis 连接成功,版本:" + g.xcache.get_version())
    
    if not model.sys_user.query_exist_admin_user():
        default_password = utils.generate_password(12)
        model.sys_user.create_user("admin",default_password,"超级管理员",True)
        logging.info("新建管理员账号[admin]成功,密码:" + default_password)
        utils.write_file_text("./admin_default_password",default_password)
        logging.warning("管理员账号密码已经保存到: %s ,为了您的数据安全,请尽快修改密码" % (os.path.abspath("./admin_default_password")))

    logging.info("启动 FASTAPI,提供Web 服务...")
    uvicorn.run("api:app",port=config.fastapi_http_port,reload=False,host="0.0.0.0",headers=[("server", config.system_name + " " + config.system_version)])
    



    
    

   