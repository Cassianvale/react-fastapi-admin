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
from app.models.admin import Api, Menu, Role
from app.models.enums import MenuType
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


# 初始化生成菜单
async def init_menus():
    menus = await Menu.exists()
    if not menus:
        parent_menu = await Menu.create(
            menu_type=MenuType.CATALOG,
            name="系统管理",
            path="/system",
            order=1,
            parent_id=0,
            icon="carbon:gui-management",
            is_hidden=False,
            component="Layout",
            keepalive=False,
            redirect="/system/users",
        )
        children_menu = [
            Menu(
                menu_type=MenuType.MENU,
                name="用户管理",
                path="users",
                order=1,
                parent_id=parent_menu.id,
                icon="material-symbols:person-outline-rounded",
                is_hidden=False,
                component="/system/users",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="角色管理",
                path="roles",
                order=2,
                parent_id=parent_menu.id,
                icon="carbon:user-role",
                is_hidden=False,
                component="/system/roles",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="菜单管理",
                path="menus",
                order=3,
                parent_id=parent_menu.id,
                icon="material-symbols:list-alt-outline",
                is_hidden=False,
                component="/system/menus",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="API管理",
                path="apis",
                order=4,
                parent_id=parent_menu.id,
                icon="ant-design:api-outlined",
                is_hidden=False,
                component="/system/apis",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="部门管理",
                path="departments",
                order=5,
                parent_id=parent_menu.id,
                icon="mingcute:department-line",
                is_hidden=False,
                component="/system/departments",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="审计日志",
                path="audit",
                order=6,
                parent_id=parent_menu.id,
                icon="ph:clipboard-text-bold",
                is_hidden=False,
                component="/system/audit",
                keepalive=False,
            ),
        ]
        await Menu.bulk_create(children_menu)


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


async def init_permissions_and_assign_roles():
    """初始化权限并分配角色"""
    from app.models.admin import Permission, User

    # 获取管理员角色
    admin_role = await Role.filter(name="管理员").first()
    if not admin_role:
        logger.warning("未找到管理员角色，跳过权限分配")
        return

    # 获取所有权限
    all_permissions = await Permission.filter(is_active=True).all()
    logger.info(f"系统中共有 {len(all_permissions)} 个活跃权限")

    # 检查管理员角色当前的权限数量
    current_permissions = await admin_role.permissions.all()
    logger.info(f"管理员角色当前有 {len(current_permissions)} 个权限")

    # 为管理员角色分配所有权限（无论是否已有权限都重新分配）
    if all_permissions:
        await admin_role.permissions.clear()
        for permission in all_permissions:
            await admin_role.permissions.add(permission)
        logger.info(f"为管理员角色重新分配了 {len(all_permissions)} 个权限")
    else:
        logger.warning("系统中没有找到任何活跃权限")

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
    await init_menus()
    await init_apis()
    await init_roles()

    # 每次启动都检查和分配权限（确保管理员角色拥有所有权限）
    await init_permissions_and_assign_roles()
