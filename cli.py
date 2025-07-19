#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
权限配置管理CLI命令行工具

提供权限配置的生成、验证、更新等功能
"""

import asyncio
import argparse
import sys
import json
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from app.utils.module_discovery import module_discovery
from app.utils.config_manager import config_manager
from app.utils.log_control import logger


class PermissionManager:
    """权限管理命令行工具"""

    def __init__(self):
        self.parser = self._create_parser()

    def _create_parser(self):
        """创建命令行参数解析器"""
        parser = argparse.ArgumentParser(
            description="权限配置管理工具",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
示例用法:
  python cli.py discover              # 发现API模块
  python cli.py generate              # 生成权限配置
  python cli.py validate              # 验证配置
  python cli.py status                # 查看配置状态
  python cli.py compare               # 比较配置差异
  python cli.py update --auto         # 自动更新配置
  python cli.py backup                # 创建配置备份
  python cli.py backup --list         # 列出所有备份
  python cli.py restore --list        # 列出可用备份
  python cli.py restore --latest      # 恢复最新备份
  python cli.py restore backup_name   # 恢复指定备份
            """,
        )

        subparsers = parser.add_subparsers(dest="command", help="可用命令")

        # discover 命令
        discover_parser = subparsers.add_parser("discover", help="发现API模块")
        discover_parser.add_argument("--output", "-o", help="输出文件路径")
        discover_parser.add_argument("--format", choices=["json", "table"], default="table", help="输出格式")

        # generate 命令
        generate_parser = subparsers.add_parser("generate", help="生成权限配置")
        generate_parser.add_argument("--force", "-f", action="store_true", help="强制覆盖现有配置")
        generate_parser.add_argument("--backup", "-b", action="store_true", default=True, help="备份现有配置")

        # validate 命令
        validate_parser = subparsers.add_parser("validate", help="验证权限配置")
        validate_parser.add_argument("--config", "-c", help="配置文件路径")

        # status 命令
        subparsers.add_parser("status", help="查看配置状态")

        # compare 命令
        compare_parser = subparsers.add_parser("compare", help="比较配置差异")
        compare_parser.add_argument("--show-details", "-d", action="store_true", help="显示详细差异")

        # update 命令
        update_parser = subparsers.add_parser("update", help="更新权限配置")
        update_parser.add_argument("--auto", "-a", action="store_true", help="自动更新（添加新发现的模块）")
        update_parser.add_argument("--module", "-m", help="更新特定模块的配置")

        # backup 命令
        backup_parser = subparsers.add_parser("backup", help="备份权限配置")
        backup_parser.add_argument("--name", "-n", help="备份名称（可选）")
        backup_parser.add_argument("--description", "-d", help="备份描述")
        backup_parser.add_argument("--list", "-l", action="store_true", help="列出所有备份")

        # restore 命令
        restore_parser = subparsers.add_parser("restore", help="恢复权限配置")
        restore_parser.add_argument("backup_name", nargs="?", help="要恢复的备份名称")
        restore_parser.add_argument("--list", "-l", action="store_true", help="列出可用的备份")
        restore_parser.add_argument("--latest", action="store_true", help="恢复最新备份")
        restore_parser.add_argument("--force", "-f", action="store_true", help="强制恢复（不询问确认）")

        return parser

    async def run(self):
        """运行命令行工具"""
        args = self.parser.parse_args()

        if not args.command:
            self.parser.logger.debug_help()
            return

        try:
            if args.command == "discover":
                await self.cmd_discover(args)
            elif args.command == "generate":
                await self.cmd_generate(args)
            elif args.command == "validate":
                await self.cmd_validate(args)
            elif args.command == "status":
                await self.cmd_status(args)
            elif args.command == "compare":
                await self.cmd_compare(args)
            elif args.command == "update":
                await self.cmd_update(args)
            elif args.command == "backup":
                await self.cmd_backup(args)
            elif args.command == "restore":
                await self.cmd_restore(args)
        except Exception as e:
            logger.debug(f"❌ 命令执行失败: {str(e)}")
            sys.exit(1)

    async def cmd_discover(self, args):
        """发现API模块命令"""
        logger.debug("🔍 正在发现API模块...")

        modules = module_discovery.discover_api_modules()

        if args.format == "json":
            output = json.dumps(modules, ensure_ascii=False, indent=2)
            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(output)
                logger.debug(f"✅ 结果已保存到: {args.output}")
            else:
                logger.debug(output)
        else:
            # 表格格式输出
            logger.debug(f"\n📊 发现 {len(modules)} 个API模块:")
            logger.debug("-" * 80)
            logger.debug(f"{'模块名称':<15} {'路由数量':<10} {'标签':<20} {'描述'}")
            logger.debug("-" * 80)

            for name, info in modules.items():
                tags = ", ".join(info.get("tags", []))[:18]
                desc = info.get("description", "")[:30]
                if len(desc) > 30:
                    desc = desc[:27] + "..."
                logger.debug(f"{name:<15} {len(info.get('routes', [])):<10} {tags:<20} {desc}")

    async def cmd_generate(self, args):
        """生成权限配置命令"""
        logger.debug("🔧 正在生成权限配置...")

        # 检查现有配置
        if not args.force:
            status = config_manager.get_config_status()
            if status["config_file_exists"]:
                response = input("⚠️  配置文件已存在，是否覆盖？(y/N): ")
                if response.lower() != "y":
                    logger.debug("❌ 操作已取消")
                    return

        # 生成配置
        config = config_manager.generate_config(save_to_file=True)

        logger.debug("✅ 权限配置生成完成!")
        logger.debug(f"📁 配置文件: {config_manager.config_file}")
        logger.debug(f"📊 模块数量: {len(config['MODULE_TO_PARENT_MENU'])}")

        # 显示生成的模块
        logger.debug("\n📋 包含的模块:")
        for module, parent in config["MODULE_TO_PARENT_MENU"].items():
            sub_name = config["SUB_MENU_MAPPING"].get(module, module)
            parent_info = config["PARENT_MENU_MAPPING"].get(parent, {})
            parent_name = parent_info.get("name", parent)
            logger.debug(f"  - {module} → {parent_name} → {sub_name}")

    async def cmd_validate(self, args):
        """验证权限配置命令"""
        logger.debug("🔍 正在验证权限配置...")

        config = None
        if args.config:
            # 验证指定的配置文件
            try:
                with open(args.config, "r", encoding="utf-8") as f:
                    config = json.load(f)
                logger.debug(f"📁 验证配置文件: {args.config}")
            except Exception as e:
                logger.debug(f"❌ 无法加载配置文件: {str(e)}")
                return

        is_valid, errors = config_manager.validate_config(config)

        if is_valid:
            logger.debug("✅ 配置验证通过!")
        else:
            logger.debug("❌ 配置验证失败:")
            for error in errors:
                logger.debug(f"  - {error}")

    async def cmd_status(self, args):
        """查看配置状态命令"""
        logger.debug("📊 权限配置状态:")
        logger.debug("=" * 50)

        status = config_manager.get_config_status()

        # 基本信息
        logger.debug(f"配置文件存在: {'✅' if status['config_file_exists'] else '❌'}")
        logger.debug(f"配置文件路径: {status['config_file_path']}")

        if status["config_file_exists"]:
            logger.debug(f"配置版本: {status.get('config_version', 'unknown')}")
            logger.debug(f"生成时间: {status.get('generated_at', 'unknown')}")
            logger.debug(f"模块数量: {status.get('modules_count', 0)}")
            logger.debug(f"自动生成: {'✅' if status.get('auto_generated') else '❌'}")
            logger.debug(f"配置有效: {'✅' if status.get('is_valid') else '❌'}")

            if not status.get("is_valid"):
                logger.debug("验证错误:")
                for error in status.get("validation_errors", []):
                    logger.debug(f"  - {error}")

        # 备份信息
        logger.debug(f"\n备份目录存在: {'✅' if status['backup_dir_exists'] else '❌'}")
        logger.debug(f"备份数量: {status['backup_count']}")
        if status.get("latest_backup"):
            logger.debug(f"最新备份: {status['latest_backup']}")

    async def cmd_compare(self, args):
        """比较配置差异命令"""
        logger.debug("🔍 正在比较配置差异...")

        diff = config_manager.compare_with_current()

        if diff["status"] == "no_current_config":
            logger.debug("⚠️  当前没有配置文件")
            logger.debug(f"📊 发现 {diff['new_modules_count']} 个新模块:")
            for module in diff["new_modules"]:
                logger.debug(f"  + {module}")
            logger.debug("\n💡 建议运行: python cli.py generate")
            return

        changes_count = diff["changes_count"]
        if changes_count == 0:
            logger.debug("✅ 配置无变化，当前配置是最新的")
            return

        logger.debug(f"📊 发现 {changes_count} 个变化:")

        # 新增模块
        if diff["added_modules"]:
            logger.debug(f"\n➕ 新增模块 ({len(diff['added_modules'])}个):")
            for module in diff["added_modules"]:
                logger.debug(f"  + {module}")

        # 删除模块
        if diff["removed_modules"]:
            logger.debug(f"\n➖ 删除模块 ({len(diff['removed_modules'])}个):")
            for module in diff["removed_modules"]:
                logger.debug(f"  - {module}")

        # 映射变化
        if diff["mapping_changes"]:
            logger.debug(f"\n🔄 映射变化 ({len(diff['mapping_changes'])}个):")
            for module, change in diff["mapping_changes"].items():
                logger.debug(f"  ~ {module}: {change['old_parent']} → {change['new_parent']}")

        if changes_count > 0:
            logger.debug("\n💡 建议运行: python cli.py update --auto")

    async def cmd_update(self, args):
        """更新权限配置命令"""
        if args.auto:
            logger.debug("🔄 正在自动更新权限配置...")

            # 比较差异
            diff = config_manager.compare_with_current()

            if diff["changes_count"] == 0:
                logger.debug("✅ 配置已是最新，无需更新")
                return

            # 生成新配置
            new_config = module_discovery.generate_permission_config()

            # 更新配置
            success = config_manager.update_config(new_config)

            if success:
                logger.debug("✅ 配置更新成功!")
                logger.debug(f"📊 更新了 {diff['changes_count']} 个变化")
            else:
                logger.debug("❌ 配置更新失败")

        elif args.module:
            logger.debug(f"🔄 正在更新模块 {args.module} 的配置...")
            # TODO: 实现单个模块更新
            logger.debug("⚠️  单个模块更新功能待实现")

        else:
            logger.debug("❌ 请指定更新方式: --auto 或 --module <模块名>")

    async def cmd_backup(self, args):
        """备份权限配置命令"""
        if args.list:
            # 列出所有备份
            print("📋 权限配置备份列表:")
            print("=" * 80)

            backups = config_manager.list_backups()
            if not backups:
                print("📭 暂无备份文件")
                return

            print(f"{'备份名称':<20} {'创建时间':<20} {'模块数':<8} {'大小':<10} {'描述'}")
            print("-" * 80)

            for backup in backups:
                size_kb = backup["size"] / 1024
                size_str = f"{size_kb:.1f}KB"
                desc = backup["description"][:30] if backup["description"] else "无描述"
                print(
                    f"{backup['name']:<20} {backup['created_at']:<20} {backup['modules_count']:<8} {size_str:<10} {desc}"
                )

            print(f"\n📊 总计: {len(backups)} 个备份")
            return

        # 创建备份
        print("💾 正在创建权限配置备份...")

        backup_path = config_manager.create_backup(name=args.name, description=args.description or "")

        if backup_path:
            print("✅ 备份创建成功!")
            print(f"📁 备份文件: {backup_path}")

            # 显示备份信息
            backups = config_manager.list_backups()
            if backups:
                latest_backup = backups[0]  # 最新的备份
                print(f"📊 备份信息:")
                print(f"  - 备份名称: {latest_backup['name']}")
                print(f"  - 创建时间: {latest_backup['created_at']}")
                print(f"  - 模块数量: {latest_backup['modules_count']}")
                print(f"  - 文件大小: {latest_backup['size'] / 1024:.1f}KB")
        else:
            print("❌ 备份创建失败")

    async def cmd_restore(self, args):
        """恢复权限配置命令"""
        if args.list:
            # 列出可用备份
            print("📋 可用的权限配置备份:")
            print("=" * 80)

            backups = config_manager.list_backups()
            if not backups:
                print("📭 暂无备份文件")
                print("\n💡 提示: 使用 'python cli.py backup' 创建备份")
                return

            print(f"{'序号':<4} {'备份名称':<20} {'创建时间':<20} {'模块数':<8} {'描述'}")
            print("-" * 80)

            for i, backup in enumerate(backups, 1):
                desc = backup["description"][:30] if backup["description"] else "无描述"
                print(f"{i:<4} {backup['name']:<20} {backup['created_at']:<20} {backup['modules_count']:<8} {desc}")

            print(f"\n💡 使用方式: python cli.py restore <备份名称>")
            return

        # 确定要恢复的备份
        backup_identifier = None

        if args.latest:
            # 恢复最新备份
            backups = config_manager.list_backups()
            if not backups:
                print("❌ 没有可用的备份")
                return
            backup_identifier = backups[0]["name"]
            print(f"🔄 准备恢复最新备份: {backup_identifier}")
        elif args.backup_name:
            backup_identifier = args.backup_name
            print(f"🔄 准备恢复备份: {backup_identifier}")
        else:
            print("❌ 请指定要恢复的备份名称或使用 --latest 恢复最新备份")
            print("💡 使用 'python cli.py restore --list' 查看可用备份")
            return

        # 确认恢复操作
        if not args.force:
            # 显示当前配置状态
            status = config_manager.get_config_status()
            if status["config_file_exists"]:
                print("⚠️  当前配置信息:")
                print(f"  - 配置版本: {status.get('config_version', 'unknown')}")
                print(f"  - 生成时间: {status.get('generated_at', 'unknown')}")
                print(f"  - 模块数量: {status.get('modules_count', 0)}")
                print("  - 当前配置将被自动备份")

            response = input("\n确认恢复配置？(y/N): ")
            if response.lower() != "y":
                print("❌ 恢复操作已取消")
                return

        # 执行恢复
        print("🔄 正在恢复权限配置...")

        success = config_manager.restore_backup(backup_identifier, force=args.force)

        if success:
            print("✅ 配置恢复成功!")
            print("🔄 请重启应用以使配置生效")

            # 显示恢复后的状态
            print("\n📊 恢复后配置状态:")
            status = config_manager.get_config_status()
            print(f"  - 模块数量: {status.get('modules_count', 0)}")
            if "_metadata" in config_manager.load_config() or {}:
                metadata = config_manager.load_config().get("_metadata", {})
                print(f"  - 恢复时间: {metadata.get('restored_at', 'unknown')}")
                print(f"  - 来源备份: {metadata.get('restored_from', 'unknown')}")
        else:
            print("❌ 配置恢复失败")


async def main():
    """主函数"""
    manager = PermissionManager()
    await manager.run()


if __name__ == "__main__":
    asyncio.run(main())
