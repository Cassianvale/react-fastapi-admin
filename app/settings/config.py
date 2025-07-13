import os
from pathlib import Path
from typing import List, Optional

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


def get_root_path() -> Path:
    """获取项目根路径"""
    return Path(__file__).parent.parent.parent.resolve()


def ensure_path(path: str) -> Path:
    """pathlib.Path 自动跨平台处理"""
    root = get_root_path()
    full_path = root / path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    return full_path


class Settings(BaseSettings):
    """应用程序配置设置"""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore")

    # 基础应用配置
    APP_ENV: str = Field(default="development", description="应用环境")
    VERSION: str = Field(default="0.1.0", description="应用版本")
    APP_TITLE: str = Field(default="Vue FastAPI Admin", description="应用标题")
    PROJECT_NAME: str = Field(default="Vue FastAPI Admin", description="项目名称")
    APP_DESCRIPTION: str = Field(default="Vue FastAPI Admin Description", description="应用描述")
    DEBUG: bool = Field(default=True, description="调试模式")

    # CORS 配置
    CORS_ORIGINS: List[str] = Field(default=["*"], description="CORS 允许的来源")
    CORS_ALLOW_CREDENTIALS: bool = Field(default=True, description="CORS 允许凭证")
    CORS_ALLOW_METHODS: List[str] = Field(default=["*"], description="CORS 允许的方法")
    CORS_ALLOW_HEADERS: List[str] = Field(default=["*"], description="CORS 允许的头部")

    # 路径配置
    BASE_DIR: Path = Field(default_factory=get_root_path, description="项目根目录")
    LOGS_ROOT: str = Field(default="app/logs", description="日志目录")

    # 日志配置
    LOG_RETENTION_DAYS: int = Field(default=7, description="日志保留天数")
    LOG_ROTATION: str = Field(default="1 day", description="日志轮转周期")
    LOG_MAX_FILE_SIZE: str = Field(default="10 MB", description="单个日志文件最大大小")
    LOG_ENABLE_ACCESS_LOG: bool = Field(default=True, description="是否启用访问日志")

    # 安全配置
    SECRET_KEY: str = Field(
        default="3488a63e1765035d386f05409663f55c83bfae3b3c61a932744b20ad14244dcf", description="应用密钥"
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT 算法")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60 * 24 * 7, description="JWT 访问令牌过期时间（分钟）")
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=30, description="JWT 刷新令牌过期时间（天）")
    JWT_AUDIENCE: str = Field(default="vue-fastapi-admin", description="JWT 受众")
    JWT_ISSUER: str = Field(default="vue-fastapi-admin", description="JWT 签发者")

    # IP 白名单配置
    IP_WHITELIST_STR: str = Field(default="", description="IP 白名单字符串")

    # 请求频率限制
    RATE_LIMIT_ENABLED: bool = Field(default=True, description="是否启用请求频率限制")
    RATE_LIMIT_MAX_REQUESTS: int = Field(default=60, description="时间窗口内最大请求数")
    RATE_LIMIT_WINDOW_SECONDS: int = Field(default=60, description="时间窗口大小（秒）")

    # 密码策略配置
    PASSWORD_MIN_LENGTH: int = Field(default=8, description="密码最小长度")
    PASSWORD_REQUIRE_UPPERCASE: bool = Field(default=True, description="是否要求包含大写字母")
    PASSWORD_REQUIRE_LOWERCASE: bool = Field(default=True, description="是否要求包含小写字母")
    PASSWORD_REQUIRE_DIGITS: bool = Field(default=True, description="是否要求包含数字")
    PASSWORD_REQUIRE_SPECIAL: bool = Field(default=True, description="是否要求包含特殊字符")

    # 阿里云 OSS 配置
    OSS_ENABLED: bool = Field(default=True, description="是否启用 OSS 存储")
    OSS_ACCESS_KEY_ID: str = Field(default="your_access_key_id", description="OSS 访问密钥 ID")
    OSS_ACCESS_KEY_SECRET: str = Field(default="your_access_key_secret", description="OSS 访问密钥")
    OSS_BUCKET_NAME: str = Field(default="your_bucket_name", description="OSS 存储桶名称")
    OSS_ENDPOINT: str = Field(default="oss-cn-hangzhou.aliyuncs.com", description="OSS 端点")
    OSS_BUCKET_DOMAIN: str = Field(default="", description="OSS 自定义域名")
    OSS_UPLOAD_DIR: str = Field(default="uploads", description="OSS 上传目录")
    OSS_URL_EXPIRE_SECONDS: int = Field(default=60 * 60 * 24, description="OSS 签名 URL 过期时间（秒）")

    # 本地存储配置
    LOCAL_STORAGE_URL_PREFIX: str = Field(default="/static/uploads", description="本地存储 URL 前缀")
    LOCAL_STORAGE_FULL_URL: str = Field(default="", description="本地存储完整 URL")

    # 数据库配置
    DB_CONNECTION: str = Field(default="sqlite", description="数据库连接类型")
    DB_FILE: str = Field(default="db.sqlite3", description="SQLite 数据库文件名")

    # MySQL/PostgreSQL 配置
    DB_HOST: str = Field(default="localhost", description="数据库主机")
    DB_PORT: int = Field(default=3306, description="数据库端口")
    DB_USERNAME: str = Field(default="root", description="数据库用户名")
    DB_PASSWORD: str = Field(default="", description="数据库密码")
    DB_DATABASE: str = Field(default="fastapi_admin", description="数据库名称")

    # 时间格式配置
    DATETIME_FORMAT: str = Field(default="%Y-%m-%d %H:%M:%S", description="日期时间格式")

    @computed_field
    @property
    def logs_path(self) -> Path:
        """获取日志文件夹路径"""
        return ensure_path(self.LOGS_ROOT)

    @computed_field
    @property
    def local_storage_path(self) -> Path:
        """获取本地存储路径"""
        return ensure_path("storage/uploads")

    @computed_field
    @property
    def ip_whitelist(self) -> List[str]:
        """获取 IP 白名单列表"""
        if not self.IP_WHITELIST_STR:
            return []
        return [ip.strip() for ip in self.IP_WHITELIST_STR.split(",") if ip.strip()]

    @computed_field
    @property
    def is_production(self) -> bool:
        """判断是否为生产环境"""
        return self.APP_ENV.lower() == "production"

    @computed_field
    @property
    def is_development(self) -> bool:
        """判断是否为开发环境"""
        return self.APP_ENV.lower() == "development"

    @computed_field
    @property
    def tortoise_orm(self) -> dict:
        """动态生成 Tortoise ORM 配置"""
        base_config = {
            "connections": {
                "sqlite": {
                    "engine": "tortoise.backends.sqlite",
                    "credentials": {"file_path": str(self.BASE_DIR / self.DB_FILE)},
                },
            },
            "apps": {
                "models": {
                    "models": ["app.models", "aerich.models"],
                    "default_connection": self.DB_CONNECTION,
                },
            },
            "use_tz": False,
            "timezone": "Asia/Shanghai",
        }

        # 根据连接类型添加相应的数据库配置
        if self.DB_CONNECTION == "mysql":
            base_config["connections"]["mysql"] = {
                "engine": "tortoise.backends.mysql",
                "credentials": {
                    "host": self.DB_HOST,
                    "port": self.DB_PORT,
                    "user": self.DB_USERNAME,
                    "password": self.DB_PASSWORD,
                    "database": self.DB_DATABASE,
                },
            }
        elif self.DB_CONNECTION == "postgres":
            base_config["connections"]["postgres"] = {
                "engine": "tortoise.backends.asyncpg",
                "credentials": {
                    "host": self.DB_HOST,
                    "port": self.DB_PORT,
                    "user": self.DB_USERNAME,
                    "password": self.DB_PASSWORD,
                    "database": self.DB_DATABASE,
                },
            }

        return base_config

    def model_post_init(self, __context) -> None:
        """模型初始化后的处理"""
        # 确保必要的目录存在
        self.logs_path.mkdir(parents=True, exist_ok=True)
        self.local_storage_path.mkdir(parents=True, exist_ok=True)

    def get_database_url(self) -> str:
        """获取数据库连接 URL"""
        if self.DB_CONNECTION == "sqlite":
            return f"sqlite:///{self.BASE_DIR / self.DB_FILE}"
        elif self.DB_CONNECTION == "mysql":
            return f"mysql://{self.DB_USERNAME}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_DATABASE}"
        elif self.DB_CONNECTION == "postgres":
            return (
                f"postgresql://{self.DB_USERNAME}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_DATABASE}"
            )
        else:
            raise ValueError(f"不支持的数据库类型: {self.DB_CONNECTION}")

    def __repr__(self) -> str:
        return f"<Settings env={self.APP_ENV} debug={self.DEBUG} db={self.DB_CONNECTION}>"


# 创建全局设置实例
settings = Settings()


# 输出当前环境信息
def print_startup_info():
    """打印启动信息"""
    print(f"🚀 当前运行环境: {settings.APP_ENV}")
    print(f"🔧 调试模式: {settings.DEBUG}")
    print(f"💾 数据库连接: {settings.DB_CONNECTION}")
    if settings.DB_CONNECTION == "sqlite":
        print(f"📁 SQLite 数据库文件: {settings.DB_FILE}")
    print(f"📂 项目根路径: {settings.BASE_DIR}")
    print(f"📋 日志路径: {settings.logs_path}")
    print(f"💾 本地存储路径: {settings.local_storage_path}")
    if settings.ip_whitelist:
        print(f"🛡️  IP 白名单: {settings.ip_whitelist}")
    print("=" * 50)


# 在模块导入时打印启动信息
if __name__ == "__main__":
    print_startup_info()
