from typing import List, Optional, Dict
import time

from app.models.admin import Permission


class PermissionController:
    """权限控制器 - 提供权限管理和缓存功能"""

    def __init__(self):
        self.model = Permission
        # 用户权限缓存 {user_id: {"permissions": List[Permission], "timestamp": float}}
        self._user_permissions_cache: Dict[int, Dict] = {}
        # 缓存过期时间（秒）
        self._cache_ttl = 3600  # 1小时
        # 最大缓存条目数
        self._max_cache_size = 1000

    def _is_cache_valid(self, cache_entry: Dict) -> bool:
        """检查缓存是否有效"""
        if not cache_entry:
            return False
        current_time = time.time()
        return current_time - cache_entry["timestamp"] < self._cache_ttl

    def _clean_expired_cache(self):
        """清理过期的缓存条目"""
        current_time = time.time()
        expired_keys = []

        for user_id, cache_entry in self._user_permissions_cache.items():
            if current_time - cache_entry["timestamp"] >= self._cache_ttl:
                expired_keys.append(user_id)

        for key in expired_keys:
            self._user_permissions_cache.pop(key, None)

    def _limit_cache_size(self):
        """限制缓存大小，移除最旧的条目"""
        if len(self._user_permissions_cache) > self._max_cache_size:
            # 按时间戳排序，移除最旧的条目
            sorted_items = sorted(self._user_permissions_cache.items(), key=lambda x: x[1]["timestamp"])
            # 保留最新的条目
            keep_count = int(self._max_cache_size * 0.8)  # 保留80%
            items_to_keep = sorted_items[-keep_count:]
            self._user_permissions_cache = dict(items_to_keep)

    def clear_user_cache(self, user_id: int):
        """清除指定用户的权限缓存"""
        self._user_permissions_cache.pop(user_id, None)

    def clear_all_cache(self):
        """清除所有权限缓存"""
        self._user_permissions_cache.clear()

    def clear_users_cache_by_role(self, role_id: int):
        """清除拥有指定角色的所有用户的权限缓存"""
        # 由于需要查询数据库来确定哪些用户拥有该角色，这里采用清空所有缓存的策略
        # 在生产环境中，可以考虑使用Redis等外部缓存来实现更精确的缓存清理
        # role_id 参数保留用于未来的精确缓存清理实现
        _ = role_id  # 标记参数已使用，避免linting警告
        self.clear_all_cache()

    async def get_by_code(self, code: str) -> Optional[Permission]:
        """根据权限代码获取权限"""
        return await self.model.filter(code=code).first()

    async def get_user_permissions(self, user_id: int, use_cache: bool = True) -> List[Permission]:
        """获取用户的所有权限（支持缓存）"""
        # 检查缓存
        if use_cache:
            cache_entry = self._user_permissions_cache.get(user_id)
            if cache_entry and self._is_cache_valid(cache_entry):
                return cache_entry["permissions"]

        # 清理过期缓存
        self._clean_expired_cache()

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

        result_permissions = list(unique_permissions.values())

        # 缓存结果
        if use_cache:
            self._user_permissions_cache[user_id] = {"permissions": result_permissions, "timestamp": time.time()}
            # 限制缓存大小
            self._limit_cache_size()

        return result_permissions

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
