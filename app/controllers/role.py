from typing import List

from app.core.crud import CRUDBase
from app.models.admin import Role, Permission
from app.schemas.roles import RoleCreate, RoleUpdate


class RoleController(CRUDBase[Role, RoleCreate, RoleUpdate]):
    """角色控制器 - 仅提供角色管理需要的核心功能"""

    def __init__(self):
        super().__init__(model=Role)

    async def is_exist(self, name: str) -> bool:
        return await self.model.filter(name=name).exists()

    async def update_role_permissions(self, role: Role, permission_ids: List[int]) -> None:
        """更新角色权限"""
        await role.permissions.clear()
        if permission_ids:
            permissions = await Permission.filter(id__in=permission_ids)
            for permission in permissions:
                await role.permissions.add(permission)

    async def get_role_permissions(self, role_id: int) -> List[Permission]:
        """获取角色的所有权限"""
        role = await Role.get(id=role_id).prefetch_related("permissions")
        return await role.permissions.filter(is_active=True)

    async def get_role_permissions_tree(self, role_id: int) -> List[dict]:
        """获取角色权限的树形结构"""
        permissions = await self.get_role_permissions(role_id)

        # 构建权限字典，便于查找
        permission_dict = {}
        for perm in permissions:
            perm_data = await perm.to_dict()
            perm_data["children"] = []
            permission_dict[perm.id] = perm_data

        # 构建树形结构
        root_permissions = []
        for perm in permissions:
            if perm.parent_id == 0:
                root_permissions.append(permission_dict[perm.id])
            elif perm.parent_id in permission_dict:
                permission_dict[perm.parent_id]["children"].append(permission_dict[perm.id])

        return root_permissions

    async def get_role_with_stats(self, role: Role) -> dict:
        """获取包含统计信息的角色数据"""
        from app.models.admin import User

        # 获取基础角色信息
        role_data = await role.to_dict()

        # 获取用户数量（通过User模型查询）
        user_count = await User.filter(roles=role.id).count()

        # 获取权限数量
        await role.fetch_related("permissions")
        permission_count = len([p for p in role.permissions if p.is_active])

        # 添加统计信息
        role_data["user_count"] = user_count
        role_data["permission_count"] = permission_count

        return role_data


role_controller = RoleController()
