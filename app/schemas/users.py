from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class BaseUser(BaseModel):
    id: int
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    last_login: Optional[datetime]
    roles: Optional[list] = []

    class Config:
        from_attributes = True


class UserOut(BaseModel):
    """用户输出模型，用于API响应"""

    id: int
    username: str
    email: EmailStr
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    email: EmailStr = Field(description="邮箱")
    username: str = Field(description="用户名")
    password: str = Field(description="密码")
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False
    role_ids: Optional[List[int]] = []
    dept_id: Optional[int] = Field(default=0, description="部门ID")

    def create_dict(self):
        return self.model_dump(exclude_unset=True, exclude={"role_ids"})


class UserUpdate(BaseModel):
    id: int
    username: Optional[str] = Field(None, description="用户名")
    email: Optional[EmailStr] = Field(None, description="邮箱")
    password: Optional[str] = Field(None, description="密码")
    is_active: Optional[bool] = Field(None, description="是否激活")
    is_superuser: Optional[bool] = Field(None, description="是否是超级管理员")
    role_ids: Optional[List[int]] = Field(None, description="角色ids")
    dept_id: Optional[int] = Field(None, description="部门ID")


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenPayload(BaseModel):
    id: int
    username: str
    email: str
    is_active: Optional[bool] = True
    is_superuser: bool
    role_ids: Optional[List[int]] = []
    dept_id: Optional[int] = 0


class UpdatePassword(BaseModel):
    old_password: str = Field(description="旧密码")
    new_password: str = Field(description="新密码")


class ProfileUpdate(BaseModel):
    """用户个人信息更新模型"""

    nickname: Optional[str] = Field(None, max_length=30, description="昵称")
    email: Optional[EmailStr] = Field(None, description="邮箱")
    phone: Optional[str] = Field(None, max_length=11, description="手机号码")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):
        if v is not None and v != "":
            # 检查是否为11位数字且以1开头，第二位为3-9
            if not v.isdigit() or len(v) != 11 or not v.startswith("1") or v[1] not in "3456789":
                raise ValueError("手机号码必须是11位数字，且格式正确")
        return v

    def update_dict(self):
        return self.model_dump(exclude_unset=True)
