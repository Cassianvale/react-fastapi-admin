from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI
from tortoise import Tortoise

from app.core.exceptions import SettingNotFound
from app.core.init_app import (
    init_data,
    make_middlewares,
    register_exceptions,
    register_routers,
)
from app.log import logger
from app.core.config import setup_json_encoder  # 导入JSON编码器设置函数

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
    
    return app


# 创建应用实例
app = create_app()
