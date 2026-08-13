"""
planner将自然语言转换成queryplan,

默认规则解析器用于离线使用和验收。ollama解析器用于更自由的表述。
二者都只生成queryplan,不生成sql。
"""
from __future__ import annotations
import re
import urllib.request
import urllib.error
import json
from dataclasses import dataclass
from models import QueryPlan,QueryFilters
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

DISTRICTS = ("金平区","龙湖区","潮阳区","澄海区","濠江区")
EVENT_TYPES = ("外伤","急病","交通事故","其他")
HOSPITALS = ("市中心医院","市人民医院","附一医院","附二医院")

@dataclass(frozen=True)
class PlannerResult:
    plan : QueryPlan
    source: str
    warning: str | None = None

def time_range(question : str,now: datetime) -> tuple[datetime, datetime]:
    """
    识别少量高频中文时间表达，没有时间强制最近三十天。
    """
    #先赋予now变量时区，默认为上海时区。
    now = datetime.now(ZoneInfo("Asia/Shanghai"))

    today = now.replace(hour=0,minute=0,second=0,microsecond=0)
    if "昨天" in question:
        yestoday = today - timedelta(days=1)
        return yestoday, today

    if '今天' in question:
        return today,now

    match = re.search(r"(?:最近|近)\s*(\d{1,3})\s*天",question)

    if match:
        time = now - timedelta(days=min(int(match.group(1)),366))
        return time, now

    if '最近7天' in question:
        time = now - timedelta(days=7)
        return time,now

    if '最近一个月' in question or '近一个月' in question or '最近30天' in question:
        time = now - timedelta(days=30)
        return time,now

    if '最近一年' in question or '近一年' in question:
        time = now - timedelta(days=365)
        return time,now

    year_match = re.search(r"(20/d{2})年",question)
    if year_match:
        year = int(year_match.group(1))
        tz = now.tzinfo
        return datetime(year,1,1,tzinfo=tz), datetime(year+1,1,1,tzinfo=tz)

    #默认没提及时间强制30天
    time = now - timedelta(days=30)
    return time,now

def semantic_text(question:str):
    """
    尽量去除问题中的动作词,减少相似度的影响
    """
    text = re.sub(r"^(请)?(?:帮我)?(?:查询|查|找出|找)","",question).strip()
    text = re.sub(r"^\d{1,3}条(?:与)?","",text).strip()
    text = re.sub(r"(?:相似|类似)的?(?:警情|情况|事件|记录","",text).strip()
    return text or question

class RuleBasedPlanner:
    """
    可预测的最小中文解析器,离线可使用，默认为该解析器。
    """
    def __init__(self, timezone: str = "Asia/Shanghai"):
        self.timezone = ZoneInfo(timezone)

    def plan(self, question: str):
        now = datetime.now(self.timezone)
        start_time,end_time = time_range(question,now)

        filter = QueryFilters(start_time=start_time, end_time=end_time)
        filter.district = next((item for item in DISTRICTS if item in question),None )
        filter.event_type = next((item for item in EVENT_TYPES if item in question),None)

        if '各医院' or '各个医院' not in question:
            filter.hospital_name = next((item for item in HOSPITALS if item in question),None)

        delay_match = re.search(
            r"派车.{0,8}?(?:超过|大于)\s*(\d{1,4})\s*(分钟|秒)",question
        )
        if delay_match:
            value = int(delay_match.group(1))
            filter.min_dispatch_seconds = value * 60 if delay_match.group(2) == "分钟" else value

        limit_match = re.search(
            r"(\d{1,3})\s*条",question
        )
        limit = min(int(limit_match.group(1)),100) if limit_match else 20

        if "相似" in question or "类似" in question:
            return PlannerResult(
                QueryPlan(
                    intent="similar_case_search",
                    filters= filter,
                    semantic_query=semantic_text(question),
                    limit=limit,
                ),
                source="rule",
            )

        group_by = []
        if "各医院" in question or "按医院" in question:
            group_by.append("hospital_name")
        if "各区" in question or "各个区域" in question or "按区" in question:
            group_by.append("district")
        if "各类型" in question or "按警情类型" in question:
            group_by.append("even_type")
        if "每天" in question or "按天" in question:
            group_by.append("day")

        average = "平均" in question
        is_arggregate = bool(group_by) or average or "统计" in question
        if is_arggregate:
            if average and ("响应" in question or "到达" in question):
                metric = "avg_response_seconds"
            elif average and "派车" in question:
                metric = "avg_dispatch_seconds"
            else:
                metric = "count"

            return PlannerResult(
                QueryPlan(
                    intent="aggregate",
                    filters=filter,
                    group_by=group_by[:2],
                    metric=metric,
                    limit=limit,
                ),
                source="rule",
            )
    
        return PlannerResult(
            QueryPlan(
                intent="detail_search",
                filters=filter,
                limit=limit,
            ),
            source="rule",
        )


class OllamaPlanner:
    """
    调用Ollama的json模式; 返回值仍由pydantic严格验证。
    """
    SYSTEM_PROMPT = """
    你是急救调度历史数据的查询计划生成器。只输出 JSON,不输出 SQL。
    输出的内容严格按照以下内容：
    - 允许的 intent: detail_search, aggregate, similar_case_search。
    - filters 只允许 start_time, end_time, district, hospital_name, event_type, dispatch_status, min_dispatch_seconds。group_by 只允许 hospital_name, district, event_type, day。
    - metric 只允许 count, avg_dispatch_seconds,
    - avg_response_seconds。limit 范围 1-100。时间输出带时区的 ISO 8601。
    - 相似查询把核心症状写入 semantic_query。没有明确时间时使用最近30天。
    """
    def __int__(self, base_url: str, model: str, timeout: int = 20 ):
        self.url = base_url.rstrip("/") + "/api/generate"
        self.model = model
        self.timeout = timeout

    def plan(self, question: str) -> PlannerResult:
        payload = json.dumps(
            {
                "model": self.model,
                "system": self.SYSTEM_PROMPT,
                "prompt": question,
                "format": "json",
                "stream": False,
                "options": {"temperature": 0},
            }
        ).encode("utf-8")
        