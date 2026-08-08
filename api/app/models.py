"""
API和查询流水线的数据模型
QueryPlan 是安全边界：无论计划来自规则还是大模型，后续只能看到这些固定字段，不能携带任意 SQL、表名、函数名或排序表达式。
"""
from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, Field, model_validator

Intent = Literal["detail_search", "aggregate", "similar_case_search"]
GroupField = Literal["hospital_name", "district", "event_type", "day"]
Metric = Literal["count", "avg_dispatch_seconds", "avg_response_seconds"]

class QueryFilters(BaseModel):
    """允许下推到数据库的过滤名单"""
    start_time : datetime | None = None
    end_time : datetime | None = None
    district : str | None = Field(default=None, max_length=32)
    hospital_name : str | None = Field(default=None, max_length=128)
    event_type : str | None = Field(default=None, max_length=32)
    dispatch_status : str | None = Field(default=None, max_length=16)
    min_dispatch_seconds : int | None = Field(default=None, ge=0, le=86400)

class QueryPlan(BaseModel):
    """大模型/规则解析器的唯一合法输出"""
    intent:  Intent
    filters: QueryFilters = Field(default_factory=QueryFilters)
    group_by: list[GroupField] = Field(default_factory=list,max_length=2)
    metric: Metric | None = None
    semantic_query: str | None = Field(default=None, max_length=300) 
    limit : int = Field(default=20,ge=1,le=100)

    @model_validator(mode="after")
    def check_intent_fields(self) -> "QueryPlan":
        if self.intent == "aggregate" and not self.metric:
            raise ValueError("(aggregate)统计查询必须指定指标(metric).")
        if self. intent == "similar_case_search" and not self.semantic_query:
            raise ValueError("相似查询必须提供semantic_query.")
        return self

class QueryRequest(BaseModel):
    question : str = Field(min_length=2,max_length=500)
    user_id : str = Field(default="demo_user", min_length=1,max_length=64)


class QueryResponse(BaseModel):
    question: str
    planner : str
    planner_warning : str | None = None 
    query_plan : QueryPlan
    sql_template : str
    columns : list[str]
    rows : list[dict[str,Any]]
    row_count: int
    elapsed_ms : int