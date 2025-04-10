from tortoise.expressions import Q
from tortoise.transactions import atomic

from app.core.crud import CRUDBase
from app.models.admin import Dept, DeptClosure
from app.schemas.depts import DeptCreate, DeptUpdate


class DeptController(CRUDBase[Dept, DeptCreate, DeptUpdate]):
    def __init__(self):
        super().__init__(model=Dept)

    async def get_dept_tree(self, name):
        q = Q()
        if name:
            q &= Q(name__contains=name)
        all_depts = await self.model.filter(q).order_by("order")

        # 辅助函数，用于递归构建部门树
        def build_tree(parent_id):
            return [
                {
                    "id": dept.id,
                    "name": dept.name,
                    "desc": dept.desc,
                    "order": dept.order,
                    "parent_id": dept.parent_id,
                    "children": build_tree(dept.id),  # 递归构建子部门
                }
                for dept in all_depts
                if dept.parent_id == parent_id
            ]

        # 从顶级部门（parent_id=0）开始构建部门树
        dept_tree = build_tree(0)
        return dept_tree

    async def get_dept_info(self):
        pass

    async def update_dept_closure(self, obj: Dept):
        parent_depts = await DeptClosure.filter(descendant=obj.parent_id)
        dept_closure_objs: list[DeptClosure] = []
        # 插入父级关系
        for item in parent_depts:
            dept_closure_objs.append(DeptClosure(ancestor=item.ancestor, descendant=obj.id, level=item.level + 1))
        # 插入自身
        dept_closure_objs.append(DeptClosure(ancestor=obj.id, descendant=obj.id, level=0))
        # 创建关系
        await DeptClosure.bulk_create(dept_closure_objs)

    @atomic()
    async def create_dept(self, obj_in: DeptCreate):
        # 检查部门名称是否已存在
        exists = await self.model.filter(name=obj_in.name).exists()
        if exists:
            raise ValueError(f"部门名称 '{obj_in.name}' 已存在")
            
        # 创建新部门
        if obj_in.parent_id != 0:
            await self.get(id=obj_in.parent_id)
        new_obj = await self.create(obj_in=obj_in)
        await self.update_dept_closure(new_obj)
        return new_obj

    @atomic()
    async def update_dept(self, obj_in: DeptUpdate):
        dept_obj = await self.get(id=obj_in.id)
        
        # 如果部门名称发生变化，需要检查名称是否重复
        if dept_obj.name != obj_in.name:
            # 检查是否存在同名部门
            same_name_dept = await self.model.filter(name=obj_in.name).exclude(id=obj_in.id).exists()
            if same_name_dept:
                raise ValueError(f"部门名称 '{obj_in.name}' 已存在")
        
        # 更新部门关系
        if dept_obj.parent_id != obj_in.parent_id:
            await DeptClosure.filter(ancestor=dept_obj.id).delete()
            await DeptClosure.filter(descendant=dept_obj.id).delete()
            # 设置新的parent_id
            dept_obj.parent_id = obj_in.parent_id
            await dept_obj.save()
            await self.update_dept_closure(dept_obj)
            
        # 更新部门其他信息
        dept_obj.name = obj_in.name
        dept_obj.desc = obj_in.desc
        dept_obj.order = obj_in.order
        await dept_obj.save()
        
        return dept_obj

    async def get_child_dept_ids(self, dept_id: int) -> list[int]:
        """获取指定部门的所有子部门ID（包括自身）"""
        # 通过DeptClosure表查询所有以dept_id为祖先的部门
        child_relations = await DeptClosure.filter(ancestor=dept_id).values_list('descendant', flat=True)
        return list(child_relations)

    @atomic()
    async def delete_dept(self, dept_id: int, cascade: bool = True):
        """
        删除部门
        :param dept_id: 部门ID
        :param cascade: 是否级联删除子部门，默认为True
        """
        # 获取需要删除的部门对象
        dept = await self.get(id=dept_id)
        
        if cascade:
            # 获取所有子部门ID（包括自身）
            dept_ids = await self.get_child_dept_ids(dept_id)
            
            # 删除关系表中的所有相关记录
            for child_id in dept_ids:
                await DeptClosure.filter(descendant=child_id).delete()
                await DeptClosure.filter(ancestor=child_id).delete()
            
            # 物理删除所有相关部门
            await Dept.filter(id__in=dept_ids).delete()
        else:
            # 检查是否有子部门
            child_depts = await self.get_child_dept_ids(dept_id)
            if len(child_depts) > 1:  # 大于1是因为包含自身
                raise ValueError("该部门下有子部门，不能单独删除。请使用级联删除或先删除子部门")
                
            # 删除关系
            await DeptClosure.filter(descendant=dept_id).delete()
            await DeptClosure.filter(ancestor=dept_id).delete()
            
            # 物理删除当前部门
            await dept.delete()


dept_controller = DeptController()
