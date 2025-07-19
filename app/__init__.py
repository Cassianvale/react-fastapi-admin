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
from app.utils.log_control import logger, init_logging
from app.core.dependency import AuthControl  # 导入身份验证控制器


# 加载环境变量
def load_environment():
    """加载.env文件中的环境变量"""
    # 不覆盖已存在的环境变量
    load_dotenv(override=False)

    # 获取当前环境
    app_env = os.getenv("APP_ENV", "development")
    logger.info(f"当前运行环境: {app_env}")


# 在导入settings之前加载环境变量
load_environment()

try:
    from app.settings.config import settings
except ImportError:
    raise SettingNotFound


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理器，对热重载友好"""
    # 启动阶段
    # 首先初始化日志系统
    init_logging()
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

    # 添加静态文件挂载
    from fastapi.staticfiles import StaticFiles

    # 注意：存储目录只在实际需要时创建，不在应用启动时自动创建
    # 这样可以避免在不使用文件上传功能时创建不必要的目录

    # 挂载静态文件目录（如果存储目录存在的话）
    storage_dir = os.path.join(settings.BASE_DIR, "storage")
    if os.path.exists(storage_dir):
        app.mount("/static", StaticFiles(directory=storage_dir), name="static")
    else:
        # 如果存储目录不存在，创建一个延迟挂载的处理器
        @app.middleware("http")
        async def ensure_static_mount(request, call_next):
            # 检查是否是静态文件请求且存储目录现在存在
            if request.url.path.startswith("/static") and os.path.exists(storage_dir):
                # 如果存储目录现在存在但还没有挂载，则挂载它
                if "static" not in [route.name for route in app.routes if hasattr(route, "name")]:
                    app.mount("/static", StaticFiles(directory=storage_dir), name="static")

            response = await call_next(request)
            return response

    # 添加根路径处理
    @app.get("/")
    async def root():
        """根路径处理器，提供API信息或重定向到文档"""
        # 重定向到API文档
        return RedirectResponse(url="/docs")

    return app


# 创建应用实例
app = create_app()
