"""
API控制器模块

负责API管理和权限自动生成功能
"""

from typing import List, Dict, Optional, Tuple
from fastapi.routing import APIRoute

from app.core.crud import CRUDBase
from app.utils.log_control import logger
from app.models.admin import Api
from app.models.enums import MethodType
from app.schemas.apis import ApiCreate, ApiUpdate


# 权限配置管理
class PermissionConfig:
    """动态权限配置管理类"""

    def __init__(self):
        self._config = None
        self._config_loaded = False

    def _load_config(self):
        """加载权限配置"""
        if self._config_loaded:
            return

        try:
            from app.utils.config_manager import config_manager

            # 尝试从文件加载配置
            config = config_manager.load_config()

            if config is None:
                logger.warning("权限配置文件不存在，使用默认配置并自动生成")
                # 生成默认配置
                config = self._get_default_config()
                config_manager.save_config(config)

            # 验证配置
            is_valid, errors = config_manager.validate_config(config)
            if not is_valid:
                logger.error(f"权限配置验证失败: {errors}")
                logger.warning("使用默认配置")
                config = self._get_default_config()

            self._config = config
            self._config_loaded = True
            logger.debug("权限配置加载完成")

        except Exception as e:
            logger.error(f"加载权限配置失败: {str(e)}")
            logger.warning("使用默认配置")
            self._config = self._get_default_config()
            self._config_loaded = True

    def _get_default_config(self):
        """获取默认配置"""
        return {
            "MODULE_TO_PARENT_MENU": {
                "base": "personal",
                "user": "system",
                "role": "system",
                "menu": "system",
                "api": "system",
                "dept": "system",
                "auditlog": "system",
                "upload": "system",
            },
            "PARENT_MENU_MAPPING": {
                "personal": {"name": "个人中心", "desc": "个人信息和设置相关功能"},
                "system": {"name": "系统管理", "desc": "系统配置和管理功能"},
                "monitor": {"name": "监控管理", "desc": "系统监控和日志管理"},
                "resource": {"name": "资源管理", "desc": "文件和资源管理功能"},
            },
            "SUB_MENU_MAPPING": {
                "base": "个人设置",
                "user": "用户管理",
                "role": "角色管理",
                "menu": "菜单管理",
                "api": "API管理",
                "dept": "部门管理",
                "auditlog": "审计日志",
                "upload": "文件管理",
            },
        }

    @property
    def MODULE_TO_PARENT_MENU(self):
        """模块到父菜单的映射"""
        self._load_config()
        return self._config.get("MODULE_TO_PARENT_MENU", {})

    @property
    def PARENT_MENU_MAPPING(self):
        """父菜单信息映射"""
        self._load_config()
        return self._config.get("PARENT_MENU_MAPPING", {})

    @property
    def SUB_MENU_MAPPING(self):
        """子菜单名称映射"""
        self._load_config()
        return self._config.get("SUB_MENU_MAPPING", {})

    def reload_config(self):
        """重新加载配置"""
        self._config_loaded = False
        self._config = None
        self._load_config()
        logger.info("权限配置已重新加载")

    def get_missing_modules(self, discovered_modules: List[str]) -> List[str]:
        """获取配置中缺失的模块"""
        self._load_config()
        configured_modules = set(self.MODULE_TO_PARENT_MENU.keys())
        return [module for module in discovered_modules if module not in configured_modules]


class ApiController(CRUDBase[Api, ApiCreate, ApiUpdate]):
    def __init__(self):
        super().__init__(model=Api)
        self.permission_config = PermissionConfig()

    async def refresh_api(self) -> None:
        """
        刷新API数据并自动生成权限

        功能：
        1. 扫描应用中的所有API路由
        2. 删除已废弃的API记录
        3. 创建或更新API记录
        4. 自动生成对应的权限结构
        """
        from app import app

        logger.info("🔄 开始刷新API数据...")

        # 1. 收集当前应用中的所有API路由
        current_apis = self._collect_current_apis(app)
        logger.debug(f"发现 {len(current_apis)} 个需要鉴权的API")

        # 2. 删除废弃的API数据
        await self._cleanup_obsolete_apis(current_apis)

        # 3. 创建或更新API记录并生成权限
        await self._sync_apis_and_permissions(app, current_apis)

        logger.info("✅ API数据刷新完成")

    def _collect_current_apis(self, app) -> List[Tuple[str, str]]:
        """收集当前应用中需要鉴权的API"""
        current_apis = []
        for route in app.routes:
            if isinstance(route, APIRoute) and len(route.dependencies) > 0:
                method = list(route.methods)[0]
                path = route.path_format
                current_apis.append((method, path))
        return current_apis

    async def _cleanup_obsolete_apis(self, current_apis: List[Tuple[str, str]]) -> None:
        """清理已废弃的API数据"""
        existing_apis = await Api.all()
        obsolete_apis = []

        for api in existing_apis:
            if (api.method.value, api.path) not in current_apis:
                obsolete_apis.append(api)

        if obsolete_apis:
            logger.info(f"🗑️ 发现 {len(obsolete_apis)} 个废弃API，正在清理...")
            for api in obsolete_apis:
                logger.debug(f"删除废弃API: {api.method.value} {api.path}")
                await self._delete_api_permission(api)  # 先删除权限
                await api.delete()  # 再删除API记录

    async def _sync_apis_and_permissions(self, app, current_apis: List[Tuple[str, str]]) -> None:
        """同步API记录并生成权限"""
        for route in app.routes:
            if isinstance(route, APIRoute) and len(route.dependencies) > 0:
                await self._process_single_api_route(route)

    async def _process_single_api_route(self, route: APIRoute) -> None:
        """处理单个API路由"""
        method = list(route.methods)[0]
        path = route.path_format
        summary = route.summary or ""
        tags = list(route.tags)[0] if route.tags else "未分类"

        # 查找或创建API记录
        api_obj = await Api.filter(method=method, path=path).first()
        if api_obj:
            # 更新现有API
            await api_obj.update_from_dict({"method": method, "path": path, "summary": summary, "tags": tags}).save()
            logger.debug(f"API更新: {method} {path}")
        else:
            # 创建新API
            api_obj = await Api.create(method=MethodType(method), path=path, summary=summary, tags=tags)
            logger.debug(f"API创建: {method} {path}")

        # 确保权限存在
        await self._create_api_permission(api_obj)

    async def _create_api_permission(self, api_obj) -> Optional[object]:
        """
        为API自动创建菜单式三层权限结构

        权限层级：
        1. 父菜单级权限（如：系统管理）
        2. 子菜单级权限（如：用户管理）
        3. 接口级权限（如：查看用户列表）

        Args:
            api_obj: API对象

        Returns:
            创建的接口级权限对象，如果创建失败则返回None
        """
        from app.models.admin import Permission
        from app.models.enums import PermissionType

        # 解析API路径获取模块信息
        module_name = self._extract_module_name(api_obj.path)
        if not module_name:
            logger.warning(f"API路径格式不标准，跳过权限创建: {api_obj.path}")
            return None

        try:
            # 1. 创建或获取父菜单级权限
            parent_menu_permission = await self._ensure_parent_menu_permission(module_name)

            # 2. 创建或获取子菜单级权限
            sub_menu_permission = await self._ensure_sub_menu_permission(module_name, parent_menu_permission.id)

            # 3. 创建接口级权限
            api_permission = await self._ensure_api_permission(api_obj, sub_menu_permission.id)

            return api_permission
        except Exception as e:
            logger.error(f"创建API权限失败 {api_obj.method.value} {api_obj.path}: {str(e)}")
            return None

    def _extract_module_name(self, api_path: str) -> Optional[str]:
        """从API路径中提取模块名称"""
        path_parts = api_path.strip("/").split("/")

        # 标准格式：/api/v1/{module}/{action}
        if len(path_parts) >= 3 and path_parts[0] == "api" and path_parts[1] == "v1":
            clean_parts = path_parts[2:]  # 从第3个部分开始：[module, action, ...]
        else:
            clean_parts = [part for part in path_parts if part and part not in ["api", "v1"]]

        return clean_parts[0] if clean_parts else None

    async def _ensure_parent_menu_permission(self, module_name: str):
        """
        确保父菜单级权限存在

        Args:
            module_name: 模块名称（如：user, role, menu等）

        Returns:
            父菜单权限对象
        """
        from app.models.admin import Permission
        from app.models.enums import PermissionType

        parent_menu_name = self.permission_config.MODULE_TO_PARENT_MENU.get(module_name, "system")
        parent_menu_code = f"menu.{parent_menu_name}"

        # 检查是否已存在
        existing = await Permission.filter(code=parent_menu_code).first()
        if existing:
            return existing

        # 获取父菜单信息
        parent_menu_info = self.permission_config.PARENT_MENU_MAPPING.get(
            parent_menu_name, {"name": f"{parent_menu_name.title()}管理", "desc": f"{parent_menu_name}相关功能"}
        )

        # 创建父菜单权限
        parent_menu_permission = await Permission.create(
            name=parent_menu_info["name"],
            code=parent_menu_code,
            description=parent_menu_info["desc"],
            permission_type=PermissionType.MODULE,
            parent_id=0,
            order=0,
            is_active=True,
        )

        logger.debug(f"父菜单权限已创建: {parent_menu_code}")
        return parent_menu_permission

    async def _ensure_sub_menu_permission(self, module_name: str, parent_menu_id: int):
        """
        确保子菜单级权限存在

        Args:
            module_name: 模块名称
            parent_menu_id: 父菜单权限ID

        Returns:
            子菜单权限对象
        """
        from app.models.admin import Permission
        from app.models.enums import PermissionType

        # 获取父菜单名称
        parent_menu = await Permission.get(id=parent_menu_id)
        parent_menu_name = parent_menu.code.split(".")[-1]  # 从 menu.system 获取 system

        sub_menu_code = f"submenu.{parent_menu_name}.{module_name}"

        # 检查是否已存在
        existing = await Permission.filter(code=sub_menu_code).first()
        if existing:
            return existing

        # 获取子菜单名称
        sub_menu_name = self.permission_config.SUB_MENU_MAPPING.get(module_name, f"{module_name.title()}管理")

        # 创建子菜单权限
        sub_menu_permission = await Permission.create(
            name=sub_menu_name,
            code=sub_menu_code,
            description=f"{sub_menu_name}相关功能",
            permission_type=PermissionType.FEATURE,
            parent_id=parent_menu_id,
            order=0,
            is_active=True,
        )

        logger.debug(f"子菜单权限已创建: {sub_menu_code}")
        return sub_menu_permission

    async def _ensure_api_permission(self, api_obj, sub_menu_id: int):
        """
        确保接口级权限存在

        Args:
            api_obj: API对象
            sub_menu_id: 子菜单权限ID

        Returns:
            接口权限对象
        """
        from app.models.admin import Permission
        from app.models.enums import PermissionType

        # 生成权限代码
        permission_code = Permission.generate_permission_code(
            permission_type=PermissionType.ACTION,
            api_path=api_obj.path,
            api_method=api_obj.method.value,
        )

        # 检查权限是否已存在
        existing_permission = await Permission.filter(code=permission_code).first()
        if existing_permission:
            # 更新父权限ID（如果不正确）
            if existing_permission.parent_id != sub_menu_id:
                existing_permission.parent_id = sub_menu_id
                await existing_permission.save()
                logger.debug(f"权限父级关系已更新: {permission_code}")
            return existing_permission

        # 创建接口权限
        permission = await Permission.create(
            name=api_obj.summary or f"{api_obj.method.value} {api_obj.path}",
            code=permission_code,
            description=f"API接口: {api_obj.summary or api_obj.path}",
            permission_type=PermissionType.ACTION,
            parent_id=sub_menu_id,
            order=0,
            is_active=True,
            api_path=api_obj.path,
            api_method=api_obj.method,
        )

        logger.debug(f"接口权限已创建: {permission.code} for API {api_obj.method.value} {api_obj.path}")
        return permission

    async def _delete_api_permission(self, api_obj) -> bool:
        """
        删除API对应的权限

        Args:
            api_obj: API对象

        Returns:
            删除是否成功
        """
        from app.models.admin import Permission
        from app.models.enums import PermissionType

        try:
            # 生成权限代码
            permission_code = Permission.generate_permission_code(
                permission_type=PermissionType.ACTION,
                api_path=api_obj.path,
                api_method=api_obj.method.value,
            )

            # 查找并删除权限
            permission = await Permission.filter(code=permission_code).first()
            if permission:
                await permission.delete()
                logger.debug(f"权限已删除: {permission.code} for API {api_obj.method.value} {api_obj.path}")

            return True
        except Exception as e:
            logger.error(f"删除API权限失败 {api_obj.method.value} {api_obj.path}: {str(e)}")
            return False

    async def get_all_tags(self) -> List[Dict[str, any]]:
        """
        获取所有API标签及其使用统计

        Returns:
            标签列表，包含标签名称、值和使用次数
        """
        try:
            # 获取所有API的标签
            apis = await Api.all()
            tag_counts = {}

            # 统计标签使用次数
            for api in apis:
                if api.tags and api.tags.strip():
                    tag = api.tags.strip()
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1

            # 按使用频率排序，返回标签和对应的API数量
            sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)

            return [{"label": tag, "value": tag, "count": count} for tag, count in sorted_tags]
        except Exception as e:
            logger.error(f"获取API标签失败: {str(e)}")
            return []


api_controller = ApiController()
