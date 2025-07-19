from fastapi.routing import APIRoute

from app.core.crud import CRUDBase
from app.utils.log_control import logger
from app.models.admin import Api
from app.models.enums import MethodType
from app.schemas.apis import ApiCreate, ApiUpdate


class ApiController(CRUDBase[Api, ApiCreate, ApiUpdate]):
    def __init__(self):
        super().__init__(model=Api)

    async def refresh_api(self):
        from app import app

        # 删除废弃API数据
        all_api_list = []
        for route in app.routes:
            # 只更新有鉴权的API
            if isinstance(route, APIRoute) and len(route.dependencies) > 0:
                all_api_list.append((list(route.methods)[0], route.path_format))
        delete_api = []
        for api in await Api.all():
            if (api.method, api.path) not in all_api_list:
                delete_api.append((api.method, api.path))
        for item in delete_api:
            method, path = item
            logger.debug(f"API Deleted {method} {path}")
            await Api.filter(method=method, path=path).delete()

        for route in app.routes:
            if isinstance(route, APIRoute) and len(route.dependencies) > 0:
                method = list(route.methods)[0]
                path = route.path_format
                summary = route.summary or ""
                # 安全获取标签，如果没有标签则使用默认值
                tags = list(route.tags)[0] if route.tags else "未分类"
                api_obj = await Api.filter(method=method, path=path).first()
                if api_obj:
                    await api_obj.update_from_dict(dict(method=method, path=path, summary=summary, tags=tags)).save()
                else:
                    logger.debug(f"API Created {method} {path}")
                    # 修复：正确创建API对象，确保method字段类型正确
                    api_obj = await Api.create(
                        method=MethodType(method), path=path, summary=summary, tags=tags  # 确保正确的枚举类型
                    )
                    # 自动创建对应的权限
                    await self._create_api_permission(api_obj)

    async def _create_api_permission(self, api_obj):
        """为API自动创建权限"""
        from app.models.admin import Permission
        from app.models.enums import PermissionType, MethodType

        # 生成权限代码
        permission_code = Permission.generate_permission_code(
            permission_type=PermissionType.ACTION,
            api_path=api_obj.path,
            api_method=api_obj.method.value,
        )

        # 检查权限是否已存在
        existing_permission = await Permission.filter(code=permission_code).first()
        if existing_permission:
            return existing_permission

        # 创建权限
        permission = await Permission.create(
            name=api_obj.summary or f"{api_obj.method.value} {api_obj.path}",
            code=permission_code,
            description=f"API权限: {api_obj.summary or api_obj.path}",
            permission_type=PermissionType.ACTION,
            parent_id=0,  # 可以后续根据模块分组
            order=0,
            is_active=True,
            api_path=api_obj.path,
            api_method=api_obj.method,
        )

        logger.debug(f"Permission Created: {permission.code} for API {api_obj.method.value} {api_obj.path}")
        return permission

    async def _delete_api_permission(self, api_obj):
        """删除API对应的权限"""
        from app.models.admin import Permission
        from app.models.enums import PermissionType

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
            logger.debug(f"Permission Deleted: {permission.code} for API {api_obj.method.value} {api_obj.path}")

        return True

    async def get_all_tags(self):
        """获取所有API标签"""
        # 获取所有API的标签
        apis = await Api.all()
        tags = []
        tag_counts = {}

        for api in apis:
            if api.tags and api.tags.strip():
                tag = api.tags.strip()
                if tag not in tag_counts:
                    tag_counts[tag] = 0
                tag_counts[tag] += 1

        # 按使用频率排序，返回标签和对应的API数量
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)

        for tag, count in sorted_tags:
            tags.append({"label": tag, "value": tag, "count": count})

        return tags


api_controller = ApiController()
