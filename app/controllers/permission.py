from typing import List, Optional

from app.models.admin import Permission


class PermissionController:
    """权限控制器 - 仅提供角色管理需要的核心功能"""

    def __init__(self):
        self.model = Permission

    async def get_by_code(self, code: str) -> Optional[Permission]:
        """根据权限代码获取权限"""
        return await self.model.filter(code=code).first()

    async def get_user_permissions(self, user_id: int) -> List[Permission]:
        """获取用户的所有权限"""
        from app.models.admin import User

        user = await User.get(id=user_id).prefetch_related("roles__permissions")
        permissions = []

        for role in user.roles:
            role_permissions = await role.permissions.filter(is_active=True)
            permissions.extend(role_permissions)

        # 去重
        unique_permissions = {}
        for perm in permissions:
            unique_permissions[perm.id] = perm

        return list(unique_permissions.values())

    async def get_user_menu_permissions(self, user_id: int) -> List[Permission]:
        """获取用户的菜单权限"""
        permissions = await self.get_user_permissions(user_id)
        return [p for p in permissions if p.menu_path is not None]

    async def get_user_api_permissions(self, user_id: int) -> List[Permission]:
        """获取用户的API权限"""
        permissions = await self.get_user_permissions(user_id)
        return [p for p in permissions if p.api_path is not None and p.api_method is not None]

    async def check_user_permission(self, user_id: int, permission_code: str) -> bool:
        """检查用户是否有指定权限"""
        permissions = await self.get_user_permissions(user_id)
        return any(p.code == permission_code for p in permissions)

    async def check_user_api_permission(self, user_id: int, api_path: str, api_method: str) -> bool:
        """检查用户是否有指定API权限"""
        permissions = await self.get_user_api_permissions(user_id)
        return any(p.api_path == api_path and p.api_method == api_method for p in permissions)


permission_controller = PermissionController()
