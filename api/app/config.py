"""
集中读取环境变量，避免凭据散落在业务代码中

"""
from functools import lru_cache
from pydantic_settings import BaseSettings,SettingsConfigDict

#

class Settings(BaseSettings):
    database_url : str = ""
    planner_mode : str = "rule"
    ollama_base_url : str = "http://127..0.1:11434"
    ollama_model : str = "qwen2.5:3b"
    audit_log_path: str = "/app/logs/query_audit.jsonl"
    app_timezone: str = "Asia/Shanghai"

    model_config = SettingsConfigDict(
        env_file = ".env",
        extra = "ignore"
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()