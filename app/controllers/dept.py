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
        # 获取所有未被软删除的部门
        q &= Q(is_deleted=False)
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
        for i in parent_depts:
            print(i.ancestor, i.descendant)
        dept_closure_objs: list[DeptClosure] = []
        # 插入父级关系
        for item in parent_depts:
            dept_closure_objs.append(DeptClosure(ancestor=item.ancestor, descendant=obj.id, level=item.level + 1))
        # 插入自身x
        dept_closure_objs.append(DeptClosure(ancestor=obj.id, descendant=obj.id, level=0))
        # 创建关系
        await DeptClosure.bulk_create(dept_closure_objs)

    @atomic()
    async def create_dept(self, obj_in: DeptCreate):
        # 检查是否存在同名的已删除部门
        existing_dept = await self.model.filter(name=obj_in.name, is_deleted=True).first()
        
        if existing_dept:
            # 如果存在同名已删除部门，恢复该部门
            print(f"恢复已删除的部门: {existing_dept.name}, ID: {existing_dept.id}")
            existing_dept.is_deleted = False
            existing_dept.desc = obj_in.desc
            existing_dept.order = obj_in.order
            existing_dept.parent_id = obj_in.parent_id
            await existing_dept.save()
            
            # 重新创建部门关系
            await DeptClosure.filter(ancestor=existing_dept.id).delete()
            await DeptClosure.filter(descendant=existing_dept.id).delete()
            await self.update_dept_closure(existing_dept)
            
            return existing_dept
        else:
            # 创建新部门
            if obj_in.parent_id != 0:
                await self.get(id=obj_in.parent_id)
            new_obj = await self.create(obj_in=obj_in)
            await self.update_dept_closure(new_obj)
            return new_obj

    @atomic()
    async def update_dept(self, obj_in: DeptUpdate):
        dept_obj = await self.get(id=obj_in.id)
        
        # 如果部门名称发生变化，需要检查是否存在同名被删除的部门
        if dept_obj.name != obj_in.name:
            # 检查是否存在同名但已被标记删除的部门
            same_name_deleted_dept = await self.model.filter(
                name=obj_in.name, 
                is_deleted=True
            ).exclude(id=obj_in.id).first()
            
            if same_name_deleted_dept:
                print(f"编辑部门名称与已删除部门冲突，删除冲突部门: {same_name_deleted_dept.name}, ID: {same_name_deleted_dept.id}")
                # 删除关系
                await DeptClosure.filter(ancestor=same_name_deleted_dept.id).delete()
                await DeptClosure.filter(descendant=same_name_deleted_dept.id).delete()
                # 物理删除冲突的部门记录
                await same_name_deleted_dept.delete()
        
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
            
            # 软删除所有相关部门
            await Dept.filter(id__in=dept_ids).update(is_deleted=True)
            
            # 删除关系表中的所有相关记录
            for child_id in dept_ids:
                await DeptClosure.filter(descendant=child_id).delete()
        else:
            # 仅删除当前部门
            dept.is_deleted = True
            await dept.save()
            
            # 删除关系
            await DeptClosure.filter(descendant=dept_id).delete()


dept_controller = DeptController()
