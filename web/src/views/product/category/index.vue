<template>
  <div class="h-full flex flex-col">
    <div class="flex-none p-4 flex justify-between">
      <div>
        <n-input
          v-model:value="searchParams.name"
          placeholder="请输入分类名称"
          class="w-200"
          @keydown.enter="handleSearch"
        />
        <n-button type="primary" @click="handleSearch" class="ml-4">搜索</n-button>
        <n-button @click="resetSearch" class="ml-4">重置</n-button>
      </div>
      <div>
        <n-button type="primary" @click="openModal()">
          <template #icon>
            <n-icon>
              <IconPlus />
            </n-icon>
          </template>
          添加分类
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
      />
    </div>

    <n-modal
      v-model:show="showModal"
      :title="modalTitle"
      preset="dialog"
      positive-text="确认"
      negative-text="取消"
      @positive-click="handleSubmit"
      @negative-click="closeModal"
    >
      <n-form
        ref="formRef"
        :model="formData"
        :rules="rules"
        label-placement="left"
        label-width="auto"
        require-mark-placement="right-hanging"
      >
        <n-form-item label="分类名称" path="name">
          <n-input v-model:value="formData.name" placeholder="请输入分类名称" />
        </n-form-item>
        <n-form-item label="分类描述" path="description">
          <n-input
            v-model:value="formData.description"
            type="textarea"
            placeholder="请输入分类描述"
          />
        </n-form-item>
        <n-form-item label="排序" path="order">
          <n-input-number v-model:value="formData.order" placeholder="请输入排序" />
        </n-form-item>
      </n-form>
    </n-modal>
  </div>
</template>

<script setup>
import { h, ref, reactive, computed } from 'vue'
import { useMessage } from 'naive-ui'
import { Icon } from '@iconify/vue'
import api from '@/api'

const IconPlus = () => h(Icon, { icon: 'material-symbols:add' })

const message = useMessage()

// 表格数据
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
  page: 1,
  page_size: 10
})

// 表单数据
const formRef = ref(null)
const formData = reactive({
  id: null,
  name: '',
  description: '',
  order: 0
})

// 表单验证规则
const rules = {
  name: {
    required: true,
    message: '请输入分类名称',
    trigger: 'blur'
  }
}

// 模态框控制
const showModal = ref(false)
const isEdit = ref(false)
const modalTitle = computed(() => isEdit.value ? '编辑商品分类' : '添加商品分类')

// 表格列定义
const columns = [
  {
    title: 'ID',
    key: 'id',
    width: 80
  },
  {
    title: '分类名称',
    key: 'name',
    width: 160
  },
  {
    title: '分类描述',
    key: 'description'
  },
  {
    title: '排序',
    key: 'order',
    width: 100
  },
  {
    title: '创建时间',
    key: 'created_at',
    width: 180
  },
  {
    title: '更新时间',
    key: 'updated_at',
    width: 180
  },
  {
    title: '操作',
    key: 'actions',
    width: 160,
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

// 加载表格数据
const loadData = async () => {
  loading.value = true
  try {
    const res = await api.getCategoryList(searchParams)
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

// 页码变更
const handlePageChange = (page) => {
  searchParams.page = page
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
  searchParams.page = 1
  loadData()
}

// 打开模态框
const openModal = (row) => {
  if (row) {
    isEdit.value = true
    Object.assign(formData, row)
  } else {
    isEdit.value = false
    formData.id = null
    formData.name = ''
    formData.description = ''
    formData.order = 0
  }
  showModal.value = true
}

// 关闭模态框
const closeModal = () => {
  showModal.value = false
  formRef.value?.restoreValidation()
}

// 编辑
const handleEdit = (row) => {
  openModal(row)
}

// 删除
const handleDelete = async (row) => {
  try {
    await api.deleteCategory(row.id)
    message.success('删除成功')
    loadData()
  } catch (error) {
    message.error('删除失败')
  }
}

// 提交表单
const handleSubmit = async () => {
  formRef.value?.validate(async (errors) => {
    if (errors) return

    try {
      if (isEdit.value) {
        await api.updateCategory(formData.id, formData)
        message.success('更新成功')
      } else {
        await api.createCategory(formData)
        message.success('添加成功')
      }
      closeModal()
      loadData()
    } catch (error) {
      message.error(isEdit.value ? '更新失败' : '添加失败')
    }
  })
}

// 初始加载
loadData()
</script> 