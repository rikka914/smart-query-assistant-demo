from sqlalchemy import text
from config import get_settings
from database import QueryRespository,create_readonly_engine

settings = get_settings()

engine = create_readonly_engine(
    database_url= settings.database_url
)

respository = QueryRespository(engine=engine)

#检查数据库是否健康
print(f"数据库健康检查: {respository.ready()}")

with engine.connect() as connection:
    current_user = connection.execute(
        text("SELECT current_user")
    ).scalar_one()

    read_only  = connection.execute(
        text("SHOW transaction_read_only")
    ).scalar_one()

    time_out = connection.execute(
        text("SHOW statement_timeout")
    ).scalar_one()

    case_count = connection.execute(
        text(
            "SELECT count(*)"
            "FROM dispatch.v_dispatch_case_search"
        )

    ).scalar_one()

print("当前数据库账号：", current_user)
print("事务是否只读：", read_only)
print("查询超时时间：", time_out)
print("脱敏视图记录数：", case_count)
    
engine.dispose()
