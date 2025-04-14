from contextlib import asynccontextmanager
import asyncio
import os

from fastapi import FastAPI
from fastapi.responses import JSONResponse, RedirectResponse
from tortoise import Tortoise
from dotenv import load_dotenv

from app.core.exceptions import SettingNotFound
from app.core.init_app import (
    init_data,
    make_middlewares,
    register_exceptions,
    register_routers,
)
from app.log import logger
from app.core.config import setup_json_encoder  # 导入JSON编码器设置函数
from app.core.dependency import AuthControl  # 导入身份验证控制器

# 加载环境变量
def load_environment():
    """根据环境加载不同的.env文件"""
    # 首先加载默认的.env文件
    load_dotenv()
    
    # 获取当前环境
    app_env = os.getenv("APP_ENV", "development")
    logger.info(f"当前运行环境: {app_env}")
    
    # 根据环境加载对应的环境配置文件
    env_file = f".env.{app_env}"
    if os.path.exists(env_file):
        load_dotenv(env_file, override=True)
        logger.info(f"已加载环境配置文件: {env_file}")
    else:
        logger.warning(f"环境配置文件不存在: {env_file}，使用默认.env配置")

# 在导入settings之前加载环境变量
load_environment()

try:
    from app.settings.config import settings
except ImportError:
    raise SettingNotFound("Can not import settings")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理器，对热重载友好"""
    # 启动阶段
    logger.info("正在初始化应用...")
    
    try:
        # 初始化身份验证控制器
        await AuthControl.initialize()
        logger.info("身份验证控制器初始化完成")
        
        # 使用shield保护初始化过程
        await asyncio.shield(init_data())
        logger.info("数据初始化完成")

    except Exception as e:
        logger.error(f"数据初始化出现问题: {str(e)}")
    
    # 运行阶段
    try:
        yield
    except asyncio.CancelledError:
        # 显式捕获取消异常，以便进行优雅关闭
        logger.warning("应用运行被取消，正在执行关闭...")
    finally:
        # 关闭阶段
        logger.info("应用正在关闭...")
        
        # 确保数据库连接正确关闭
        if Tortoise._inited:
            try:
                await asyncio.shield(Tortoise.close_connections())
            except Exception:
                pass


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_TITLE,
        description=settings.APP_DESCRIPTION,
        version=settings.VERSION,
        openapi_url="/openapi.json",
        middleware=make_middlewares(),
        lifespan=lifespan,
        redirect_slashes=False,  # 禁用URL末尾斜杠重定向
    )
    register_exceptions(app)
    register_routers(app, prefix="/api")
    
    # 设置自定义JSON编码器，处理Decimal类型
    setup_json_encoder(app)
    
    # 添加根路径处理
    @app.get("/")
    async def root():
        """根路径处理器，提供API信息或重定向到文档"""
        # 重定向到API文档
        return RedirectResponse(url="/docs")
    
    return app


# 创建应用实例
app = create_app()
