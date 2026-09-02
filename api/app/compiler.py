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


def compile_query(plan: QueryPlan) -> CompilerQuery:
    where_sql, params = _where(plan)
    params["limit"] = plan.limit

    if plan.intent == 'aggregate':
        group_expr = {
            "district":("district", "district"),
            "hospital_name":("hospital_name", "hospital_name"),
            "event_type":("event_type", "event_type"),
            "day":("day_trunc('day',alarm_time)::date AS day",
                   "day_trunc('day',alarm_time)::date"
                )
        }

        metric_expr = {
            "count":"count(*)::integer AS case_count",
            "avg_dispatch_seconds":"round(avg(avg_dispatch_seconds))::integer AS avg_dispatch_seconds",
            "avg_response_seconds":"round(avg(avg_response_seconds))::integer AS avg_response_seconds",
        }

        selected = [group_expr[item][0] for item in plan.group_by]
        selected.append(metric_expr[plan.metric])

        group_clause = ""

        if plan.group_by:
            group_clause = " GROUP BY " + ", ".join(group_expr[item][1] for item in plan.group_by)

        sql = (
            f"SELECT {', '.join(selected)} FROM {View} WHERE {where_sql}"
            f"{group_clause} ORDER BY 1 LIMIT :limit"
        )

        return CompilerQuery(sql,params)

    detail_columns = (
        "case_id, alarm_time, district, address_masked, event_type,"
        "chief_complaint, case_summary, hospital_name, ambulance_code_masked,"
        "dispatch_status, dispatch_seconds, response_seconds"
    )

    if plan.intent == 'similar_case_search':
        params["semantic_query"] = plan.semantic_query

        score = (
            "round(greatest(similarity(case_summary, :semantic_query),"
            "similarity(chief_ccomplaint, :semantic_query)"
            ")::numeric,3)"
        )

        sql = (
            f"SELECT {detail_columns}, "
            f"{score} AS similarity "
            f"FROM {View} "
            f"WHERE {where_sql} "
            f"ORDER BY similarity DESC, "
            f"alarm_time DESC "
            f"LIMIT :limit"
        )

        return CompilerQuery(sql,params)

    sql = (
        f"SELECT {detail_columns}, "
        f"FROM {View} "
        f"WHERE {where_sql} "
        f"ORDER BY alarm_time DESC "
        f"LIMIT :limit"
    )
    return CompilerQuery(sql,params)
