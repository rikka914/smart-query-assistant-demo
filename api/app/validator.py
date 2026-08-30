"""对QueryPlan做与模型无关的最终安全规范化"""

from datetime import datetime,timedelta
from .models import QueryPlan
from zoneinfo import ZoneInfo

class QueryPlanValidatorError(ValueError):
    pass

def validate_and_normalize(plan: QueryPlan, timezone: str ) -> QueryPlan:
    """补默认时间,限制时间跨度,修复Planner输出的QueryPlan中出现的错误,修复不了的错误直接报错拒绝"""
    normalized = plan.model_copy(deep=True)
    target_timezone = ZoneInfo(timezone)
    now = datetime.now(target_timezone)

    normalized.filters.start_time = normalized.filters.start_time or now-timedelta(days=30)
    normalized.filters.end_time = normalized.filters.end_time or now

    #统一QueryPlan里的时区，避免因时区混乱导致的比较异常。
    if normalized.filters.start_time.tzinfo is None:
        normalized.filters.start_time = (
            normalized.filters.start_time.replace(tzinfo=target_timezone)
        )

    if normalized.filters.end_time.tzinfo is None:
        normalized.filters.end_time = (
            normalized.filters.end_time.replace(tzinfo=target_timezone)
        )

    start = normalized.filters.start_time
    end = normalized.filters.end_time

    if end <= start :
        raise QueryPlanValidatorError("结束时间必须晚于开始时间")

    if end - start > timedelta(days=366):
        raise QueryPlanValidatorError("时间跨度不能超过366天")

    #限制limit数值在100以内
    normalized.limit = max(1,min(normalized.limit,100))

    #判断相似查询中的描述是否符合要求
    if normalized.intent == "similar_case_search":
        normalized.semantic_query = (normalized.semantic_query or "").strip()

        if len(normalized.semantic_query) < 2:
            raise QueryPlanValidatorError("相似查询的描述至少需要2个字符")

    return normalized