from typing import Any, Dict, Generic, List, NewType, Optional, Tuple, Type, TypeVar, Union

from pydantic import BaseModel
from tortoise.expressions import Q
from tortoise.models import Model

from app.core.exceptions import RecordNotFoundError, InvalidParameterError

Total = NewType("Total", int)
ModelType = TypeVar("ModelType", bound=Model)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get(self, id: int) -> Optional[ModelType]:
        """获取记录，如果不存在返回None"""
        return await self.model.get_or_none(id=id)

    async def get_or_raise(self, id: int) -> ModelType:
        """获取记录，如果不存在抛出异常"""
        obj = await self.model.get_or_none(id=id)
        if obj is None:
            raise RecordNotFoundError(detail=f"{self.model.__name__} with id {id} not found")
        return obj

    async def list(
        self,
        page: int,
        page_size: int,
        search: Q = Q(),
        order: list | None = None,
        prefetch_related: list[str] | None = None,
        select_related: list[str] | None = None,
    ) -> Tuple[Total, List[ModelType]]:
        """
        获取分页列表，包含参数验证和关联查询优化

        Args:
            page: 页码，从1开始
            page_size: 每页数量，最大1000
            search: 查询条件
            order: 排序字段列表
            prefetch_related: 预取多对多和反向外键关联（解决N+1问题）
            select_related: 预取外键关联（JOIN查询）
        """
        # 参数验证
        if page < 1:
            raise InvalidParameterError(detail="页码必须大于0")
        if page_size < 1:
            raise InvalidParameterError(detail="页面大小必须大于0")
        if page_size > 1000:
            raise InvalidParameterError(detail="页面大小不能超过1000")

        if order is None:
            order = []
        if prefetch_related is None:
            prefetch_related = []
        if select_related is None:
            select_related = []

        # 构建查询
        query = self.model.filter(search)

        # 获取总数（不需要关联查询优化）
        total = await query.count()

        # 获取分页数据，应用关联查询优化
        items_query = query.offset((page - 1) * page_size).limit(page_size).order_by(*order)

        # 应用 select_related (外键关联，使用 JOIN)
        if select_related:
            items_query = items_query.select_related(*select_related)

        # 应用 prefetch_related (多对多和反向外键，使用额外查询)
        if prefetch_related:
            items = await items_query.prefetch_related(*prefetch_related)
        else:
            items = await items_query

        return Total(total), items

    async def create(self, obj_in: CreateSchemaType) -> ModelType:
        """创建新记录"""
        if isinstance(obj_in, Dict):
            obj_dict = obj_in
        else:
            obj_dict = obj_in.model_dump()
        obj = self.model(**obj_dict)
        await obj.save()
        return obj

    async def update(self, id: int, obj_in: Union[UpdateSchemaType, Dict[str, Any]]) -> ModelType:
        """更新记录，如果记录不存在抛出异常"""
        obj = await self.get_or_raise(id=id)

        if isinstance(obj_in, Dict):
            obj_dict = obj_in
        else:
            obj_dict = obj_in.model_dump(exclude_unset=True, exclude={"id"})

        obj = obj.update_from_dict(obj_dict)
        await obj.save()
        return obj

    async def remove(self, id: int) -> ModelType:
        """删除记录，如果记录不存在抛出异常，返回被删除的对象"""
        obj = await self.get_or_raise(id=id)
        deleted_obj = obj  # 保存引用用于返回
        await obj.delete()
        return deleted_obj
