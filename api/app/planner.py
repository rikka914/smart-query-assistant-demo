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
    today = now.replace(hour=0,minute=0,second=0,microsecond=0)
    if "昨天" in question:
        yestoday = today - timedelta(days=1)
        return yestoday, today

    if '今天' in question:
        return today,now

    match = re.match(r"(?:最近|近)\s*(\d{1,3})\s*天",question)

    if match:
        time = now - timedelta(days=min(int(match.group(1)),366))
        return time, now