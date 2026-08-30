"""
把QueryPlan编译为固定模板的参数化sql。
本模块故意不接受原始 SQL 字符串。所有列名、函数和排序方向都来自常量；
用户值只进入 params,交给 psycopg 绑定，从源头避免 SQL 注入。
"""

from dataclasses import dataclass
from typing import Any
from .models import QueryPlan

@dataclass(frozen=True)
class CompilerQuery:
    sql:str
    params: dict[str,Any]

View = "dispatch.v_dispatch_case_search"

def _where(plan: QueryPlan) -> tuple[str,dict[str,Any]]:
    filters = plan.filters
    clauses = ["alarm_time >= :start_time", "alarm_time < :end_time"]
    params: dict[str,Any] = {
        "start_time":filters.start_time,
        "end_time": filters.end_time
    }

    #绑定filters参数，左边SQL片段为代码常量，右边为filters参数
    optional = (
        ("district","district = :district",filters.district),
        ("hospital_name","hospital_name = :hospital_name",filters.hospital_name),
        ("event_type","event_type = :event_type",filters.event_type),
        ("dispatch_status","dispatch_status = :dispatch_status",filters.dispatch_status),
        ("min_dispatch_seconds","dispatch_seconds >= :min_dispatch_seconds",filters.min_dispatch_seconds)
    )
    for name,clause,value in optional:
        if value is not None:
            clauses.append(clause)
            params[name] = value
        

    return " AND ".join(clauses),params
