import os
import typing
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 环境设置
    APP_ENV: str = os.getenv("APP_ENV", "development")
    
    VERSION: str = "0.1.0"
    APP_TITLE: str = "Vue FastAPI Admin"
    PROJECT_NAME: str = "Vue FastAPI Admin"
    APP_DESCRIPTION: str = "Description"

    CORS_ORIGINS: typing.List = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: typing.List = ["*"]
    CORS_ALLOW_HEADERS: typing.List = ["*"]

    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"

    PROJECT_ROOT: str = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    BASE_DIR: str = os.path.abspath(os.path.join(PROJECT_ROOT, os.pardir))
    LOGS_ROOT: str = os.path.join(BASE_DIR, "app/logs")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "3488a63e1765035d386f05409663f55c83bfae3b3c61a932744b20ad14244dcf")  # openssl rand -hex 32
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24 * 7))  # 7 day
    
    # 安全相关配置
    # IP白名单，为空列表则不启用白名单检查
    IP_WHITELIST: List[str] = os.getenv("IP_WHITELIST", "").split(",") if os.getenv("IP_WHITELIST") else []
    
    # 请求频率限制配置
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"  # 是否启用请求频率限制
    RATE_LIMIT_MAX_REQUESTS: int = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", 60))  # 时间窗口内最大请求数
    RATE_LIMIT_WINDOW_SECONDS: int = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", 60))  # 时间窗口大小（秒）
    
    # JWT令牌相关设置
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", 30))  # 刷新令牌过期时间（天）
    JWT_AUDIENCE: str = os.getenv("JWT_AUDIENCE", "vue-fastapi-admin")  # 令牌受众
    JWT_ISSUER: str = os.getenv("JWT_ISSUER", "vue-fastapi-admin")  # 令牌签发者
    
    # 密码策略配置
    PASSWORD_MIN_LENGTH: int = int(os.getenv("PASSWORD_MIN_LENGTH", 8))  # 密码最小长度
    PASSWORD_REQUIRE_UPPERCASE: bool = os.getenv("PASSWORD_REQUIRE_UPPERCASE", "true").lower() == "true"  # 是否要求包含大写字母
    PASSWORD_REQUIRE_LOWERCASE: bool = os.getenv("PASSWORD_REQUIRE_LOWERCASE", "true").lower() == "true"  # 是否要求包含小写字母
    PASSWORD_REQUIRE_DIGITS: bool = os.getenv("PASSWORD_REQUIRE_DIGITS", "true").lower() == "true"  # 是否要求包含数字
    PASSWORD_REQUIRE_SPECIAL: bool = os.getenv("PASSWORD_REQUIRE_SPECIAL", "true").lower() == "true"  # 是否要求包含特殊字符
    
    # 阿里云OSS配置
    OSS_ACCESS_KEY_ID: str = os.getenv("OSS_ACCESS_KEY_ID", "your_access_key_id")
    OSS_ACCESS_KEY_SECRET: str = os.getenv("OSS_ACCESS_KEY_SECRET", "your_access_key_secret")
    OSS_BUCKET_NAME: str = os.getenv("OSS_BUCKET_NAME", "your_bucket_name")
    OSS_ENDPOINT: str = os.getenv("OSS_ENDPOINT", "oss-cn-hangzhou.aliyuncs.com")  # 例如：oss-cn-hangzhou.aliyuncs.com
    OSS_BUCKET_DOMAIN: str = os.getenv("OSS_BUCKET_DOMAIN", "")  # 自定义域名，如果有的话
    OSS_UPLOAD_DIR: str = os.getenv("OSS_UPLOAD_DIR", "uploads")  # 上传目录
    OSS_URL_EXPIRE_SECONDS: int = int(os.getenv("OSS_URL_EXPIRE_SECONDS", 60 * 60 * 24))  # 签名URL过期时间（秒）
    
    # 数据库配置
    DB_CONNECTION: str = os.getenv("DB_CONNECTION", "sqlite")
    DB_FILE: str = os.getenv("DB_FILE", "db.sqlite3")  # SQLite数据库文件名
    
    @property
    def TORTOISE_ORM(self) -> dict:
        """根据环境动态配置数据库连接"""
        db_config = {
            "connections": {
                # SQLite configuration
                "sqlite": {
                    "engine": "tortoise.backends.sqlite",
                    "credentials": {"file_path": f"{self.BASE_DIR}/{self.DB_FILE}"},  # Path to SQLite database file
                },
            },
            "apps": {
                "models": {
                    "models": ["app.models", "aerich.models"],
                    "default_connection": self.DB_CONNECTION,
                },
            },
            "use_tz": False,  # Whether to use timezone-aware datetimes
            "timezone": "Asia/Shanghai",  # Timezone setting
        }
        
        # 根据环境添加不同的数据库配置
        if self.DB_CONNECTION == "mysql":
            db_config["connections"]["mysql"] = {
                "engine": "tortoise.backends.mysql",
                "credentials": {
                    "host": os.getenv("DB_HOST", "localhost"),
                    "port": int(os.getenv("DB_PORT", 3306)),
                    "user": os.getenv("DB_USERNAME", "root"),
                    "password": os.getenv("DB_PASSWORD", ""),
                    "database": os.getenv("DB_DATABASE", "fastapi_admin"),
                },
            }
        elif self.DB_CONNECTION == "postgres":
            db_config["connections"]["postgres"] = {
                "engine": "tortoise.backends.asyncpg",
                "credentials": {
                    "host": os.getenv("DB_HOST", "localhost"),
                    "port": int(os.getenv("DB_PORT", 5432)),
                    "user": os.getenv("DB_USERNAME", "postgres"),
                    "password": os.getenv("DB_PASSWORD", ""),
                    "database": os.getenv("DB_DATABASE", "fastapi_admin"),
                },
            }
            
        return db_config
    
    DATETIME_FORMAT: str = "%Y-%m-%d %H:%M:%S"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()

# 输出当前环境信息
print(f"当前运行环境: {settings.APP_ENV}")
print(f"调试模式: {settings.DEBUG}")
print(f"数据库连接: {settings.DB_CONNECTION}")
if settings.DB_CONNECTION == "sqlite":
    print(f"SQLite数据库文件: {settings.DB_FILE}")
