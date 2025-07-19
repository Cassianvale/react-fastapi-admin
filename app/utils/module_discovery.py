"""
API模块自动发现和配置生成工具

自动扫描API模块，生成权限配置，减少手动配置工作
"""

import os
import ast
import importlib
from typing import Dict, List, Set, Optional, Tuple
from pathlib import Path

from app.utils.log_control import logger


class ModuleDiscovery:
    """API模块自动发现器"""
    
    def __init__(self, api_base_path: str = "app/api/v1"):
        self.api_base_path = Path(api_base_path)
        self.discovered_modules = {}
        self.module_configs = {}
    
    def discover_api_modules(self) -> Dict[str, Dict]:
        """
        自动发现API模块
        
        Returns:
            发现的模块信息字典
        """
        logger.info("🔍 开始自动发现API模块...")
        
        modules = {}
        
        # 扫描API目录
        if not self.api_base_path.exists():
            logger.warning(f"API目录不存在: {self.api_base_path}")
            return modules
        
        for item in self.api_base_path.iterdir():
            if item.is_dir() and not item.name.startswith('_'):
                module_info = self._analyze_module(item)
                if module_info:
                    modules[item.name] = module_info
                    logger.debug(f"发现模块: {item.name}")
        
        self.discovered_modules = modules
        logger.info(f"✅ 发现 {len(modules)} 个API模块")
        return modules
    
    def _analyze_module(self, module_path: Path) -> Optional[Dict]:
        """分析单个模块"""
        try:
            # 查找模块的主路由文件
            main_file = None
            for file_name in [f"{module_path.name}.py", "routes.py", "__init__.py"]:
                file_path = module_path / file_name
                if file_path.exists():
                    main_file = file_path
                    break
            
            if not main_file:
                return None
            
            # 解析文件获取路由信息
            routes_info = self._parse_routes_file(main_file)
            
            return {
                "name": module_path.name,
                "path": str(module_path),
                "main_file": str(main_file),
                "routes": routes_info["routes"],
                "tags": routes_info["tags"],
                "description": routes_info["description"]
            }
        except Exception as e:
            logger.error(f"分析模块失败 {module_path.name}: {str(e)}")
            return None
    
    def _parse_routes_file(self, file_path: Path) -> Dict:
        """解析路由文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            routes = []
            tags = set()
            description = ""
            
            # 遍历AST节点
            for node in ast.walk(tree):
                # 查找路由装饰器
                if isinstance(node, ast.FunctionDef):
                    route_info = self._extract_route_info(node)
                    if route_info:
                        routes.append(route_info)
                        if route_info.get("tags"):
                            tags.update(route_info["tags"])
                
                # 查找模块描述
                if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
                    if isinstance(node.value.value, str) and len(node.value.value) > 10:
                        description = node.value.value.strip()
            
            return {
                "routes": routes,
                "tags": list(tags),
                "description": description
            }
        except Exception as e:
            logger.error(f"解析路由文件失败 {file_path}: {str(e)}")
            return {"routes": [], "tags": [], "description": ""}
    
    def _extract_route_info(self, func_node: ast.FunctionDef) -> Optional[Dict]:
        """从函数节点提取路由信息"""
        route_info = {
            "function_name": func_node.name,
            "methods": [],
            "path": "",
            "summary": "",
            "tags": []
        }
        
        # 查找装饰器
        for decorator in func_node.decorator_list:
            if isinstance(decorator, ast.Call):
                # 处理 @router.get(), @router.post() 等
                if (isinstance(decorator.func, ast.Attribute) and 
                    isinstance(decorator.func.value, ast.Name) and
                    decorator.func.value.id == "router"):
                    
                    method = decorator.func.attr.upper()
                    route_info["methods"].append(method)
                    
                    # 提取路径和其他参数
                    for i, arg in enumerate(decorator.args):
                        if i == 0 and isinstance(arg, ast.Constant):
                            route_info["path"] = arg.value
                    
                    # 提取关键字参数
                    for keyword in decorator.keywords:
                        if keyword.arg == "summary" and isinstance(keyword.value, ast.Constant):
                            route_info["summary"] = keyword.value.value
                        elif keyword.arg == "tags" and isinstance(keyword.value, ast.List):
                            tags = []
                            for tag in keyword.value.elts:
                                if isinstance(tag, ast.Constant):
                                    tags.append(tag.value)
                            route_info["tags"] = tags
        
        return route_info if route_info["methods"] else None
    
    def generate_permission_config(self) -> Dict[str, Dict]:
        """
        基于发现的模块生成权限配置
        
        Returns:
            生成的权限配置
        """
        if not self.discovered_modules:
            self.discover_api_modules()
        
        logger.info("🔧 生成权限配置...")
        
        # 默认的父菜单映射规则
        default_parent_menu_rules = {
            "base": "personal",
            "auth": "personal", 
            "profile": "personal",
            "user": "system",
            "role": "system",
            "menu": "system",
            "api": "system",
            "dept": "system",
            "permission": "system",
            "auditlog": "monitor",
            "log": "monitor",
            "monitor": "monitor",
            "upload": "resource",
            "file": "resource",
            "storage": "resource"
        }
        
        # 生成模块到父菜单的映射
        module_to_parent_menu = {}
        parent_menu_mapping = {
            "personal": {"name": "个人中心", "desc": "个人信息和设置相关功能"},
            "system": {"name": "系统管理", "desc": "系统配置和管理功能"},
            "monitor": {"name": "监控管理", "desc": "系统监控和日志管理"},
            "resource": {"name": "资源管理", "desc": "文件和资源管理功能"},
        }
        
        # 生成子菜单映射
        sub_menu_mapping = {}
        
        for module_name, module_info in self.discovered_modules.items():
            # 确定父菜单
            parent_menu = self._determine_parent_menu(module_name, module_info, default_parent_menu_rules)
            module_to_parent_menu[module_name] = parent_menu
            
            # 生成子菜单名称
            sub_menu_name = self._generate_sub_menu_name(module_name, module_info)
            sub_menu_mapping[module_name] = sub_menu_name
        
        config = {
            "MODULE_TO_PARENT_MENU": module_to_parent_menu,
            "PARENT_MENU_MAPPING": parent_menu_mapping,
            "SUB_MENU_MAPPING": sub_menu_mapping
        }
        
        self.module_configs = config
        logger.info("✅ 权限配置生成完成")
        return config
    
    def _determine_parent_menu(self, module_name: str, module_info: Dict, rules: Dict) -> str:
        """确定模块的父菜单"""
        # 1. 优先使用预定义规则
        if module_name in rules:
            return rules[module_name]
        
        # 2. 根据模块标签推断
        tags = module_info.get("tags", [])
        for tag in tags:
            tag_lower = tag.lower()
            if any(keyword in tag_lower for keyword in ["用户", "角色", "权限", "系统", "管理"]):
                return "system"
            elif any(keyword in tag_lower for keyword in ["个人", "profile", "auth"]):
                return "personal"
            elif any(keyword in tag_lower for keyword in ["监控", "日志", "log"]):
                return "monitor"
            elif any(keyword in tag_lower for keyword in ["文件", "上传", "资源"]):
                return "resource"
        
        # 3. 根据模块名称推断
        name_lower = module_name.lower()
        if any(keyword in name_lower for keyword in ["user", "role", "permission", "admin"]):
            return "system"
        elif any(keyword in name_lower for keyword in ["log", "audit", "monitor"]):
            return "monitor"
        elif any(keyword in name_lower for keyword in ["file", "upload", "storage"]):
            return "resource"
        
        # 4. 默认归类到系统管理
        return "system"
    
    def _generate_sub_menu_name(self, module_name: str, module_info: Dict) -> str:
        """生成子菜单名称"""
        # 预定义的名称映射
        predefined_names = {
            "base": "个人设置",
            "user": "用户管理",
            "role": "角色管理",
            "menu": "菜单管理",
            "api": "API管理",
            "dept": "部门管理",
            "auditlog": "审计日志",
            "upload": "文件管理",
            "auth": "身份认证",
            "permission": "权限管理",
            "log": "系统日志",
            "monitor": "系统监控",
            "file": "文件管理",
            "storage": "存储管理"
        }
        
        if module_name in predefined_names:
            return predefined_names[module_name]
        
        # 尝试从标签中提取名称
        tags = module_info.get("tags", [])
        if tags:
            # 使用第一个标签作为名称
            return tags[0]
        
        # 默认生成名称
        return f"{module_name.title()}管理"


module_discovery = ModuleDiscovery()
