<template>
  <div class="product-spec-editor-wrapper">
    <div class="spec-editor">
      <div class="spec-header flex justify-between mb-4">
        <div class="flex gap-2">
          <NButton size="small" type="primary" @click.stop="addSpecRow">
            <template #icon><NIcon><IconRowAdd /></NIcon></template>
            添加规格
          </NButton>
          <NButton v-if="specRows.length > 0" size="small" @click.stop="previewJSON">
            <template #icon><NIcon><IconCode /></NIcon></template>
            查看JSON
          </NButton>
        </div>
      </div>
      
      <NCard v-if="specRows.length === 0" size="small" class="empty-spec-card text-center py-6">
        <NEmpty description="暂无规格信息">
          <template #extra>
            <NButton type="primary" @click.stop="addSpecRow">添加第一个规格</NButton>
          </template>
        </NEmpty>
      </NCard>
      
      <div v-else class="spec-items-container">
        <div v-for="(row, index) in specRows" :key="index" class="spec-item">
          <div class="spec-item-content">
            <div class="spec-input-group">
              <div class="spec-label">规格名称</div>
              <NInput 
                v-model:value="row.key" 
                placeholder="如：颜色、尺寸" 
                class="spec-input"
                @update:value="updateSpecifications" 
              />
            </div>
            <div class="spec-input-group">
              <div class="spec-label">规格值</div>
              <NInput 
                v-model:value="row.value" 
                placeholder="如：红色、XL" 
                class="spec-input"
                @update:value="updateSpecifications" 
              />
            </div>
            <div class="spec-actions">
              <NButton 
                size="small" 
                quaternary 
                circle 
                type="error" 
                @click="deleteSpecRow(index)"
              >
                <template #icon><NIcon><IconDelete /></NIcon></template>
              </NButton>
            </div>
          </div>
          <NDivider v-if="index < specRows.length - 1" style="margin: 12px 0" />
        </div>
      </div>
    </div>

    <!-- JSON预览弹窗 -->
    <NModal v-model:show="showJsonPreview" preset="card" title="规格JSON预览" style="width: 500px">
      <NCode :code="specificationPreviewJson" language="json" />
      <template #footer>
        <div class="flex justify-end">
          <NButton @click="showJsonPreview = false">关闭</NButton>
        </div>
      </template>
    </NModal>
  </div>
</template>

<script setup>
import { ref, watch, h } from 'vue'
import { NButton, NCard, NEmpty, NInput, NIcon, NDivider, NModal, NCode } from 'naive-ui'
import { Icon } from '@iconify/vue'

const props = defineProps({
  value: {
    type: Object,
    default: () => ({})
  },
  modelValue: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:value', 'update:modelValue'])

// 图标组件
const IconRowAdd = () => h(Icon, { icon: 'material-symbols:add-box' })
const IconDelete = () => h(Icon, { icon: 'material-symbols:delete-outline' })
const IconCode = () => h(Icon, { icon: 'material-symbols:code' })

// 规格编辑相关
const specRows = ref([])
const showJsonPreview = ref(false)
const specificationPreviewJson = ref('')

// 确保规格是有效的对象
const ensureValidSpecifications = (specs) => {
  if (typeof specs !== 'object' || specs === null) {
    return {}
  }
  return specs
}

// 初始化规格行数据
const initSpecRows = (specs = {}) => {
  specRows.value = []
  const validSpecs = ensureValidSpecifications(specs)
  for (const key in validSpecs) {
    specRows.value.push({ key, value: validSpecs[key] })
  }
}

// 更新规格JSON数据并触发更新事件
const updateSpecifications = () => {
  const specs = {}
  for (const row of specRows.value) {
    if (row.key && row.key.trim() !== '') {
      specs[row.key] = row.value
    }
  }
  emit('update:value', specs)
  emit('update:modelValue', specs)
}

// 添加规格行
const addSpecRow = () => {
  specRows.value.push({ key: '', value: '' })
  // 添加延迟，确保DOM更新后再更新规格
  setTimeout(() => {
    updateSpecifications()
  }, 0)
}

// 删除规格行
const deleteSpecRow = (index) => {
  specRows.value.splice(index, 1)
  // 添加延迟，确保DOM更新后再更新规格
  setTimeout(() => {
    updateSpecifications()
  }, 0)
}

// 预览JSON
const previewJSON = () => {
  // 优先使用modelValue（如果使用v-model绑定），否则使用value
  const specs = Object.keys(props.modelValue || {}).length > 0 
    ? props.modelValue 
    : props.value
  specificationPreviewJson.value = JSON.stringify(specs, null, 2)
  showJsonPreview.value = true
}

// 监听value变化，更新规格行
watch(() => props.value, (newVal) => {
  initSpecRows(newVal)
}, { immediate: true })

// 同时监听modelValue变化，更新规格行
watch(() => props.modelValue, (newVal) => {
  if (Object.keys(newVal || {}).length > 0) {
    initSpecRows(newVal)
  }
}, { immediate: true })
</script>

<style scoped>
.product-spec-editor-wrapper {
  width: 100%;
}

.spec-editor {
  border: 1px solid #eee;
  border-radius: 6px;
  padding: 16px;
  background-color: #fafafa;
  width: 100%;
}

.empty-spec-card {
  background-color: #fcfcfc;
  border: 1px dashed #e0e0e0;
}

.spec-items-container {
  max-height: 300px;
  overflow-y: auto;
  padding: 8px;
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
  gap: 16px;
}

.spec-input-group {
  flex: 1;
}

.spec-label {
  font-size: 12px;
  color: #606266;
  margin-bottom: 4px;
  font-weight: 500;
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