"""
应用配置模块
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置类"""
    
    # 应用基础配置
    APP_NAME: str = "股票交易纪律系统"
    APP_ENV: str = "development"
    DEBUG: bool = True
    
    # 数据库配置
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/stock_discipline.db"
    
    # Redis配置
    REDIS_URL: Optional[str] = None
    
    # Tushare Token
    TUSHARE_TOKEN: Optional[str] = None
    
    # 日志配置
    LOG_LEVEL: str = "DEBUG"
    
    # 选股配置
    MAX_STOCK_POOL_SIZE: int = 100
    DEFAULT_STOCK_COUNT: int = 20
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 全局配置实例
settings = Settings()
