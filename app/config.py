"""
应用配置管理
支持从环境变量和配置文件读取配置
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置类"""

    # 数据库配置
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "essay_scoring"
    DB_CHARSET: str = "utf8mb4"

    # OpenAI配置
    OPENAI_BASE_URL: str = "https://api.chatanywhere.tech/v1"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4"

    # 应用配置
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    APP_DEBUG: bool = True
    APP_PAGE_SIZE: int = 20
    APP_SESSION_TIMEOUT: int = 3600

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"

    @property
    def DATABASE_URL(self) -> str:
        """构建数据库连接URL"""
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset={self.DB_CHARSET}"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """获取配置实例(单例模式)"""
    return Settings()


# 导出配置实例
settings = get_settings()
