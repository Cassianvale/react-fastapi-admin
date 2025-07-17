from enum import StrEnum
from typing import Optional, Union, List

from pydantic import BaseModel, Field


class MenuType(StrEnum):
    CATALOG = "catalog"  # 目录
    MENU = "menu"  # 菜单
    BUTTON = "button"  # 按钮


class BaseMenu(BaseModel):
    id: int
    name: str
    path: str
    remark: Optional[dict]
    menu_type: Optional[MenuType]
    icon: Optional[str]
    order: int
    parent_id: int
    is_hidden: bool
    component: str
    keepalive: bool
    redirect: Optional[str]
    children: Optional[list["BaseMenu"]]

    class Config:
        from_attributes = True


class MenuCreate(BaseModel):
    menu_type: MenuType = MenuType.CATALOG
    name: str
    icon: Optional[str] = "ph:user-list-bold"
    path: str
    order: Optional[int] = 1
    parent_id: Optional[int] = 0
    is_hidden: Optional[bool] = False
    component: str = "Layout"
    keepalive: Optional[bool] = True
    redirect: Optional[str] = ""


class MenuUpdate(BaseModel):
    id: int
    menu_type: Optional[MenuType] = None
    name: Optional[str] = None
    icon: Optional[str] = "ph:user-list-bold"
    path: Optional[str] = None
    order: Optional[int] = None
    parent_id: Optional[int] = None
    is_hidden: Optional[bool] = False
    component: Optional[str] = None
    keepalive: Optional[bool] = False
    redirect: Optional[str] = ""
