"""只读数据库访问层"""

from datetime import datetime,date
from decimal import Decimal
from typing import Any

from sqlalchemy import create_engine,text
from sqlalchemy.engine import Engine

from .compiler import CompilerQuery


def create_readonly_engine(database_url: str) -> Engine:
    """
    创建供查询助手的连接池

    参数:
        database_url:
            PostgreSQL连接地址,例如:
            postgresql+psycopg://demo_reader:密码@127.0.0.1:5432/dispatch_demo
    
    返回:
        SQLalchemy的Engine对象。
    """
    return create_engine(
        database_url,

        #每次从连接池取出旧连接前，先检查连接是否有效。
        pool_pre_ping=True,

        #连接池长期保留的数量。
        pool_size=5,

        #繁忙时允许增加的连接数。
        max_overflow=5,
        #每条数据库连接都设置5秒的查询超时。
        connect_args={
            "options": "-c statement_timeout=5000"
        }
    )

def _json_value(value: Any) -> Any:
    if isinstance(value,(date,datetime)):
        return value.isoformat()

    if isinstance(value,Decimal):
        return float(value)

    return value

class QueryRespository:
    """
    封装助手允许进行的数据库操作。
    """

    def __init__(self,engine: Engine) -> None:
        """引用外部创建的引擎"""
        self.engine = engine

    def ready(self) -> bool:
        """检查数据库连接是否正常。"""

        with self.engine.connect() as connection:
            result = connection.execute(
                text("SELECT 1")
                )

            value = result.scalar_one()

        return value == 1

    def execute(self,compiled:CompilerQuery) -> tuple[list[str],list[dict[str,Any]]]:
        # text() 识别 :name 占位符, params与SQL模板分别传给驱动
        with self.engine.connect() as connection:
            result = connection.execute(text(compiled.sql),compiled.params)
            columns = list(result.keys())
            rows = [
                {   
                    key: _json_value(value)
                    for key, value in row._mapping.items()
                }
                for row in result.fetchall()
            ]
            
        return columns,rows
