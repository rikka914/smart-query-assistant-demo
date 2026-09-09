"""FASTAPI入口: 规划 -> 校验 -> 编译 -> 只读执行 -> 审计"""

from time import perf_counter
from fastapi import FastAPI,HTTPException
from sqlalchemy.exc import DBAPIError,SQLAlchemyError

from .audit import JsonlAuditWriter
from .compiler import compile_query
from .config import get_settings
from .database import QueryRespository, create_readonly_engine
from .models import QueryRequest,QueryResponse
from .planner import Build_Planner
from .validator import QueryPlanValidatorError,validate_and_normalize

setting = get_settings()
planner = Build_Planner(
    mode=setting.planner_mode,
    timezone=setting.app_timezone,
    ollama_base_url=setting.ollama_base_url,
    ollama_model=setting.ollama_model
)
repository = QueryRespository(create_readonly_engine(setting.database_url))
audit = JsonlAuditWriter(setting.audit_log_path)

app = FastAPI(
    title="智能查询助手 demo API",
    version="1.0.0",
    description="仅查询历史脱敏调度数据；不用于诊断或实时派车。"
)

@app.get("/health/live")
def live() -> dict[str,str]:
    return {"status": "ok"}

@app.get("/helath/ready")
def ready() -> dict[str,str]:
    try:
        if repository.ready():
            return{"status": "ready"}
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503,detail="数据库未就绪") from exc
    raise HTTPException(status_code=503,detail="数据库未就绪")

@app.get("/api/v1/example")
def examples() -> dict[str,list[str]]:
    return {
        "examples":[
            "查询最近7天各医院的派车数量",
            "找出最近30天海淀区派车超过5分钟的记录",
            "找10条与老人胸闷出冷汗意识模糊相似的警情",
            "统计最近30天各区的平均响应时间",
        ]
    }

@app.post(
    "/api/v1/query",
    response_model=QueryResponse
)
def query(request: QueryRequest) -> QueryResponse:
    started = perf_counter()
    plan_dict = None
    row_count = 0
    try:
        planned = planner.plan(request.question)
        plan = validate_and_normalize(planned.plan,setting.app_timezone)
        plan_dict = plan.model_dump(mode='json')
        compiled = compile_query(plan)
        columns,rows = repository.execute(compiled)
        row_count = len(rows)
        elapsed_ms = int((perf_counter() - started) * 1000)

        response = QueryResponse(
                question= request.question,
                planner= planned.source,
                planner_warning= planned.warning,
                query_plan= plan,
                sql_template= compiled.sql,
                columns= columns,
                rows= rows,
                row_count= row_count,
                elapsed_ms= elapsed_ms
            )
        
        audit.write(
            user_id= request.user_id,
            question= request.question,
            query_plan= plan_dict,
            return_rows= row_count,
            elapse_ms= elapsed_ms,
            succeeded=True,
        )
        return response

    except (
        QueryPlanValidatorError,
        ValueError,
        RuntimeError
    ) as exc:
        elapsed_ms = int((perf_counter() - started) * 1000)
        audit.write(
            user_id= request.user_id,
            question= request.question,
            query_plan= plan_dict,
            return_rows= 0,
            elapse_ms= elapsed_ms,
            succeeded= False,
            error_code="INVALID_QUERY_PLAN"
        )
        raise HTTPException(status_code=400,detail=str(exc)) from exc
    except DBAPIError as exc:
        elapsed_ms = int((perf_counter() - started) * 1000)
        audit.write(
            user_id= request.user_id,
            question= request.question,
            query_plan= plan_dict,
            return_rows= 0,
            elapse_ms= elapsed_ms,
            succeeded=False,
            error_code="DATABASE_QUERY_FAILED"
        )
        raise HTTPException(status_code=503,detail="查询数据库暂时不可用") from exc