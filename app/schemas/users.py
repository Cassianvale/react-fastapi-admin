from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


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


class UserCreate(BaseModel):
    email: EmailStr = Field(example="admin@qq.com", description="邮箱")
    username: str = Field(example="admin", description="用户名")
    password: str = Field(example="123456", description="密码")
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False
    role_ids: Optional[List[int]] = []
    dept_id: Optional[int] = Field(0, description="部门ID")

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
