<template>
  <!-- 业务页面 -->
  <CommonPage show-footer title="商品列表">
    <template #action>
      <div>
        <NButton
          v-permission="'post/api/v1/product/create'"
          class="float-right mr-15"
          type="primary"
          @click="handleAdd"
        >
          <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />新建商品
        </NButton>
      </div>
    </template>
    
    <!-- 表格 -->
    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      :columns="columns"
      :get-data="loadProducts"
    >
      <template #queryBar>
        <QueryBarItem label="商品名称" :label-width="80">
          <NInput
            v-model:value="queryItems.name"
            clearable
            type="text"
            placeholder="请输入商品名称"
            @keypress.enter="$table?.handleSearch()"
            style="width: 200px"
          />
        </QueryBarItem>
        <QueryBarItem label="商品分类" :label-width="80">
          <NSelect
            v-model:value="queryItems.category_id"
            :options="categoryOptions"
            placeholder="请选择商品分类"
            clearable
            style="width: 200px"
          />
        </QueryBarItem>
        <QueryBarItem label="商品状态" :label-width="80">
          <NSelect
            v-model:value="queryItems.status"
            :options="statusOptions"
            placeholder="请选择商品状态"
            clearable
            style="width: 160px"
          />
        </QueryBarItem>
      </template>
    </CrudTable>

    <!-- 新增/编辑 弹窗 -->
    <CrudModal
      v-model:visible="modalVisible"
      :title="modalTitle"
      :loading="modalLoading"
      style="width: 750px"
      @save="handleSubmit"
    >
      <NForm
        ref="modalFormRef"
        label-placement="left"
        label-align="left"
        :label-width="80"
        :model="modalForm"
        :rules="productRules"
      >
        <NFormItem label="商品名称" path="name">
          <NInput v-model:value="modalForm.name" clearable placeholder="请输入商品名称" />
        </NFormItem>
        <NFormItem label="商品分类" path="category_id">
          <NSelect
            v-model:value="modalForm.category_id"
            :options="categoryOptions"
            placeholder="请选择商品分类"
            style="width: 100%"
          />
        </NFormItem>
        <NFormItem label="商品图片" path="image">
          <NInput v-model:value="modalForm.image" clearable placeholder="请输入商品图片URL" />
        </NFormItem>
        <NFormItem label="成本价" path="cost_price">
          <NInputNumber
            v-model:value="modalForm.cost_price"
            placeholder="请输入成本价"
            :min="0"
            :precision="2"
          />
        </NFormItem>
        <NFormItem label="销售价" path="sale_price">
          <NInputNumber
            v-model:value="modalForm.sale_price"
            placeholder="请输入销售价"
            :min="0"
            :precision="2"
          />
        </NFormItem>
        <NFormItem label="商品规格" path="specifications">
          <ProductSpecEditor v-model="modalForm.specifications" class="w-full" />
        </NFormItem>
        <NFormItem label="商品描述" path="description">
          <NInput
            v-model:value="modalForm.description"
            type="textarea"
            clearable
            placeholder="请输入商品描述"
          />
        </NFormItem>
        <NFormItem label="商品状态" path="status">
          <NSwitch v-model:value="modalForm.status" />
        </NFormItem>
      </NForm>
    </CrudModal>
  </CommonPage>
</template>

<script setup>
import { h, onMounted, ref, resolveDirective, withDirectives } from 'vue'
import { 
  NButton, 
  NForm, 
  NFormItem, 
  NInput, 
  NInputNumber, 
  NPopconfirm, 
  NSelect, 
  NSwitch, 
  NTag, 
  useMessage 
} from 'naive-ui'

import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import TheIcon from '@/components/icon/TheIcon.vue'
import ProductSpecEditor from './components/ProductSpecEditor.vue'

import { renderIcon } from '@/utils'
import { useCRUD } from '@/composables'
import api from '@/api'

defineOptions({ name: '商品管理' })

// 状态与引用
const $table = ref(null)
const queryItems = ref({
  name: '',
  category_id: null,
  status: null
})
const vPermission = resolveDirective('permission')
const $message = useMessage()

// 选项数据
const statusOptions = [
  { label: '上架', value: true },
  { label: '下架', value: false }
]
const categoryOptions = ref([])

// 加载商品数据
const loadProducts = async (params) => {
  try {
    return await api.products.getList(params)
  } catch (error) {
    $message.error('加载商品失败')
    return { data: [] }
  }
}

// 加载分类选项
const loadCategories = async () => {
  try {
    const res = await api.categories.getList({ page_size: 100 })
    if (res.code === 200) {
      categoryOptions.value = res.data.map(item => ({
        label: item.name,
        value: item.id
      }))
    }
  } catch (error) {
    console.error('加载分类失败', error)
  }
}

// 商品表单验证规则
const productRules = {
  name: {
    required: true,
    message: '请输入商品名称',
    trigger: ['blur', 'change']
  },
  category_id: {
    required: true,
    type: 'number',
    message: '请选择商品分类',
    trigger: ['blur', 'change']
  },
  cost_price: {
    required: true,
    type: 'number',
    validator: (rule, value) => {
      if (value === null || value === undefined || value === '') return false
      return Number(value) >= 0
    },
    message: '请输入有效的成本价',
    trigger: ['blur', 'change']
  },
  sale_price: {
    required: true,
    type: 'number',
    validator: (rule, value) => {
      if (value === null || value === undefined || value === '') return false
      return Number(value) >= 0
    },
    message: '请输入有效的销售价',
    trigger: ['blur', 'change']
  }
}

// 使用CRUD钩子统一管理状态
const {
  modalVisible,
  modalTitle,
  modalLoading,
  modalForm,
  modalFormRef,
  handleAdd,
  handleDelete,
  modalAction
} = useCRUD({
  name: '商品',
  initForm: { 
    name: '',
    category_id: null,
    image: '',
    cost_price: 0,
    sale_price: 0,
    specifications: {},
    description: '',
    status: true
  },
  doCreate: (data) => api.products.create(data),
  doUpdate: (data) => {
    // 从数据中提取ID，然后传递ID和剩余数据给API
    const { id, ...restData } = data
    return api.products.update(id, restData)
  },
  doDelete: (id) => api.products.delete(id),
  refresh: () => $table.value?.handleSearch(),
})

// 自定义handleSave函数，不使用CRUD中的handleSave
const handleSave = async (apiData) => {
  try {
    if (modalAction.value === 'add') {
      await api.products.create(apiData)
      $message.success('新增成功')
    } else if (modalAction.value === 'edit') {
      // 从表单数据中分离ID和其他数据
      const { id, ...productData } = apiData
      await api.products.update(id, productData)
      $message.success('编辑成功')
    }
    modalVisible.value = false
    $table.value?.handleSearch()
  } catch (error) {
    console.error('保存失败', error)
    $message.error('保存失败')
  }
}

// 自定义编辑函数，处理价格字段类型
const handleEdit = (row) => {
  // 创建一个数据副本
  const formData = { ...row }
  
  // 确保价格字段是数值类型
  if (formData.cost_price !== undefined && formData.cost_price !== null) {
    formData.cost_price = Number(formData.cost_price)
  }
  
  if (formData.sale_price !== undefined && formData.sale_price !== null) {
    formData.sale_price = Number(formData.sale_price)
  }
  
  // 调用CRUD钩子的编辑方法
  modalVisible.value = true
  modalAction.value = 'edit'
  modalForm.value = formData
}

// 格式化价格为两位小数字符串
const formatPrice = (price) => (Number(price) || 0).toFixed(2)

// 处理表单提交
const handleSubmit = async () => {
  modalFormRef.value?.validate(async (errors) => {
    if (errors) return
      
    try {
      // 创建API请求数据并处理价格字段
      const apiData = {...modalForm.value}
      
      // 确保价格字段是字符串格式，保留两位小数
      if (apiData.cost_price !== null && apiData.cost_price !== undefined) {
        apiData.cost_price = formatPrice(apiData.cost_price)
      }
      
      if (apiData.sale_price !== null && apiData.sale_price !== undefined) {
        apiData.sale_price = formatPrice(apiData.sale_price)
      }

      await handleSave(apiData)
    } catch (error) {
      $message.error('保存失败')
    }
  })
}

// 切换商品状态
const handleToggleStatus = async (row) => {
  try {
    await api.products.updateStatus(row.id, !row.status)
    $message.success(`商品已${row.status ? '下架' : '上架'}`)
    $table.value?.handleSearch()
  } catch (error) {
    $message.error('状态更新失败')
  }
}

// 表格列配置
const columns = [
  {
    title: 'ID',
    key: 'id',
    width: 80,
    align: 'center',
  },
  {
    title: '商品名称',
    key: 'name',
    width: 150,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '商品分类',
    key: 'category_name',
    width: 120,
    align: 'center',
  },
  {
    title: '商品图片',
    key: 'image',
    width: 100,
    align: 'center',
    render(row) {
      return row.image 
        ? h('img', { 
            src: row.image, 
            style: { width: '50px', height: '50px', objectFit: 'cover', borderRadius: '4px' } 
          })
        : '无图片'
    }
  },
  {
    title: '价格信息',
    key: 'price',
    width: 180,
    align: 'center',
    render(row) {
      return h('div', [
        h('div', { style: { fontSize: '13px', marginBottom: '4px' }}, [
          h('span', { style: { color: '#606266' }}, '成本: '),
          h('span', { style: { fontWeight: '500', color: '#2080f0' }}, formatPrice(row.cost_price))
        ]),
        h('div', { style: { fontSize: '13px' }}, [
          h('span', { style: { color: '#606266' }}, '销售: '),
          h('span', { style: { fontWeight: '500', color: '#d03050' }}, formatPrice(row.sale_price))
        ])
      ])
    }
  },
  {
    title: '状态',
    key: 'status',
    width: 80,
    align: 'center',
    render(row) {
      return h(
        NTag,
        {
          type: row.status ? 'success' : 'error',
          round: true,
          size: 'small'
        },
        { default: () => row.status ? '上架' : '下架' }
      )
    }
  },
  {
    title: '创建时间',
    key: 'created_at',
    width: 180,
    align: 'center',
  },
  {
    title: '操作',
    key: 'actions',
    width: 220,
    align: 'center',
    fixed: 'right',
    render(row) {
      return [
        withDirectives(
          h(
            NButton,
            {
              size: 'small',
              type: 'primary',
              style: 'margin-right: 8px;',
              onClick: () => handleEdit(row),
            },
            {
              default: () => '编辑',
              icon: renderIcon('material-symbols:edit', { size: 16 }),
            }
          ),
          [[vPermission, 'post/api/v1/product/update']]
        ),
        withDirectives(
          h(
            NButton,
            {
              size: 'small',
              type: row.status ? 'warning' : 'success',
              style: 'margin-right: 8px;',
              onClick: () => handleToggleStatus(row),
            },
            {
              default: () => row.status ? '下架' : '上架',
              icon: renderIcon(row.status ? 'material-symbols:arrow-downward' : 'material-symbols:arrow-upward', { size: 16 }),
            }
          ),
          [[vPermission, 'post/api/v1/product/update-status']]
        ),
        h(
          NPopconfirm,
          {
            onPositiveClick: () => handleDelete(row.id, false),
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
                  },
                  {
                    default: () => '删除',
                    icon: renderIcon('material-symbols:delete-outline', { size: 16 }),
                  }
                ),
                [[vPermission, 'delete/api/v1/product/delete']]
              ),
            default: () => h('div', {}, '确定删除该商品吗?'),
          }
        ),
      ]
    },
  },
]

// 初始化
onMounted(() => {
  $table.value?.handleSearch()
  loadCategories()
})
</script> 