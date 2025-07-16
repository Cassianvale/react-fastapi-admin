from fastapi.routing import APIRoute

from app.core.crud import CRUDBase
from app.utils.log_control import logger
from app.models.admin import Api
from app.models.enums import MethodType
from app.schemas.apis import ApiCreate, ApiUpdate


class ApiController(CRUDBase[Api, ApiCreate, ApiUpdate]):
    def __init__(self):
        super().__init__(model=Api)

    async def refresh_api(self):
        from app import app

        # 删除废弃API数据
        all_api_list = []
        for route in app.routes:
            # 只更新有鉴权的API
            if isinstance(route, APIRoute) and len(route.dependencies) > 0:
                all_api_list.append((list(route.methods)[0], route.path_format))
        delete_api = []
        for api in await Api.all():
            if (api.method, api.path) not in all_api_list:
                delete_api.append((api.method, api.path))
        for item in delete_api:
            method, path = item
            logger.debug(f"API Deleted {method} {path}")
            await Api.filter(method=method, path=path).delete()

        for route in app.routes:
            if isinstance(route, APIRoute) and len(route.dependencies) > 0:
                method = list(route.methods)[0]
                path = route.path_format
                summary = route.summary or ""
                # 安全获取标签，如果没有标签则使用默认值
                tags = list(route.tags)[0] if route.tags else "未分类"
                api_obj = await Api.filter(method=method, path=path).first()
                if api_obj:
                    await api_obj.update_from_dict(dict(method=method, path=path, summary=summary, tags=tags)).save()
                else:
                    logger.debug(f"API Created {method} {path}")
                    # 修复：正确创建API对象，确保method字段类型正确
                    await Api.create(
                        method=MethodType(method),  # 确保正确的枚举类型
                        path=path,
                        summary=summary,
                        tags=tags
                    )


api_controller = ApiController()
