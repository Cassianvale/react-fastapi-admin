"""
配置管理工具

提供配置生成、验证、更新等功能
"""

import json
import os
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from app.utils.log_control import logger
from app.utils.module_discovery import module_discovery


class ConfigManager:
    """配置管理器"""

    def __init__(self):
        self.config_file = Path("app/config/permission_config.json")
        self.backup_dir = Path("app/config/backups")

    def generate_config(self, save_to_file: bool = True) -> Dict:
        """
        生成完整的权限配置

        Args:
            save_to_file: 是否保存到文件

        Returns:
            生成的配置字典
        """
        logger.info("🔧 开始生成权限配置...")

        # 发现模块并生成配置
        config = module_discovery.generate_permission_config()

        # 添加元数据
        config["_metadata"] = {
            "generated_at": self._get_current_timestamp(),
            "version": "1.0",
            "auto_generated": True,
            "modules_count": len(config["MODULE_TO_PARENT_MENU"]),
            "description": "自动生成的权限配置文件",
        }

        if save_to_file:
            self.save_config(config)

        logger.info("✅ 权限配置生成完成")
        return config

    def save_config(self, config: Dict, backup: bool = True) -> bool:
        """
        保存配置到文件

        Args:
            config: 配置字典
            backup: 是否备份现有配置

        Returns:
            保存是否成功
        """
        try:
            # 确保目录存在
            self.config_file.parent.mkdir(parents=True, exist_ok=True)

            # 备份现有配置
            if backup and self.config_file.exists():
                self._backup_config()

            # 保存新配置
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)

            logger.info(f"配置已保存到: {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"保存配置失败: {str(e)}")
            return False

    def load_config(self) -> Optional[Dict]:
        """
        从文件加载配置

        Returns:
            配置字典，如果加载失败返回None
        """
        try:
            if not self.config_file.exists():
                logger.warning(f"配置文件不存在: {self.config_file}")
                return None

            with open(self.config_file, "r", encoding="utf-8") as f:
                config = json.load(f)

            logger.info(f"配置已从文件加载: {self.config_file}")
            return config
        except Exception as e:
            logger.error(f"加载配置失败: {str(e)}")
            return None

    def validate_config(self, config: Optional[Dict] = None) -> Tuple[bool, List[str]]:
        """
        验证配置的完整性和一致性

        Args:
            config: 要验证的配置，如果为None则加载文件配置

        Returns:
            (是否有效, 错误信息列表)
        """
        if config is None:
            config = self.load_config()
            if config is None:
                return False, ["配置文件不存在或加载失败"]

        errors = []

        # 检查必需的配置项
        required_keys = ["MODULE_TO_PARENT_MENU", "PARENT_MENU_MAPPING", "SUB_MENU_MAPPING"]
        for key in required_keys:
            if key not in config:
                errors.append(f"缺少必需的配置项: {key}")

        if errors:
            return False, errors

        # 检查配置一致性
        module_to_parent = config["MODULE_TO_PARENT_MENU"]
        parent_mapping = config["PARENT_MENU_MAPPING"]
        sub_mapping = config["SUB_MENU_MAPPING"]

        # 检查父菜单映射的一致性
        used_parents = set(module_to_parent.values())
        defined_parents = set(parent_mapping.keys())

        missing_parents = used_parents - defined_parents
        if missing_parents:
            errors.append(f"父菜单映射中缺少定义: {missing_parents}")

        # 检查子菜单映射的一致性
        modules_in_parent = set(module_to_parent.keys())
        modules_in_sub = set(sub_mapping.keys())

        missing_in_sub = modules_in_parent - modules_in_sub
        if missing_in_sub:
            errors.append(f"子菜单映射中缺少模块: {missing_in_sub}")

        extra_in_sub = modules_in_sub - modules_in_parent
        if extra_in_sub:
            errors.append(f"子菜单映射中存在多余模块: {extra_in_sub}")

        return len(errors) == 0, errors

    def update_config(self, updates: Dict) -> bool:
        """
        更新配置

        Args:
            updates: 要更新的配置项

        Returns:
            更新是否成功
        """
        try:
            # 加载现有配置
            config = self.load_config()
            if config is None:
                logger.warning("现有配置不存在，将创建新配置")
                config = self.generate_config(save_to_file=False)

            # 应用更新
            for key, value in updates.items():
                if isinstance(value, dict) and key in config and isinstance(config[key], dict):
                    config[key].update(value)
                else:
                    config[key] = value

            # 更新元数据
            if "_metadata" not in config:
                config["_metadata"] = {}
            config["_metadata"]["last_updated"] = self._get_current_timestamp()

            # 验证更新后的配置
            is_valid, errors = self.validate_config(config)
            if not is_valid:
                logger.error(f"配置验证失败: {errors}")
                return False

            # 保存配置
            return self.save_config(config)
        except Exception as e:
            logger.error(f"更新配置失败: {str(e)}")
            return False

    def compare_with_current(self) -> Dict:
        """
        比较生成的配置与当前配置的差异

        Returns:
            差异报告
        """
        logger.info("🔍 比较配置差异...")

        # 生成新配置
        new_config = module_discovery.generate_permission_config()

        # 加载当前配置
        current_config = self.load_config()

        if current_config is None:
            return {
                "status": "no_current_config",
                "message": "当前没有配置文件，建议生成新配置",
                "new_modules": list(new_config["MODULE_TO_PARENT_MENU"].keys()),
                "new_modules_count": len(new_config["MODULE_TO_PARENT_MENU"]),
            }

        # 比较差异
        current_modules = set(current_config.get("MODULE_TO_PARENT_MENU", {}).keys())
        new_modules = set(new_config["MODULE_TO_PARENT_MENU"].keys())

        added_modules = new_modules - current_modules
        removed_modules = current_modules - new_modules

        # 检查映射变化
        mapping_changes = {}
        for module in current_modules & new_modules:
            current_parent = current_config["MODULE_TO_PARENT_MENU"].get(module)
            new_parent = new_config["MODULE_TO_PARENT_MENU"].get(module)
            if current_parent != new_parent:
                mapping_changes[module] = {"old_parent": current_parent, "new_parent": new_parent}

        return {
            "status": "compared",
            "added_modules": list(added_modules),
            "removed_modules": list(removed_modules),
            "mapping_changes": mapping_changes,
            "total_modules": len(new_modules),
            "changes_count": len(added_modules) + len(removed_modules) + len(mapping_changes),
        }

    def _backup_config(self) -> bool:
        """备份当前配置"""
        try:
            if not self.config_file.exists():
                return True

            # 确保备份目录存在
            self.backup_dir.mkdir(parents=True, exist_ok=True)

            # 生成备份文件名
            timestamp = self._get_current_timestamp().replace(":", "-").replace(" ", "_")
            backup_file = self.backup_dir / f"permission_config_{timestamp}.json"

            # 复制文件
            import shutil

            shutil.copy2(self.config_file, backup_file)

            logger.info(f"配置已备份到: {backup_file}")
            return True
        except Exception as e:
            logger.error(f"备份配置失败: {str(e)}")
            return False

    def _get_current_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime

        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def create_backup(self, name: Optional[str] = None, description: str = "") -> Optional[str]:
        """
        创建配置备份

        Args:
            name: 备份名称，如果为None则自动生成
            description: 备份描述

        Returns:
            备份文件路径，如果失败返回None
        """
        try:
            if not self.config_file.exists():
                logger.warning("配置文件不存在，无法创建备份")
                return None

            # 确保备份目录存在
            self.backup_dir.mkdir(parents=True, exist_ok=True)

            # 生成备份文件名
            timestamp = self._get_current_timestamp().replace(":", "-").replace(" ", "_")
            if name:
                backup_filename = f"permission_config_{name}_{timestamp}.json"
            else:
                backup_filename = f"permission_config_{timestamp}.json"

            backup_path = self.backup_dir / backup_filename

            # 读取当前配置
            with open(self.config_file, "r", encoding="utf-8") as f:
                config = json.load(f)

            # 添加备份元数据
            backup_metadata = {
                "backup_created_at": self._get_current_timestamp(),
                "backup_name": name or "auto",
                "backup_description": description,
                "original_config": config.get("_metadata", {}),
                "backup_version": "1.0",
            }

            config["_backup_metadata"] = backup_metadata

            # 保存备份
            with open(backup_path, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)

            logger.info(f"配置备份已创建: {backup_path}")
            return str(backup_path)
        except Exception as e:
            logger.error(f"创建备份失败: {str(e)}")
            return None

    def list_backups(self) -> List[Dict]:
        """
        列出所有备份

        Returns:
            备份信息列表
        """
        backups = []

        if not self.backup_dir.exists():
            return backups

        try:
            backup_files = list(self.backup_dir.glob("permission_config_*.json"))
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            for backup_file in backup_files:
                try:
                    with open(backup_file, "r", encoding="utf-8") as f:
                        backup_config = json.load(f)

                    backup_metadata = backup_config.get("_backup_metadata", {})
                    file_stat = backup_file.stat()

                    backup_info = {
                        "filename": backup_file.name,
                        "path": str(backup_file),
                        "created_at": backup_metadata.get("backup_created_at", "unknown"),
                        "name": backup_metadata.get("backup_name", "auto"),
                        "description": backup_metadata.get("backup_description", ""),
                        "size": file_stat.st_size,
                        "modules_count": len(backup_config.get("MODULE_TO_PARENT_MENU", {})),
                    }
                    backups.append(backup_info)
                except Exception as e:
                    logger.warning(f"读取备份文件失败 {backup_file}: {str(e)}")
                    continue

        except Exception as e:
            logger.error(f"列出备份失败: {str(e)}")

        return backups

    def restore_backup(self, backup_identifier: str, force: bool = False) -> bool:
        """
        恢复备份

        Args:
            backup_identifier: 备份标识符（文件名或备份名称）
            force: 是否强制恢复

        Returns:
            恢复是否成功
        """
        try:
            # 查找备份文件
            backup_file = self._find_backup_file(backup_identifier)
            if not backup_file:
                logger.error(f"未找到备份: {backup_identifier}")
                return False

            # 读取备份配置
            with open(backup_file, "r", encoding="utf-8") as f:
                backup_config = json.load(f)

            # 移除备份元数据
            if "_backup_metadata" in backup_config:
                del backup_config["_backup_metadata"]

            # 更新元数据
            if "_metadata" not in backup_config:
                backup_config["_metadata"] = {}
            backup_config["_metadata"]["restored_at"] = self._get_current_timestamp()
            backup_config["_metadata"]["restored_from"] = backup_file.name

            # 备份当前配置（如果存在）
            if not force and self.config_file.exists():
                current_backup = self.create_backup(name="before_restore", description="恢复前自动备份")
                if current_backup:
                    logger.info(f"当前配置已备份到: {current_backup}")

            # 恢复配置
            success = self.save_config(backup_config, backup=False)

            if success:
                logger.info(f"配置已从备份恢复: {backup_file.name}")
                return True
            else:
                logger.error("恢复配置失败")
                return False

        except Exception as e:
            logger.error(f"恢复备份失败: {str(e)}")
            return False

    def _find_backup_file(self, identifier: str) -> Optional[Path]:
        """查找备份文件"""
        if not self.backup_dir.exists():
            return None

        # 首先尝试直接匹配文件名
        direct_path = self.backup_dir / identifier
        if direct_path.exists():
            return direct_path

        # 如果不是完整文件名，尝试模糊匹配
        backup_files = list(self.backup_dir.glob("permission_config_*.json"))

        # 按名称匹配
        for backup_file in backup_files:
            try:
                with open(backup_file, "r", encoding="utf-8") as f:
                    backup_config = json.load(f)
                backup_metadata = backup_config.get("_backup_metadata", {})
                if backup_metadata.get("backup_name") == identifier:
                    return backup_file
            except:
                continue

        # 按文件名部分匹配
        for backup_file in backup_files:
            if identifier in backup_file.name:
                return backup_file

        return None

    def get_config_status(self) -> Dict:
        """
        获取配置状态信息

        Returns:
            配置状态字典
        """
        status = {
            "config_file_exists": self.config_file.exists(),
            "config_file_path": str(self.config_file),
            "backup_dir_exists": self.backup_dir.exists(),
            "backup_count": 0,
        }

        if self.backup_dir.exists():
            backup_files = list(self.backup_dir.glob("permission_config_*.json"))
            status["backup_count"] = len(backup_files)
            status["latest_backup"] = max(backup_files, key=os.path.getctime).name if backup_files else None

        if status["config_file_exists"]:
            config = self.load_config()
            if config:
                metadata = config.get("_metadata", {})
                status["config_version"] = metadata.get("version", "unknown")
                status["generated_at"] = metadata.get("generated_at", "unknown")
                status["modules_count"] = metadata.get("modules_count", 0)
                status["auto_generated"] = metadata.get("auto_generated", False)

                # 验证配置
                is_valid, errors = self.validate_config(config)
                status["is_valid"] = is_valid
                status["validation_errors"] = errors

        return status


config_manager = ConfigManager()
