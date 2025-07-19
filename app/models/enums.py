from enum import Enum, StrEnum


class EnumBase(Enum):
    @classmethod
    def get_member_values(cls):
        return [item.value for item in cls._member_map_.values()]

    @classmethod
    def get_member_names(cls):
        return [name for name in cls._member_names_]


class MethodType(StrEnum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


class PermissionType(StrEnum):
    """权限类型枚举"""

    MODULE = "module"  # 模块权限（如：系统管理）
    FEATURE = "feature"  # 功能权限（如：角色管理）
    ACTION = "action"  # 操作权限（如：添加角色）


class ResourceType(StrEnum):
    """资源类型枚举"""

    MENU = "menu"  # 菜单资源
    API = "api"  # API资源
    BUTTON = "button"  # 按钮资源


class MenuType(StrEnum):
    """菜单类型枚举"""

    CATALOG = "catalog"  # 目录
    MENU = "menu"  # 菜单
    BUTTON = "button"  # 按钮
