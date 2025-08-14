from app.core.crud import CRUDBase
from app.models.admin import Role
from app.schemas.roles import RoleCreate, RoleUpdate


class RoleController(CRUDBase[Role, RoleCreate, RoleUpdate]):
    """角色控制器 - 提供基本的角色CRUD功能"""

    def __init__(self):
        super().__init__(model=Role)

    async def is_exist(self, name: str) -> bool:
        return await self.model.filter(name=name).exists()

    async def get_role_with_stats(self, role: Role) -> dict:
        """获取包含统计信息的角色数据"""
        from app.models.admin import User

        # 获取基础角色信息
        role_data = await role.to_dict()

        # 获取用户数量（通过User模型查询）
        user_count = await User.filter(roles=role.id).count()

        # 添加统计信息
        role_data["user_count"] = user_count

        return role_data


role_controller = RoleController()
