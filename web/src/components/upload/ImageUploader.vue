<template>
  <div class="image-uploader" :style="containerStyle">
    <!-- 预览区域 -->
    <div v-if="modelValue && !isUploading" class="preview-container" :style="sizeStyle">
      <img :src="modelValue" class="preview-image" />
      <div class="preview-actions">
        <n-button circle type="error" size="small" @click="showDeleteConfirm">
          <template #icon>
            <n-icon><icon-material-symbols:delete-outline /></n-icon>
          </template>
        </n-button>
        <n-button circle type="info" size="small" @click="handlePreview">
          <template #icon>
            <n-icon><icon-material-symbols:visibility-outline /></n-icon>
          </template>
        </n-button>
      </div>
    </div>
    
    <!-- 上传区域 -->
    <div v-else class="upload-container" @click="handleClick" :class="{ 'is-uploading': isUploading }" :style="sizeStyle">
      <n-spin v-if="isUploading" />
      <template v-else>
        <n-icon size="24" class="upload-icon">
          <icon-material-symbols:cloud-upload />
        </n-icon>
        <div class="upload-text">{{ placeholder || '点击上传图片' }}</div>
      </template>
    </div>
    
    <!-- 文件选择框 -->
    <input
      ref="fileInput"
      type="file"
      :accept="accept"
      style="display: none"
      @change="handleFileChange"
    />
    
    <!-- 预览对话框 -->
    <n-modal
      v-model:show="previewVisible"
      preset="card"
      style="width: 80%; max-width: 800px"
      title="图片预览"
    >
      <img :src="modelValue" style="width: 100%" />
    </n-modal>
    
    <!-- 删除确认对话框 -->
    <n-modal
      v-model:show="deleteConfirmVisible"
      preset="dialog"
      title="确认删除"
      positive-text="确认"
      negative-text="取消"
      type="warning"
      @positive-click="confirmDelete"
      @negative-click="cancelDelete"
    >
      <template #icon>
        <n-icon><icon-material-symbols:warning-outline /></n-icon>
      </template>
      <div>确定删除此图片吗？此操作将从服务器上永久删除该图片，且不可恢复。</div>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { NButton, NIcon, NModal, NSpin, useMessage } from 'naive-ui'
import api from '@/api'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  placeholder: {
    type: String,
    default: '点击上传图片'
  },
  accept: {
    type: String,
    default: 'image/jpeg,image/png,image/gif,image/webp'
  },
  maxSize: {
    type: Number,
    default: 5 // 5MB
  },
  deleteConfirm: {
    type: Boolean,
    default: true
  },
  width: {
    type: [Number, String],
    default: 200
  },
  height: {
    type: [Number, String],
    default: 200
  }
})

const emit = defineEmits(['update:modelValue', 'success', 'error', 'remove'])

const fileInput = ref(null)
const isUploading = ref(false)
const previewVisible = ref(false)
const deleteConfirmVisible = ref(false)
const isDeleting = ref(false)
const message = useMessage()

// URL转OSS文件Key
const getOssKeyFromUrl = (url) => {
  if (!url) return null
  
  try {
    // 解析URL以获取路径部分
    const urlObj = new URL(url)
    // 获取路径部分（去除域名和查询参数）
    let path = urlObj.pathname
    // 确保路径以 / 开头
    if (path.startsWith('/')) {
      path = path.substring(1)
    }
    return path
  } catch (error) {
    console.error('解析OSS路径出错:', error)
    return null
  }
}

// 计算大小样式
const sizeStyle = computed(() => {
  const width = typeof props.width === 'number' ? `${props.width}px` : props.width
  const height = typeof props.height === 'number' ? `${props.height}px` : props.height
  return {
    width,
    height
  }
})

// 计算容器样式
const containerStyle = computed(() => {
  if (props.width === '100%') {
    return { width: '100%' }
  }
  return {}
})

// 点击上传区域
const handleClick = () => {
  if (isUploading.value) return
  fileInput.value.click()
}

// 文件选择变化
const handleFileChange = async (e) => {
  const file = e.target.files[0]
  
  // 重置input, 确保相同的文件可以触发change事件
  e.target.value = null
  
  if (!file) return
  
  // 检查文件大小
  const maxSizeBytes = props.maxSize * 1024 * 1024
  if (file.size > maxSizeBytes) {
    message.error(`文件大小不能超过${props.maxSize}MB`)
    return
  }
  
  // 开始上传
  isUploading.value = true
  
  try {
    const res = await api.upload.uploadImage(file)
    if (res.code === 200) {
      emit('update:modelValue', res.data.url)
      emit('success', res.data)
      message.success('上传成功')
    } else {
      message.error(res.msg || '上传失败')
      emit('error', new Error(res.msg || '上传失败'))
    }
  } catch (error) {
    console.error('上传失败:', error)
    message.error('上传失败，请重试')
    emit('error', error)
  } finally {
    isUploading.value = false
  }
}

// 显示删除确认
const showDeleteConfirm = () => {
  if (props.deleteConfirm) {
    deleteConfirmVisible.value = true
  } else {
    confirmDelete()
  }
}

// 取消删除
const cancelDelete = () => {
  deleteConfirmVisible.value = false
}

// 确认删除
const confirmDelete = async () => {
  if (isDeleting.value) return
  
  isDeleting.value = true
  deleteConfirmVisible.value = false
  
  try {
    // 获取OSS文件路径
    const fileKey = getOssKeyFromUrl(props.modelValue)
    
    if (fileKey) {
      // 调用API删除OSS文件
      await api.upload.deleteFile(fileKey)
      message.success('图片已删除')
    }
    
    // 更新表单值
    emit('update:modelValue', '')
    emit('remove', { url: props.modelValue })
    
  } catch (error) {
    console.error('删除文件失败:', error)
    message.error('删除图片失败，请重试')
  } finally {
    isDeleting.value = false
  }
}

// 移除图片（兼容旧版处理方式）
const handleRemove = () => {
  showDeleteConfirm()
}

// 预览图片
const handlePreview = () => {
  previewVisible.value = true
}
</script>

<style scoped>
.image-uploader {
  display: inline-block;
  width: 100%;
}

.upload-container, .preview-container {
  position: relative;
  border: 1px dashed #d9d9d9;
  border-radius: 4px;
  background-color: #fafafa;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  transition: border-color 0.3s;
  overflow: hidden;
}

.upload-container:hover {
  border-color: var(--primary-color);
}

.upload-container.is-uploading {
  cursor: wait;
}

.upload-icon {
  margin-bottom: 8px;
  color: #999;
}

.upload-text {
  font-size: 14px;
  color: #999;
}

.preview-container {
  overflow: hidden;
  cursor: default;
}

.preview-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.preview-actions {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
  opacity: 0;
  transition: opacity 0.3s;
}

.preview-container:hover .preview-actions {
  opacity: 1;
}
</style> 