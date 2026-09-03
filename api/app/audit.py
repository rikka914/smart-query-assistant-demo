"""与业务数据库分离的jsonl审计日志"""

import json
import os
import threading
from datetime import datetime,timezone
from typing import Any

class JsonlAuditWriter:
    def __init__(self, path: str ) -> None:
        self.path = path
        self._lock = threading.Lock()
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

    def write(
            self,
            *,
            user_id: str,
            question: str,
            query_plan: dict[str,Any]|None,
            return_rows: int,
            elapse_ms: int,
            succeeded: bool,
            error_code: str | None = None,
    ) -> None:

        record = {
            "queried_at": datetime.now(timezone.utc).isoformat(),
            "user_id": user_id,
            "question": question,
            "query_plan": query_plan,
            "return_rows": return_rows,
            "elapse_ms": elapse_ms,
            "succeeded": succeeded,
            "error_code": error_code
        }

        line =( 
            json.dumps(
                record,
                ensure_ascii=False,
                default=str
            )
            + "\n"
        )

        with self._lock, open(
            self.path,
            "a",
            encoding="utf-8"
        )as handle:
            handle.write(line)