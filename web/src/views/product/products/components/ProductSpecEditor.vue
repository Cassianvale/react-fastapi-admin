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
        <div v-for="(row, rowIndex) in specRows" :key="rowIndex" class="spec-item">
          <div class="spec-item-content">
            <div class="spec-input-group">
              <div class="spec-label">规格名称</div>
              <NInput 
                v-model:value="row.key" 
                placeholder="如：颜色、尺寸" 
                class="spec-input"
                @update:value="() => handleUpdateRow(rowIndex)" 
              />
            </div>
            <div class="spec-input-group flex-grow-1">
              <div class="spec-label">规格值</div>
              <div class="spec-values-container">
                <div v-for="(value, valueIndex) in row.values" :key="`${rowIndex}-${valueIndex}`" class="spec-value-item">
                  <NInput 
                    v-model:value="row.values[valueIndex]" 
                    placeholder="如：红色、XL" 
                    class="spec-value-input"
                    @update:value="() => handleUpdateRow(rowIndex)" 
                  />
                  <NButton 
                    size="tiny" 
                    quaternary 
                    circle 
                    type="error" 
                    class="delete-value-btn"
                    @click="deleteSpecValue(rowIndex, valueIndex)"
                  >
                    <template #icon><NIcon><IconDelete /></NIcon></template>
                  </NButton>
                </div>
                <NButton size="small" text class="add-value-btn" @click="addSpecValue(rowIndex)">
                  <template #icon><NIcon><IconAdd /></NIcon></template>
                  添加规格值
                </NButton>
              </div>
            </div>
            <div class="spec-actions">
              <NButton 
                size="small" 
                quaternary 
                circle 
                type="error" 
                @click="deleteSpecRow(rowIndex)"
              >
                <template #icon><NIcon><IconDelete /></NIcon></template>
              </NButton>
            </div>
          </div>
          <NDivider v-if="rowIndex < specRows.length - 1" style="margin: 12px 0" />
        </div>
      </div>
    </div>

    <!-- JSON预览弹窗 -->
    <NModal v-model:show="showJsonPreview" preset="card" title="规格JSON预览" style="width: 500px">
      <div>
        <pre class="json-preview">{{ specificationPreviewJson }}</pre>
      </div>
      <template #footer>
        <div class="flex justify-end">
          <NButton @click="showJsonPreview = false">关闭</NButton>
        </div>
      </template>
    </NModal>
  </div>
</template>

<script setup>
import { ref, watch, reactive, h, onMounted, computed } from 'vue'
import { NButton, NCard, NEmpty, NInput, NIcon, NDivider, NModal } from 'naive-ui'
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
const IconAdd = () => h(Icon, { icon: 'material-symbols:add-circle-outline' })

// 规格编辑相关
const specRows = ref([])
const showJsonPreview = ref(false)
const specificationPreviewJson = ref('{}')

// 获取当前规格值的对象形式
const specificationObject = computed(() => {
  const specs = {}
  for (const row of specRows.value) {
    // 只有key有值时才添加
    if (row.key && row.key.trim() !== '') {
      // 只保留非空的规格值
      const validValues = row.values.filter(val => val && val.trim() !== '')
      if (validValues.length > 0) {
        specs[row.key] = validValues
      }
    }
  }
  return specs
})

// 当规格行更新时，更新输出的值
const handleUpdateRow = () => {
  // 使用计算属性获取当前规格对象
  const specs = specificationObject.value
  
  // 触发更新事件
  emit('update:value', specs)
  emit('update:modelValue', specs)
}

// 初始化规格行数据
const initSpecRows = (specsObj = {}) => {
  // 确保输入是有效的对象
  const validSpecs = typeof specsObj === 'object' && specsObj !== null ? specsObj : {}
  
  // 清空当前规格行
  specRows.value = []
  
  // 将对象转换为规格行数组
  for (const key in validSpecs) {
    if (Object.prototype.hasOwnProperty.call(validSpecs, key)) {
      const values = Array.isArray(validSpecs[key]) 
        ? [...validSpecs[key]] 
        : (validSpecs[key] ? [validSpecs[key]] : [])
      
      specRows.value.push({
        key: key,
        values: values.length > 0 ? values : [''] // 至少包含一个空值
      })
    }
  }
  
  // 如果没有规格行，添加一个空的规格行
  if (specRows.value.length === 0) {
    addSpecRow()
  }
}

// 添加规格行
const addSpecRow = () => {
  // 添加新的空规格行
  specRows.value.push({ key: '', values: [''] })
}

// 删除规格行
const deleteSpecRow = (index) => {
  // 删除指定索引的规格行
  specRows.value.splice(index, 1)
  
  // 如果删除后没有规格行，添加一个空的规格行
  if (specRows.value.length === 0) {
    addSpecRow()
  }
  
  // 更新规格值
  handleUpdateRow()
}

// 添加规格值
const addSpecValue = (rowIndex) => {
  specRows.value[rowIndex].values.push('')
}

// 删除规格值
const deleteSpecValue = (rowIndex, valueIndex) => {
  // 只有当存在多个规格值时才允许删除
  if (specRows.value[rowIndex].values.length > 1) {
    specRows.value[rowIndex].values.splice(valueIndex, 1)
    handleUpdateRow()
  } else {
    // 如果只剩一个规格值，则清空它
    specRows.value[rowIndex].values = ['']
    handleUpdateRow()
  }
}

// 预览JSON
const previewJSON = () => {
  // 使用计算属性获取当前规格对象并格式化为JSON
  specificationPreviewJson.value = JSON.stringify(specificationObject.value, null, 2)
  showJsonPreview.value = true
}

// 获取初始值
const getInitialValue = () => {
  // 优先使用modelValue，如果为空则使用value
  return Object.keys(props.modelValue || {}).length > 0
    ? props.modelValue
    : props.value
}

// 组件挂载时初始化
onMounted(() => {
  const initialValue = getInitialValue()
  initSpecRows(initialValue)
})

// 监听外部值变化
watch(
  [() => props.modelValue, () => props.value],
  ([newModelValue, newValue]) => {
    // 判断是否需要更新内部数据
    // 只在输入值有实际内容且与当前值不同时更新
    const externalValue = Object.keys(newModelValue || {}).length > 0
      ? newModelValue
      : newValue
    
    const currentValue = specificationObject.value
    
    // 检查是否与当前值不同
    const isDifferent = JSON.stringify(externalValue) !== JSON.stringify(currentValue)
    
    // 只有当外部值有内容且与当前值不同时才初始化
    if (Object.keys(externalValue || {}).length > 0 && isDifferent) {
      initSpecRows(externalValue)
    }
  },
  { deep: true }
)
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
  align-items: flex-start;
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

.spec-values-container {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.spec-value-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.spec-value-input {
  flex: 1;
}

.add-value-btn {
  margin-top: 4px;
  align-self: flex-start;
}

.delete-value-btn {
  flex-shrink: 0;
}

.spec-actions {
  display: flex;
  align-items: flex-start;
  justify-content: center;
  width: 40px;
}

.json-preview {
  background-color: #f8f8f8;
  padding: 12px;
  border-radius: 4px;
  font-family: monospace;
  white-space: pre-wrap;
  overflow-x: auto;
}
</style> 