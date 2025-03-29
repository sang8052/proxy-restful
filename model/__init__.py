
from sqlmodel import select, Session, func
import math


class PageReponse:
    total: int
    page: int
    row: int
    data: list
    total_page: int

    def dict(self):
        return {
            "total":self.total,
            "page":self.page,
            "row":self.row,
            "data":self.data,
            "total_page":self.total_page
        }

def paginate_query(session:Session,query,page:int,row:int):
    response =  PageReponse()
    response.total =  session.exec(select(func.count()).select_from(query.subquery())).one()
    response.page = page
    data = session.exec(query.offset((page-1)*row).limit(row)).all()
    response.row = len(data)
    response.data =data
    response.total_page =  math.ceil(response.total / response.page)
    return response

from . import sys_user
from . import user_bill
from . import user_log
from . import user_token
