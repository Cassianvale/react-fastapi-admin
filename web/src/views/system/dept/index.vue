<script setup>
import { h, onMounted, ref, resolveDirective, withDirectives } from 'vue'
import { NButton, NForm, NFormItem, NInput, NInputNumber, NPopconfirm, NTreeSelect, useMessage, NTag } from 'naive-ui'

import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import TheIcon from '@/components/icon/TheIcon.vue'

import { renderIcon } from '@/utils'
import { useCRUD } from '@/composables'
import api from '@/api'

defineOptions({ name: '部门管理' })

const $table = ref(null)
const queryItems = ref({})
const vPermission = resolveDirective('permission')
const message = useMessage()

// 部门数据管理
const allDeptOptions = ref([]) // 存储完整的部门选项
const deptOption = ref([]) // 用于显示在界面上的部门选项（可能经过过滤）
const isDisabled = ref(false)
const currentEditingDeptId = ref(null) // 当前正在编辑的部门ID

// 定义层级样式
const levelColors = [
  '#2d8cf0', // 一级部门
  '#19be6b', // 二级部门
  '#ff9900', // 三级部门
  '#ed4014', // 四级部门
  '#9a66e4', // 五级部门
  '#7265e6', // 其他层级
  '#ffbf00',
  '#00a854',
]

// 获取部门数据并处理为树形结构
const getTableData = async (params) => {
  try {
    const res = await api.departments.getList(params)
    if (res.data && Array.isArray(res.data)) {
      // 处理树形结构，添加层级信息
      return { ...res, data: processTreeData(res.data) }
    }
    return res
  } catch (error) {
    message.error('获取部门数据失败')
    return { data: [] }
  }
}

// 加载部门选项数据
const loadDeptOptions = async () => {
  try {
    const res = await api.departments.getList()
    if (res.data && Array.isArray(res.data)) {
      // 添加顶级部门选项
      const fullOptions = [
        { id: 0, name: '顶级部门', children: [] },
        ...res.data
      ]
      allDeptOptions.value = JSON.parse(JSON.stringify(fullOptions)) // 保存完整副本
      deptOption.value = fullOptions // 当前显示选项
    }
  } catch (error) {
    message.error('加载部门数据失败')
  }
}

// 处理树形数据，添加层级信息
const processTreeData = (deptTree, level = 1) => {
  if (!deptTree || !deptTree.length) return []
  
  return deptTree.map(node => {
    // 创建新节点，包含层级信息
    const newNode = {
      ...node,
      _level: level,
      _levelName: level === 1 ? '一级部门' : level === 2 ? '二级部门' : level === 3 ? '三级部门' : `${level}级部门`
    }
    
    // 如果有子节点，递归处理
    if (node.children && node.children.length) {
      newNode.children = processTreeData(node.children, level + 1)
    } else {
      newNode.children = [] // 确保子节点为空数组
    }
    
    return newNode
  })
}

// 递归获取部门及其所有子部门的ID
const getDeptAndChildrenIds = (deptId, deptList) => {
  const ids = [deptId]
  
  const findChildren = (id, list) => {
    for (const item of list) {
      if (item.parent_id === id) {
        ids.push(item.id)
        findChildren(item.id, list)
      }
    }
  }
  
  findChildren(deptId, deptList)
  return ids
}

// 过滤部门树，排除指定部门及其子部门
const filterDeptTree = (deptId) => {
  if (!deptId) {
    // 如果没有指定部门ID，返回完整的部门树
    deptOption.value = JSON.parse(JSON.stringify(allDeptOptions.value))
    return
  }
  
  // 获取需要从树中排除的部门ID列表
  const excludeIds = getDeptAndChildrenIds(deptId, getPlainDeptList())
  
  // 从完整部门树中创建新的过滤后的树
  const fullTree = JSON.parse(JSON.stringify(allDeptOptions.value))
  
  // 递归过滤部门树
  const filterTree = (treeNodes) => {
    if (!treeNodes || !treeNodes.length) return []
    
    return treeNodes
      .filter(node => !excludeIds.includes(node.id))
      .map(node => {
        if (node.children && node.children.length) {
          node.children = filterTree(node.children)
        }
        return node
      })
  }
  
  deptOption.value = filterTree(fullTree)
}

// 获取扁平化的部门列表（用于查找部门关系）
const getPlainDeptList = () => {
  const plainList = []
  
  const flattenTree = (nodes) => {
    if (!nodes || !nodes.length) return
    
    for (const node of nodes) {
      // 提取主要属性到平面列表
      plainList.push({
        id: node.id,
        name: node.name,
        parent_id: node.parent_id
      })
      
      if (node.children && node.children.length) {
        flattenTree(node.children)
      }
    }
  }
  
  flattenTree(allDeptOptions.value)
  return plainList
}

// 刷新数据
const refreshData = async () => {
  await $table.value?.handleSearch()
  await loadDeptOptions()
}

// 自定义删除处理函数
const customHandleDelete = async (row, cascade = true) => {
  try {
    // 确保传递的是正确的参数格式
    const params = {
      dept_id: row.dept_id || row.id, // 兼容两种参数格式
      cascade: cascade
    }
    
    await api.departments.delete(params)
    message.success('删除成功')
    await refreshData()
  } catch (error) {
    message.error(error.response?.data?.detail || '删除部门失败，请重试')
  }
}

// 检查是否有子部门
const hasChildren = (row) => {
  // 查找当前部门树中是否有父ID等于当前部门ID的记录
  const findChildren = (list) => {
    for (const item of list) {
      if (item.parent_id === row.id) {
        return true
      }
      if (item.children && item.children.length > 0) {
        const found = findChildren(item.children)
        if (found) return true
      }
    }
    return false
  }
  
  // 从部门选项中查找
  return findChildren(allDeptOptions.value)
}

const {
  modalVisible,
  modalTitle,
  modalLoading,
  handleSave: originalHandleSave,
  modalForm,
  modalFormRef,
  handleEdit: originalHandleEdit,
  handleDelete: originalHandleDelete,
  handleAdd,
  modalAction
} = useCRUD({
  name: '部门',
  initForm: { order: 0, parent_id: 0 },
  doCreate: api.departments.create,
  doUpdate: api.departments.update,
  doDelete: api.departments.delete,
  refresh: () => refreshData(),
})

// 自定义编辑处理函数
const handleEdit = (row) => {
  // 创建一个包含所有必要字段的完整对象
  const fullRow = {
    id: row.id,
    name: row.name,
    desc: row.desc || '',
    parent_id: row.parent_id || 0,
    order: row.order || 0
  }
  
  // 设置父级选择状态
  isDisabled.value = fullRow.parent_id === 0
  
  // 设置当前正在编辑的部门ID
  currentEditingDeptId.value = fullRow.id
  
  // 过滤部门树，排除当前部门及其子部门
  filterDeptTree(fullRow.id)
  
  // 调用原始编辑函数，传递完整的对象
  originalHandleEdit(fullRow)
}

// 自定义保存处理函数，增加错误处理
const handleSave = async () => {
  try {
    // 编辑模式下，确保ID字段存在
    if (modalAction.value === 'edit' && !modalForm.value.id) {
      message.error('编辑部门失败：缺少ID字段')
      modalLoading.value = false
      return
    }
    
    const result = await originalHandleSave()
    
    // 处理返回结果
    if (result?.data?.id) {
      if (modalAction.value === 'add') {
        // 新增模式下，可能是恢复了已删除的部门
        message.success('部门创建成功（已恢复之前删除的同名部门）')
      } else if (modalAction.value === 'edit') {
        // 编辑模式下，可能删除了一个同名的已删除部门
        message.success('部门更新成功（已处理同名冲突）')
      }
    }
    
    // 成功保存后刷新部门选择器数据
    await loadDeptOptions()
    // 重置当前编辑部门ID
    currentEditingDeptId.value = null
  } catch (error) {
    // 处理部门名称重复错误
    if (error.response?.data?.detail?.includes('UNIQUE constraint failed: dept.name')) {
      message.error('部门名称已存在，请使用其他名称')
      modalLoading.value = false
      return
    }
    
    // 处理其他错误
    message.error(error.response?.data?.detail || '保存部门失败，请重试')
    modalLoading.value = false
  }
}

onMounted(() => {
  refreshData()
})

const deptRules = {
  name: [
    {
      required: true,
      message: '请输入部门名称',
      trigger: ['input', 'blur', 'change'],
    },
    {
      message: '部门名称必须唯一',
      trigger: ['input', 'blur', 'change'],
    }
  ],
}

// 新增部门
function addDepts() {
  isDisabled.value = false
  modalForm.value.parent_id = 0
  // 恢复完整的部门树
  filterDeptTree(null)
  // 重置当前编辑部门ID
  currentEditingDeptId.value = null
  handleAdd()
}

// 渲染部门名称，添加层级样式
const renderDeptName = (row) => {
  // 确保有层级信息
  const level = typeof row._level === 'number' ? row._level : 1
  
  // 获取对应层级的颜色
  const colorIndex = level - 1
  const color = levelColors[colorIndex >= 0 ? colorIndex % levelColors.length : 0]
  
  // 选择不同层级的图标
  const iconName = level === 1 ? 'material-symbols:business' : 'material-symbols:subdirectory-arrow-right'
  
  // 获取层级标签文本
  const getLevelTagText = (level) => {
    switch (level) {
      case 2: return '二级'
      case 3: return '三级'
      case 4: return '四级'
      case 5: return '五级'
      default: return `${level}级`
    }
  }
  
  return h(
    'div',
    { style: { display: 'flex', alignItems: 'center' } },
    [
      // 图标
      h(TheIcon, {
        icon: iconName,
        size: 18,
        color: color,
        style: 'margin-right: 5px;'
      }),
      
      // 部门名称
      h('span', 
        { style: { color, fontWeight: level === 1 ? 'bold' : 'normal' } },
        row.name
      ),
      
      // 显示层级标签（仅对非一级部门）
      level > 1 ? h(
        NTag,
        { size: 'small', type: 'info', style: 'margin-left: 5px;' },
        { default: () => getLevelTagText(level) }
      ) : null
    ]
  )
}

const columns = [
  {
    title: '部门名称',
    key: 'name',
    align: 'left',
    width: 'auto',
    ellipsis: { tooltip: true },
    render: (row) => renderDeptName(row)
  },
  {
    title: '备注',
    key: 'desc',
    align: 'center',
    width: 'auto',
    ellipsis: { tooltip: true },
  },
  {
    title: '操作',
    key: 'actions',
    align: 'center',
    width: 'auto',
    fixed: 'right',
    render(row) {
      return [
        withDirectives(
          h(
            NButton,
            {
              size: 'small',
              type: 'primary',
              style: 'margin-left: 8px;',
              onClick: () => handleEdit(row),
            },
            {
              default: () => '编辑',
              icon: renderIcon('material-symbols:edit', { size: 16 }),
            }
          ),
          [[vPermission, 'post/api/v1/dept/update']]
        ),
        h(
          NPopconfirm,
          {
            onPositiveClick: () => customHandleDelete({ dept_id: row.id }),
            onNegativeClick: () => {},
          },
          {
            trigger: () =>
              withDirectives(
                h(
                  NButton,
                  {
                    size: 'small',
                    type: 'error',
                    style: 'margin-left: 8px;',
                  },
                  {
                    default: () => '删除',
                    icon: renderIcon('material-symbols:delete-outline', { size: 16 }),
                  }
                ),
                [[vPermission, 'delete/api/v1/dept/delete']]
              ),
            default: () => {
              // 检查是否有子部门，显示级联删除提示
              const hasChildDepts = hasChildren(row)
              if (hasChildDepts) {
                return h('div', {}, [
                  h('p', { style: 'margin-bottom: 8px;' }, '确定删除该部门吗?'),
                  h('p', { style: 'color: #ff7875;' }, '警告：该部门下存在子部门，将一并删除！')
                ])
              } else {
                return h('div', {}, '确定删除该部门吗?')
              }
            }
          }
        ),
      ]
    },
  },
]
</script>

<template>
  <!-- 业务页面 -->
  <CommonPage show-footer title="部门列表">
    <template #action>
      <div>
        <NButton
          v-permission="'post/api/v1/dept/create'"
          class="float-right mr-15"
          type="primary"
          @click="addDepts"
        >
          <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />新建部门
        </NButton>
      </div>
    </template>
    <!-- 表格 -->
    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      :columns="columns"
      :get-data="getTableData"
      row-key="id"
      :tree="true"
      :children-key="'children'"
      :indent="20"
      :default-expand-all="true"
    >
      <template #queryBar>
        <QueryBarItem label="部门名称" :label-width="80">
          <NInput
            v-model:value="queryItems.name"
            clearable
            type="text"
            placeholder="请输入部门名称"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
      </template>
    </CrudTable>

    <!-- 新增/编辑 弹窗 -->
    <CrudModal
      v-model:visible="modalVisible"
      :title="modalTitle"
      :loading="modalLoading"
      @save="handleSave"
    >
      <NForm
        ref="modalFormRef"
        label-placement="left"
        label-align="left"
        :label-width="80"
        :model="modalForm"
        :rules="deptRules"
      >
        <NFormItem label="父级部门" path="parent_id">
          <NTreeSelect
            v-model:value="modalForm.parent_id"
            :options="deptOption"
            key-field="id"
            label-field="name"
            placeholder="请选择父级部门"
            clearable
            default-expand-all
            :disabled="isDisabled"
          ></NTreeSelect>
        </NFormItem>
        <NFormItem label="部门名称" path="name">
          <NInput v-model:value="modalForm.name" clearable placeholder="请输入部门名称" />
        </NFormItem>
        <NFormItem label="备注" path="desc">
          <NInput v-model:value="modalForm.desc" type="textarea" clearable />
        </NFormItem>
        <NFormItem label="排序" path="order">
          <NInputNumber v-model:value="modalForm.order" min="0"></NInputNumber>
        </NFormItem>
      </NForm>
    </CrudModal>
  </CommonPage>
</template>
