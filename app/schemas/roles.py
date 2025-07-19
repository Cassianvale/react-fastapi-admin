from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class BaseRole(BaseModel):
    id: int
    name: str
    desc: str = ""
    users: Optional[list] = []
    permissions: Optional[list] = []
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class RoleCreate(BaseModel):
    name: str = Field(..., description="角色名称")
    desc: str = Field("", description="角色描述")
    permission_ids: Optional[list] = []


class RoleUpdate(BaseModel):
    id: int
    name: Optional[str] = Field(None, description="角色名称")
    desc: Optional[str] = Field(None, description="角色描述")
    permission_ids: Optional[list] = None


class RoleUpdatePermissions(BaseModel):
    """角色权限更新模型"""

    id: int = Field(..., description="角色ID")
    permission_ids: list = Field([], description="权限ID列表")
