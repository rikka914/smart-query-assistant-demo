"""只读数据库访问层"""

from sqlalchemy import create_engine,text
from sqlalchemy.engine import Engine

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