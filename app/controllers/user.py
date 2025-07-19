from datetime import datetime
from typing import List, Optional, Tuple

from fastapi.exceptions import HTTPException

from app.core.crud import CRUDBase
from app.models.admin import User
from app.schemas.login import CredentialsSchema
from app.schemas.users import UserCreate, UserUpdate
from app.utils.password import get_password_hash, verify_password, validate_password_strength

from .role import role_controller


class UserController(CRUDBase[User, UserCreate, UserUpdate]):
    def __init__(self):
        super().__init__(model=User)

    async def get_by_email(self, email: str) -> Optional[User]:
        return await self.model.filter(email=email).first()

    async def get_by_username(self, username: str) -> Optional[User]:
        return await self.model.filter(username=username).first()

    async def validate_password(self, password: str) -> Tuple[bool, str]:
        """
        验证密码强度
        :param password: 要验证的密码
        :return: (是否通过验证, 失败原因)
        """
        return validate_password_strength(password)

    async def create_user(self, obj_in: UserCreate) -> User:
        # 验证密码强度，初始化时绕过密码强度校验
        if obj_in.password != "123456":
            is_valid, message = await self.validate_password(obj_in.password)
            if not is_valid:
                raise HTTPException(status_code=400, detail=f"密码强度不足: {message}")

        obj_in.password = get_password_hash(password=obj_in.password)
        obj = await self.create(obj_in)
        return obj

    async def update_last_login(self, id: int) -> None:
        user = await self.model.get(id=id)
        user.last_login = datetime.now()
        await user.save()

    async def authenticate(self, credentials: CredentialsSchema) -> Optional["User"]:
        # 获取用户
        user = await self.model.filter(username=credentials.username).first()
        if not user:
            # 为了防止用户枚举攻击，不明确指出用户不存在
            raise HTTPException(status_code=400, detail="用户名或密码错误")

        # 验证密码
        verified = verify_password(credentials.password, user.password)
        if not verified:
            # 为了防止用户枚举攻击，不明确指出密码错误
            raise HTTPException(status_code=400, detail="用户名或密码错误")

        # 检查用户状态
        if not user.is_active:
            raise HTTPException(status_code=400, detail="用户已被禁用")

        return user

    async def update_roles(self, user: User, role_ids: List[int]) -> None:
        await user.roles.clear()
        for role_id in role_ids:
            role_obj = await role_controller.get(id=role_id)
            await user.roles.add(role_obj)

        # 清除用户的权限缓存
        from app.controllers.permission import permission_controller

        permission_controller.clear_user_cache(user.id)

    async def reset_password(self, user_id: int, new_password: str = "123456"):
        user_obj = await self.get(id=user_id)
        if user_obj.is_superuser:
            raise HTTPException(status_code=403, detail="不允许重置超级管理员密码")

        # 验证新密码强度（除非是默认密码）
        if new_password != "123456":
            is_valid, message = await self.validate_password(new_password)
            if not is_valid:
                raise HTTPException(status_code=400, detail=f"密码强度不足: {message}")

        user_obj.password = get_password_hash(password=new_password)
        await user_obj.save()


user_controller = UserController()
