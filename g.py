
from sqlmodel import Session
from typing import Annotated
from fastapi import Depends
from contextlib import contextmanager

db_engine = None
db_mysql_version = ""

xcache:None

@contextmanager  
def get_session():
    with Session(db_engine) as session:
        yield session
        
SessionDep = Annotated[Session, Depends(get_session)]