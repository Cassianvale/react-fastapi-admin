from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class BaseRole(BaseModel):
    id: int
    name: str
    desc: str = ""
    users: Optional[list] = []
    menus: Optional[list] = []
    apis: Optional[list] = []
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class RoleCreate(BaseModel):
    name: str = Field(..., description="角色名称")
    desc: str = Field("", description="角色描述")
    menu_ids: Optional[list] = []
    api_ids: Optional[list] = []


class RoleUpdate(BaseModel):
    id: int
    name: Optional[str] = Field(None, description="角色名称")
    desc: Optional[str] = Field(None, description="角色描述")
    menu_ids: Optional[list] = None
    api_ids: Optional[list] = None


class RoleUpdateMenusApis(BaseModel):
    id: int
    menu_ids: list[int] = []
    api_infos: list[dict] = []
