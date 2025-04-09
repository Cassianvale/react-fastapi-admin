<template>
  <div class="h-full flex flex-col">
    <div class="flex-none p-4 flex justify-between">
      <div class="flex gap-4">
        <n-input
          v-model:value="searchParams.name"
          placeholder="请输入商品名称"
          class="w-200"
          @keydown.enter="handleSearch"
        />
        <n-select
          v-model:value="searchParams.category_id"
          :options="categoryOptions"
          placeholder="请选择商品分类"
          clearable
          class="w-200"
        />
        <n-select
          v-model:value="searchParams.status"
          :options="statusOptions"
          placeholder="请选择商品状态"
          clearable
          class="w-160"
        />
        <n-button type="primary" @click="handleSearch">搜索</n-button>
        <n-button @click="resetSearch">重置</n-button>
      </div>
      <div>
        <n-button type="primary" @click="openModal()">
          <template #icon>
            <n-icon>
              <IconPlus />
            </n-icon>
          </template>
          添加商品
        </n-button>
      </div>
    </div>

    <div class="flex-auto p-4">
      <n-data-table
        :columns="columns"
        :data="tableData"
        :pagination="pagination"
        :loading="loading"
        @update:page="handlePageChange"
        @update:page-size="handlePageSizeChange"
      />
    </div>

    <n-modal
      v-model:show="showModal"
      :title="modalTitle"
      preset="card"
      style="width: 750px"
      :mask-closable="false"
    >
      <n-form
        ref="formRef"
        :model="formData"
        :rules="rules"
        label-placement="left"
        label-width="auto"
        require-mark-placement="right-hanging"
      >
        <n-form-item label="商品名称" path="name">
          <n-input v-model:value="formData.name" placeholder="请输入商品名称" />
        </n-form-item>
        <n-form-item label="商品分类" path="category_id">
          <n-select
            v-model:value="formData.category_id"
            :options="categoryOptions"
            placeholder="请选择商品分类"
          />
        </n-form-item>
        <n-form-item label="商品图片" path="image">
          <n-input v-model:value="formData.image" placeholder="请输入商品图片URL" />
        </n-form-item>
        <n-form-item label="成本价" path="cost_price">
          <n-input-number
            v-model:value="formData.cost_price"
            placeholder="请输入成本价"
            :min="0"
            :precision="2"
          />
        </n-form-item>
        <n-form-item label="销售价" path="sale_price">
          <n-input-number
            v-model:value="formData.sale_price"
            placeholder="请输入销售价"
            :min="0"
            :precision="2"
          />
        </n-form-item>
        <n-form-item label="商品规格" path="specifications">
          <div class="spec-editor">
            <div class="spec-header flex justify-between mb-3">
              <div class="flex gap-2">
                <n-button size="small" type="primary" @click="addSpecRow">
                  <template #icon><n-icon><IconRowAdd /></n-icon></template>
                  添加规格
                </n-button>
                <n-button v-if="specRows.length > 0" size="small" @click="previewJSON">
                  <template #icon><n-icon><IconCode /></n-icon></template>
                  查看JSON
                </n-button>
              </div>
            </div>
            
            <n-card v-if="specRows.length === 0" size="small" class="empty-spec-card text-center py-6">
              <n-empty description="暂无规格信息">
                <template #extra>
                  <n-button type="primary" @click="addSpecRow">添加第一个规格</n-button>
                </template>
              </n-empty>
            </n-card>
            
            <div v-else class="spec-items-container">
              <div v-for="(row, index) in specRows" :key="index" class="spec-item">
                <div class="spec-item-content">
                  <div class="spec-input-group">
                    <div class="spec-label">规格名称</div>
                    <n-input 
                      v-model:value="row.key" 
                      placeholder="如：颜色、尺寸" 
                      class="spec-input"
                      @update:value="updateSpecifications" 
                    />
                  </div>
                  <div class="spec-input-group">
                    <div class="spec-label">规格值</div>
                    <n-input 
                      v-model:value="row.value" 
                      placeholder="如：红色、XL" 
                      class="spec-input"
                      @update:value="updateSpecifications" 
                    />
                  </div>
                  <div class="spec-actions">
                    <n-button 
                      size="small" 
                      quaternary 
                      circle 
                      type="error" 
                      @click="deleteSpecRow(index)"
                    >
                      <template #icon><n-icon><IconDelete /></n-icon></template>
                    </n-button>
                  </div>
                </div>
                <n-divider v-if="index < specRows.length - 1" style="margin: 10px 0" />
              </div>
            </div>
          </div>
        </n-form-item>
        <n-form-item label="商品描述" path="description">
          <n-input
            v-model:value="formData.description"
            type="textarea"
            placeholder="请输入商品描述"
          />
        </n-form-item>
        <n-form-item label="商品状态" path="status">
          <n-switch v-model:value="formData.status" />
        </n-form-item>
      </n-form>
      <template #footer>
        <div class="flex justify-end gap-2">
          <n-button @click="closeModal">取消</n-button>
          <n-button type="primary" @click="handleSubmit">确认</n-button>
        </div>
      </template>
    </n-modal>
    
    <!-- JSON预览弹窗 -->
    <n-modal v-model:show="showJsonPreview" preset="card" title="规格JSON预览">
      <n-code :code="specificationPreviewJson" language="json" />
      <template #footer>
        <div class="flex justify-end">
          <n-button @click="showJsonPreview = false">关闭</n-button>
        </div>
      </template>
    </n-modal>
  </div>
</template>

<script setup>
import { h, ref, reactive, computed, watch, nextTick } from 'vue'
import { useMessage } from 'naive-ui'
import { Icon } from '@iconify/vue'
import api from '@/api'

// 图标组件
const IconPlus = () => h(Icon, { icon: 'material-symbols:add' })
const IconRowAdd = () => h(Icon, { icon: 'material-symbols:add-box' })
const IconDelete = () => h(Icon, { icon: 'material-symbols:delete-outline' })
const IconEdit = () => h(Icon, { icon: 'material-symbols:edit' })
const IconCode = () => h(Icon, { icon: 'material-symbols:code' })

const message = useMessage()

// ==================== 表格和列表状态 ====================
const tableData = ref([])
const loading = ref(false)
const pagination = reactive({
  page: 1,
  pageSize: 10,
  itemCount: 0,
  showSizePicker: true,
  pageSizes: [10, 20, 30, 40]
})

// 搜索参数
const searchParams = reactive({
  name: '',
  category_id: null,
  status: null,
  page: 1,
  page_size: 10
})

// 状态选项
const statusOptions = [
  { label: '上架', value: true },
  { label: '下架', value: false }
]

// 分类选项
const categoryOptions = ref([])

// ==================== 表单数据 ====================
const formRef = ref(null)
const initialFormState = {
  id: null,
  name: '',
  category_id: null,
  image: '',
  cost_price: 0,
  sale_price: 0,
  specifications: {},
  description: '',
  status: true
}
const formData = reactive({...initialFormState})

// 模态框控制
const showModal = ref(false)
const isEdit = ref(false)
const modalTitle = computed(() => isEdit.value ? '编辑商品' : '添加商品')

// ==================== 规格相关 ====================
const specRows = ref([])
const showJsonPreview = ref(false)
const specificationPreviewJson = ref('')

// ==================== 加载数据函数 ====================
// 加载分类选项
const loadCategories = async () => {
  try {
    const res = await api.getCategoryList({ page_size: 100 })
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

// 加载表格数据
const loadData = async () => {
  loading.value = true
  try {
    const res = await api.getProductList(searchParams)
    if (res.code === 200) {
      tableData.value = res.data
      pagination.itemCount = res.total
      pagination.page = res.page
      pagination.pageSize = res.page_size
    }
  } catch (error) {
    console.error('加载数据失败', error)
  } finally {
    loading.value = false
  }
}

// ==================== 公共工具函数 ====================
// 格式化价格为两位小数字符串
const formatPrice = (price) => {
  return (Number(price) || 0).toFixed(2)
}

// 将字符串价格转为数字
const priceToNumber = (price) => {
  return typeof price === 'string' ? Number(price) || 0 : (price || 0)
}

// 确保规格是有效的对象
const ensureValidSpecifications = (specs) => {
  if (typeof specs !== 'object' || specs === null) {
    return {}
  }
  return specs
}

// ==================== 表单和规格处理函数 ====================
// 处理价格字段，确保为两位小数字符串
const processPriceFields = (data) => {
  const result = {...data}
  if (result.cost_price !== null && result.cost_price !== undefined) {
    result.cost_price = formatPrice(result.cost_price)
  }
  if (result.sale_price !== null && result.sale_price !== undefined) {
    result.sale_price = formatPrice(result.sale_price)
  }
  return result
}

// 初始化规格行数据
const initSpecRows = (specs = {}) => {
  specRows.value = []
  const validSpecs = ensureValidSpecifications(specs)
  for (const key in validSpecs) {
    specRows.value.push({ key, value: validSpecs[key] })
  }
}

// 更新规格JSON数据
const updateSpecifications = () => {
  const specs = {}
  for (const row of specRows.value) {
    if (row.key && row.key.trim() !== '') {
      specs[row.key] = row.value
    }
  }
  formData.specifications = specs
}

// 添加规格行
const addSpecRow = () => {
  specRows.value.push({ key: '', value: '' })
  updateSpecifications()
}

// 删除规格行
const deleteSpecRow = (index) => {
  specRows.value.splice(index, 1)
  updateSpecifications()
}

// 预览JSON
const previewJSON = () => {
  specificationPreviewJson.value = JSON.stringify(formData.specifications, null, 2)
  showJsonPreview.value = true
}

// 重置表单
const resetForm = () => {
  // 重置为初始状态
  Object.keys(initialFormState).forEach(key => {
    formData[key] = typeof initialFormState[key] === 'object' 
      ? JSON.parse(JSON.stringify(initialFormState[key])) 
      : initialFormState[key]
  })
  
  // 重置规格表格数据
  initSpecRows()
  
  // 重置表单验证状态
  formRef.value?.restoreValidation()
}

// ==================== 事件处理函数 ====================
// 页码变更
const handlePageChange = (page) => {
  searchParams.page = page
  loadData()
}

// 页大小变更
const handlePageSizeChange = (pageSize) => {
  searchParams.page_size = pageSize
  searchParams.page = 1
  loadData()
}

// 搜索
const handleSearch = () => {
  searchParams.page = 1
  loadData()
}

// 重置搜索
const resetSearch = () => {
  searchParams.name = ''
  searchParams.category_id = null
  searchParams.status = null
  searchParams.page = 1
  loadData()
}

// 打开模态框
const openModal = (row) => {
  resetForm()
  
  if (row) {
    isEdit.value = true
    // 深拷贝数据以避免直接引用
    Object.keys(row).forEach(key => {
      if (key in formData) {
        if (key === 'cost_price' || key === 'sale_price') {
          // 确保价格为数字类型，用于表单显示
          formData[key] = priceToNumber(row[key])
        } else if (key === 'specifications') {
          formData[key] = ensureValidSpecifications(row[key])
        } else {
          formData[key] = typeof row[key] === 'object' && row[key] !== null
            ? JSON.parse(JSON.stringify(row[key]))
            : row[key]
        }
      }
    })
    
    // 初始化规格表格数据
    nextTick(() => {
      initSpecRows(formData.specifications)
    })
  } else {
    isEdit.value = false
  }
  
  showModal.value = true
}

// 关闭模态框
const closeModal = () => {
  showModal.value = false
}

// 编辑
const handleEdit = (row) => {
  openModal(row)
}

// 切换状态
const handleToggleStatus = async (row) => {
  try {
    await api.updateProductStatus(row.id, !row.status)
    message.success('状态更新成功')
    loadData()
  } catch (error) {
    message.error('状态更新失败')
  }
}

// 删除
const handleDelete = async (row) => {
  try {
    await api.deleteProduct(row.id)
    message.success('删除成功')
    loadData()
  } catch (error) {
    message.error('删除失败')
  }
}

// 提交表单
const handleSubmit = async () => {
  formRef.value?.validate(async (errors) => {
    if (errors) {
      console.error('表单验证错误:', errors)
      return
    }

    try {
      // 创建一个用于API请求的数据副本并处理价格字段
      const apiData = processPriceFields({...formData})
      
      // 确保规格是有效的JSON对象
      apiData.specifications = ensureValidSpecifications(apiData.specifications)

      if (isEdit.value) {
        await api.updateProduct(apiData.id, apiData)
        message.success('更新成功')
      } else {
        await api.createProduct(apiData)
        message.success('添加成功')
      }
      closeModal()
      loadData()
    } catch (error) {
      console.error('提交失败:', error)
      message.error(isEdit.value ? '更新失败' : '添加失败')
    }
  })
}

// ==================== 表单验证规则 ====================
const rules = {
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

// ==================== 表格列定义 ====================
const columns = [
  {
    title: 'ID',
    key: 'id',
    width: 80
  },
  {
    title: '商品名称',
    key: 'name',
    width: 150
  },
  {
    title: '商品分类',
    key: 'category_name',
    width: 120
  },
  {
    title: '商品图片',
    key: 'image',
    width: 100,
    render(row) {
      return row.image 
        ? h('img', { 
            src: row.image, 
            style: { width: '50px', height: '50px', objectFit: 'cover' } 
          })
        : '无图片'
    }
  },
  {
    title: '成本价',
    key: 'cost_price',
    width: 100
  },
  {
    title: '销售价',
    key: 'sale_price',
    width: 100
  },
  {
    title: '状态',
    key: 'status',
    width: 80,
    render(row) {
      return h(
        'n-tag',
        {
          type: row.status ? 'success' : 'error'
        },
        { default: () => row.status ? '上架' : '下架' }
      )
    }
  },
  {
    title: '创建时间',
    key: 'created_at',
    width: 180
  },
  {
    title: '操作',
    key: 'actions',
    width: 250,
    fixed: 'right',
    render(row) {
      return h('div', [
        h(
          'button',
          {
            style: {
              marginRight: '10px',
              color: '#2080f0'
            },
            onClick: () => handleEdit(row)
          },
          '编辑'
        ),
        h(
          'button',
          {
            style: {
              marginRight: '10px',
              color: row.status ? '#d03050' : '#18a058'
            },
            onClick: () => handleToggleStatus(row)
          },
          row.status ? '下架' : '上架'
        ),
        h(
          'button',
          {
            style: {
              color: '#d03050'
            },
            onClick: () => handleDelete(row)
          },
          '删除'
        )
      ])
    }
  }
]

// 初始加载
loadCategories()
loadData()
</script>

<style scoped>
.spec-editor {
  border: 1px solid #eee;
  border-radius: 6px;
  padding: 16px;
  background-color: #fafafa;
}

.empty-spec-card {
  background-color: #fcfcfc;
  border: 1px dashed #e0e0e0;
}

.spec-items-container {
  max-height: 300px;
  overflow-y: auto;
  padding: 2px;
  background-color: #fff;
  border-radius: 4px;
  border: 1px solid #eee;
}

.spec-item {
  padding: 8px;
}

.spec-item-content {
  display: flex;
  align-items: center;
  gap: 12px;
}

.spec-input-group {
  flex: 1;
}

.spec-label {
  font-size: 12px;
  color: #606266;
  margin-bottom: 4px;
}

.spec-input {
  width: 100%;
}

.spec-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
}
</style> 