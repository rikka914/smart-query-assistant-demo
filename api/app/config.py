"""
项目配置模块，
作用是校验.env中配置的数据类型，
并向其他模块提供统一的settings对象。

"""
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

#先获取.env文件的绝对路径
#__file__表示当前文件也就是config.py的绝对路径。
#resolve()作用是将__file__转换为绝对路径
config_file_path = Path(__file__).resolve()

#parent作用是读取config_file_path的父路径
app_dir = config_file_path.parent
api_dir = app_dir.parent
project_dir = api_dir.parent

#拼接得到项目根目录下的.env文件
env_path = project_dir / ".env"

class Settings(BaseSettings):
   """
   查询助手的运行配置。

   BaseSettings会自动从.env文件中读取同名字段。
   字段db_host对应DB_HOST
   """ 

   db_host : str = Field(default="127.0.0.1")
   db_port : int = Field(default=5432, gt=0, le=65535)
   db_name : str = Field(default='dispatch_demo')
   db_user : str = Field(default='demo_reader')
   db_password : str = Field(min_length=1)
   db_pool_size : int = Field(default=5)
   db_max_overflow: int = Field(default=5)
   db_pool_timeout : int = Field(default=30)
    # 是否在控制台打印SQL语句
    # 开发阶段可以设为 true，生产环境通常设为 false
   db_echo : bool = Field(default=False)

   model_config = SettingsConfigDict(
        env_file = env_path,
        #环境变量不区分大小写
        case_sensitive=False,
        env_file_encoding="utf-8",
        extra="ignore",
   )

settings = Settings()