import shutil
import asyncio

from aerich import Command
from fastapi import FastAPI
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from tortoise.expressions import Q
from tortoise import Tortoise

from app.api import api_router
from app.controllers.api import api_controller
from app.controllers.user import UserCreate, user_controller
from app.core.exceptions import exception_handlers
from app.utils.log_control import logger
from app.models.admin import Api, Role
from app.settings.config import settings

from .middlewares import BackGroundTaskMiddleware, HttpAuditLogMiddleware
from app.utils.log_control import AccessLogMiddleware


def make_middlewares():
    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=settings.CORS_ORIGINS,
            allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
            allow_methods=settings.CORS_ALLOW_METHODS,
            allow_headers=settings.CORS_ALLOW_HEADERS,
        ),
        Middleware(BackGroundTaskMiddleware),
    ]

    # 根据设置决定是否启用访问日志中间件
    if settings.LOG_ENABLE_ACCESS_LOG:
        middleware.append(
            Middleware(
                AccessLogMiddleware,
                skip_paths=["/docs", "/redoc", "/openapi.json", "/favicon.ico", "/static/", "/health"],
            )
        )

    middleware.append(
        Middleware(
            HttpAuditLogMiddleware,
            methods=["GET", "POST", "PUT", "DELETE"],
            exclude_paths=[
                "/api/v1/base/access_token",
                "/docs",
                "/openapi.json",
                # 审计日志相关的API路径
                "/api/v1/auditlog/list",
                "/api/v1/auditlog/delete",
                "/api/v1/auditlog/batch_delete",
                "/api/v1/auditlog/clear",
                "/api/v1/auditlog/export",
                "/api/v1/auditlog/download",
                "/api/v1/auditlog/statistics",
            ],
        )
    )

    return middleware


def register_exceptions(app: FastAPI):
    """注册异常处理器"""
    for exception_type, handler in exception_handlers.items():
        app.add_exception_handler(exception_type, handler)


def register_routers(app: FastAPI, prefix: str = "/api"):
    app.include_router(api_router, prefix=prefix)


async def init_superuser():
    user = await user_controller.model.exists()
    if not user:
        admin_user = await user_controller.create_user(
            UserCreate(
                username="admin",
                email="admin@admin.com",
                nickname="admin",
                phone=None,
                password="123456",
                is_active=True,
                is_superuser=True,
            )
        )
        return admin_user
    return None





async def init_apis():
    apis = await api_controller.model.exists()
    if not apis:
        await api_controller.refresh_api()


async def init_db():
    command = Command(tortoise_config=settings.tortoise_orm)
    # 确保Tortoise已初始化
    if not Tortoise._inited:
        await Tortoise.init(config=settings.tortoise_orm)

    try:
        # 使用shield保护数据库操作
        await asyncio.shield(command.init_db(safe=True))
        await command.init()
        await asyncio.shield(command.migrate())
        await asyncio.shield(command.upgrade(run_in_transaction=True))
    except FileExistsError:
        # 忽略已存在的migrations目录
        pass
    except AttributeError:
        # 处理无法检索模型历史的情况
        logger.warning("无法从数据库检索模型历史，将从头创建模型历史")
        shutil.rmtree("migrations")
        await asyncio.shield(command.init_db(safe=True))
        await command.init()
        await asyncio.shield(command.upgrade(run_in_transaction=True))
    except Exception as e:
        # 记录其他异常但不中断应用启动
        logger.error(f"数据库初始化过程出错: {str(e)}")


async def init_roles():
    roles = await Role.exists()
    if not roles:
        admin_role = await Role.create(
            name="管理员",
            desc="管理员角色",
        )
        user_role = await Role.create(
            name="普通用户",
            desc="普通用户角色",
        )
        return admin_role, user_role
    return None, None


async def init_user_roles():
    """初始化用户角色关系"""
    from app.models.admin import User

    # 获取管理员角色
    admin_role = await Role.filter(name="管理员").first()
    if not admin_role:
        logger.warning("未找到管理员角色，跳过角色分配")
        return

    # 获取超级管理员用户
    admin_user = await User.filter(username="admin", is_superuser=True).first()
    if admin_user:
        # 检查是否已经分配了管理员角色
        user_roles = await admin_user.roles.all()
        admin_role_assigned = any(role.name == "管理员" for role in user_roles)

        if not admin_role_assigned:
            await admin_user.roles.add(admin_role)
            logger.info("为超级管理员用户分配了管理员角色")
        else:
            logger.info("超级管理员用户已经拥有管理员角色")
    else:
        logger.warning("未找到超级管理员用户")


async def init_data():
    """初始化应用数据"""
    await init_db()
    await init_superuser()
    await init_apis()
    await init_roles()

    # 初始化用户角色关系
    await init_user_roles()
