from typing import Any, Dict, Generic, List, NewType, Optional, Tuple, Type, TypeVar, Union

from pydantic import BaseModel
from tortoise.expressions import Q
from tortoise.models import Model

Total = NewType("Total", int)
ModelType = TypeVar("ModelType", bound=Model)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get(self, id: int) -> Optional[ModelType]:
        return await self.model.get_or_none(id=id)

    async def list(self, page: int, page_size: int, search: Q = Q(), order: list = None) -> Tuple[Total, List[ModelType]]:
        if order is None:
            order = []
        query = self.model.filter(search)
        return await query.count(), await query.offset((page - 1) * page_size).limit(page_size).order_by(*order)

    async def create(self, obj_in: CreateSchemaType) -> ModelType:
        if isinstance(obj_in, Dict):
            obj_dict = obj_in
        else:
            obj_dict = obj_in.model_dump()
        obj = self.model(**obj_dict)
        await obj.save()
        return obj

    async def update(self, id: int, obj_in: Union[UpdateSchemaType, Dict[str, Any]]) -> Optional[ModelType]:
        obj = await self.get(id=id)
        if obj is None:
            return None
            
        if isinstance(obj_in, Dict):
            obj_dict = obj_in
        else:
            obj_dict = obj_in.model_dump(exclude_unset=True, exclude={"id"})
            
        obj = obj.update_from_dict(obj_dict)
        await obj.save()
        return obj

    async def remove(self, id: int) -> bool:
        obj = await self.get(id=id)
        if obj is None:
            return False
            
        await obj.delete()
        return True
