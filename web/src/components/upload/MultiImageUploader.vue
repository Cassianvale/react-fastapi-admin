<template>
  <div class="multi-image-uploader">
    <div class="images-container">
      <!-- 已上传的图片列表 -->
      <div
        v-for="(image, index) in imageList"
        :key="index"
        class="image-item"
        :style="getItemStyle"
      >
        <img :src="image" class="preview-image" @click="previewImage(image)" />
        <div class="image-actions">
          <n-button circle type="error" size="tiny" @click="handleRemoveImage(index)">
            <template #icon>
              <n-icon><icon-material-symbols:delete-outline /></n-icon>
            </template>
          </n-button>
          <n-button circle type="info" size="tiny" @click="previewImage(image)">
            <template #icon>
              <n-icon><icon-material-symbols:visibility-outline /></n-icon>
            </template>
          </n-button>
        </div>
      </div>
      
      <!-- 上传按钮 -->
      <div 
        v-if="imageList.length < maxCount" 
        class="image-upload-btn" 
        @click="handleUploadClick"
        :class="{ 'is-uploading': isUploading }"
        :style="getItemStyle"
      >
        <n-spin v-if="isUploading" />
        <template v-else>
          <n-icon size="32" class="upload-icon">
            <icon-material-symbols:add-circle-outline />
          </n-icon>
          <div class="upload-text">{{ placeholder }}</div>
        </template>
      </div>
    </div>
    
    <!-- 图片数量提示 -->
    <div class="image-count-tip">
      <span>{{ imageList.length }}/{{ maxCount }}</span>
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
      <img :src="previewUrl" style="width: 100%" />
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
import { ref, computed, watch } from 'vue'
import { NButton, NIcon, NModal, NSpin, useMessage } from 'naive-ui'
import api from '@/api'

const props = defineProps({
  modelValue: {
    type: [String, Array],
    default: () => []
  },
  placeholder: {
    type: String,
    default: '上传图片'
  },
  accept: {
    type: String,
    default: 'image/jpeg,image/png,image/gif,image/webp'
  },
  maxSize: {
    type: Number,
    default: 5 // 5MB
  },
  maxCount: {
    type: Number,
    default: 9 // 最多上传9张图片
  },
  deleteConfirm: {
    type: Boolean,
    default: true
  },
  imageWidth: {
    type: Number,
    default: 150
  },
  imageHeight: {
    type: Number,
    default: 150
  }
})

const emit = defineEmits(['update:modelValue', 'success', 'error', 'remove'])

const fileInput = ref(null)
const isUploading = ref(false)
const previewVisible = ref(false)
const previewUrl = ref('')
const deleteConfirmVisible = ref(false)
const imageToDelete = ref(null)
const message = useMessage()

// 处理输入值是字符串还是数组的情况
const imageList = computed(() => {
  if (!props.modelValue) return []
  if (typeof props.modelValue === 'string') {
    return props.modelValue ? [props.modelValue] : []
  }
  return props.modelValue
})

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

// 点击上传按钮
const handleUploadClick = () => {
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
      // 添加新图片到列表
      let newImages = [...imageList.value]
      newImages.push(res.data.url)
      
      // 更新v-model值
      if (typeof props.modelValue === 'string') {
        // 如果之前是字符串模式，使用第一张图片的URL
        emit('update:modelValue', newImages[0])
      } else {
        // 如果是数组模式，更新整个数组
        emit('update:modelValue', newImages)
      }
      
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

// 预览图片
const previewImage = (url) => {
  previewUrl.value = url
  previewVisible.value = true
}

// 处理删除图片
const handleRemoveImage = (index) => {
  if (props.deleteConfirm) {
    imageToDelete.value = { index, url: imageList.value[index] }
    deleteConfirmVisible.value = true
  } else {
    deleteImage(index)
  }
}

// 取消删除
const cancelDelete = () => {
  deleteConfirmVisible.value = false
  imageToDelete.value = null
}

// 确认删除
const confirmDelete = async () => {
  if (!imageToDelete.value) return
  
  const { index, url } = imageToDelete.value
  deleteConfirmVisible.value = false
  
  try {
    // 获取OSS文件路径
    const fileKey = getOssKeyFromUrl(url)
    
    if (fileKey) {
      // 调用API删除OSS文件
      await api.upload.deleteFile(fileKey)
      message.success('图片已删除')
    }
    
    // 从列表中移除
    deleteImage(index)
    
  } catch (error) {
    console.error('删除文件失败:', error)
    message.error('删除图片失败，请重试')
  } finally {
    imageToDelete.value = null
  }
}

// 从列表中删除图片
const deleteImage = (index) => {
  const newImages = [...imageList.value]
  const removedUrl = newImages.splice(index, 1)[0]
  
  // 更新v-model值
  if (typeof props.modelValue === 'string') {
    // 如果之前是字符串模式，使用第一张图片的URL或空字符串
    emit('update:modelValue', newImages.length > 0 ? newImages[0] : '')
  } else {
    // 如果是数组模式，更新整个数组
    emit('update:modelValue', newImages)
  }
  
  // 触发remove事件
  emit('remove', { url: removedUrl, index })
}

// 计算图片和上传按钮的尺寸样式
const getItemStyle = computed(() => {
  return {
    width: `${props.imageWidth}px`,
    height: `${props.imageHeight}px`
  }
})
</script>

<style scoped>
.multi-image-uploader {
  width: 100%;
}

.images-container {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  margin-bottom: 10px;
}

/* 响应式布局调整 */
@media (max-width: 768px) {
  .images-container {
    gap: 10px;
  }
}

@media (max-width: 480px) {
  .images-container {
    gap: 8px;
  }
}

.image-item, .image-upload-btn {
  position: relative;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  transition: transform 0.2s, box-shadow 0.2s;
  margin-bottom: 10px;
}

.image-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.image-item {
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #f8f8f8;
}

.preview-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  cursor: pointer;
}

.image-actions {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
  opacity: 0;
  transition: opacity 0.3s;
}

.image-item:hover .image-actions {
  opacity: 1;
}

.image-upload-btn {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  border: 2px dashed #d9d9d9;
  background-color: #fafafa;
  cursor: pointer;
  transition: border-color 0.3s, transform 0.2s;
}

.image-upload-btn:hover {
  border-color: var(--primary-color);
  transform: translateY(-2px);
}

.image-upload-btn.is-uploading {
  cursor: wait;
}

.upload-icon {
  margin-bottom: 8px;
  color: #666;
}

.upload-text {
  font-size: 13px;
  color: #666;
}

.image-count-tip {
  margin-top: 8px;
  font-size: 13px;
  color: #666;
  text-align: right;
}
</style> 