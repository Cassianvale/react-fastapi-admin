<script setup>
import { onMounted, ref, h, reactive, nextTick } from 'vue'
import { NInput, NSelect, NPopover, NDatePicker, NButton, NSpace, NModal, NCard, NInputNumber, NStatistic, NDivider } from 'naive-ui'
import { useMessage } from 'naive-ui'
import TheIcon from '@/components/icon/TheIcon.vue'

import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudTable from '@/components/table/CrudTable.vue'

import api from '@/api'
import { defineComponent } from 'vue'
// 导入 echarts 相关
import * as echarts from 'echarts/core'
import { BarChart, LineChart } from 'echarts/charts'
import { TooltipComponent, GridComponent, LegendComponent, TitleComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

// 注册必要的组件
echarts.use([
  BarChart,
  LineChart,
  TooltipComponent,
  GridComponent,
  LegendComponent,
  TitleComponent,
  CanvasRenderer
])

defineOptions({ name: '审计日志' })

const message = useMessage()
const $table = ref(null)
const queryItems = ref({})
const selectedRowKeys = ref([])
const showClearModal = ref(false)
const clearDays = ref(30)
const showStatisticsModal = ref(false)
const statisticsData = ref({})
const statisticsDays = ref(7)
const isLoading = ref(false)
const chartRef = ref(null)
let chartInstance = null

onMounted(() => {
  $table.value?.handleSearch()
})

// 获取当天的开始时间的时间戳
function getStartOfDayTimestamp() {
  const now = new Date()
  now.setHours(0, 0, 0, 0) // 将小时、分钟、秒和毫秒都设置为0
  return now.getTime()
}

// 获取当天的结束时间的时间戳
function getEndOfDayTimestamp() {
  const now = new Date()
  now.setHours(23, 59, 59, 999) // 将小时设置为23，分钟设置为59，秒设置为59，毫秒设置为999
  return now.getTime()
}

function formatTimestamp(timestamp) {
  const date = new Date(timestamp)

  const pad = (num) => num.toString().padStart(2, '0')

  const year = date.getFullYear()
  const month = pad(date.getMonth() + 1) // 月份从0开始，所以需要+1
  const day = pad(date.getDate())
  const hours = pad(date.getHours())
  const minutes = pad(date.getMinutes())
  const seconds = pad(date.getSeconds())

  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
}

const startOfDayTimestamp = getStartOfDayTimestamp()
const endOfDayTimestamp = getEndOfDayTimestamp()

queryItems.value.start_time = formatTimestamp(startOfDayTimestamp)
queryItems.value.end_time = formatTimestamp(endOfDayTimestamp)

const datetimeRange = ref([startOfDayTimestamp, endOfDayTimestamp])
const handleDateRangeChange = (value) => {
  if (value == null) {
    queryItems.value.start_time = null
    queryItems.value.end_time = null
  } else {
    queryItems.value.start_time = formatTimestamp(value[0])
    queryItems.value.end_time = formatTimestamp(value[1])
  }
}

const methodOptions = [
  { label: 'GET', value: 'GET' },
  { label: 'POST', value: 'POST' },
  { label: 'PUT', value: 'PUT' },
  { label: 'DELETE', value: 'DELETE' },
]

const logLevelOptions = [
  { label: '信息', value: 'info' },
  { label: '警告', value: 'warning' },
  { label: '错误', value: 'error' },
]

const operationTypeOptions = [
  { label: '查询', value: '查询' },
  { label: '创建', value: '创建' },
  { label: '更新', value: '更新' },
  { label: '删除', value: '删除' },
  { label: '其他', value: '其他' },
]

function formatJSON(data) {
  try {
    return typeof data === 'string' 
      ? JSON.stringify(JSON.parse(data), null, 2)
      : JSON.stringify(data, null, 2)
  } catch (e) {
    return data || '无数据'
  }
}

// 导出日志
async function handleExport() {
  try {
    const response = await api.auditLogs.export({
      ...queryItems.value
    })
    message.success(response.msg || '导出成功')
  } catch (error) {
    message.error(error.message || '导出失败')
  }
}

// 删除日志
async function handleDelete(id) {
  try {
    await api.auditLogs.delete(id)
    message.success('删除成功')
    $table.value?.handleSearch()
  } catch (error) {
    message.error(error.message || '删除失败')
  }
}

// 批量删除日志
async function handleBatchDelete() {
  if (selectedRowKeys.value.length === 0) {
    message.warning('请先选择要删除的日志')
    return
  }
  
  try {
    await api.auditLogs.batchDelete(selectedRowKeys.value)
    message.success('批量删除成功')
    selectedRowKeys.value = []
    $table.value?.handleSearch()
  } catch (error) {
    message.error(error.message || '批量删除失败')
  }
}

// 清空日志
async function handleClear() {
  try {
    await api.auditLogs.clear({ days: clearDays.value })
    message.success('清空成功')
    showClearModal.value = false
    $table.value?.handleSearch()
  } catch (error) {
    message.error(error.message || '清空失败')
  }
}

// 初始化ECharts图表
function initChart() {
  if (chartInstance) {
    chartInstance.dispose()
  }
  
  nextTick(() => {
    if (chartRef.value) {
      chartInstance = echarts.init(chartRef.value)
      updateChart()
    }
  })
}

// 更新图表数据
function updateChart() {
  if (!chartInstance || !statisticsData.value || Object.keys(statisticsData.value).length === 0) return
  
  const dates = Object.keys(statisticsData.value)
  const values = Object.values(statisticsData.value)
  
  // 图表配置
  const option = {
    title: {
      text: '审计日志统计',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: dates,
      axisTick: {
        alignWithLabel: true
      }
    },
    yAxis: {
      type: 'value',
      name: '日志数量'
    },
    series: [
      {
        name: '日志数量',
        type: 'bar',
        barWidth: '60%',
        data: values,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#83bff6' },
            { offset: 0.5, color: '#188df0' },
            { offset: 1, color: '#188df0' }
          ])
        },
        emphasis: {
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#2378f7' },
              { offset: 0.7, color: '#2378f7' },
              { offset: 1, color: '#83bff6' }
            ])
          }
        }
      },
      {
        name: '趋势线',
        type: 'line',
        smooth: true,
        data: values,
        symbolSize: 8,
        itemStyle: {
          color: '#ff9800'
        },
        lineStyle: {
          width: 2,
          color: '#ff9800'
        }
      }
    ]
  }
  
  // 设置图表配置
  chartInstance.setOption(option)
}

// 处理窗口大小变化
function handleResize() {
  if (chartInstance) {
    chartInstance.resize()
  }
}

// 获取统计数据
async function handleShowStatistics() {
  isLoading.value = true
  try {
    const response = await api.auditLogs.getStatistics({ days: statisticsDays.value })
    statisticsData.value = response.data
    showStatisticsModal.value = true
    
    // 在弹窗显示后初始化图表
    nextTick(() => {
      initChart()
      
      // 监听窗口大小变化
      window.addEventListener('resize', handleResize)
    })
  } catch (error) {
    message.error(error.message || '获取统计数据失败')
  } finally {
    isLoading.value = false
  }
}

// 在弹窗关闭时移除事件监听
function handleModalClose() {
  window.removeEventListener('resize', handleResize)
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
}

// 监听统计天数变化，更新图表
function handleStatisticsDaysChange(value) {
  statisticsDays.value = value
  handleShowStatistics()
}

const columns = [
  {
    type: 'selection'
  },
  {
    title: '用户名称',
    key: 'username',
    width: 100,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '接口概要',
    key: 'summary',
    align: 'center',
    width: 150,
    ellipsis: { tooltip: true },
  },
  {
    title: '功能模块',
    key: 'module',
    align: 'center',
    width: 120,
    ellipsis: { tooltip: true },
  },
  {
    title: '请求方法',
    key: 'method',
    align: 'center',
    width: 80,
    ellipsis: { tooltip: true },
  },
  {
    title: 'IP地址',
    key: 'ip_address',
    align: 'center',
    width: 120,
    ellipsis: { tooltip: true },
  },
  {
    title: '操作类型',
    key: 'operation_type',
    align: 'center',
    width: 80,
    ellipsis: { tooltip: true },
  },
  {
    title: '日志级别',
    key: 'log_level',
    align: 'center',
    width: 80,
    render: (row) => {
      let color = 'default'
      if (row.log_level === 'info') color = 'info'
      if (row.log_level === 'warning') color = 'warning'
      if (row.log_level === 'error') color = 'error'
      
      return h('span', { style: `color: ${color === 'info' ? '#1890ff' : color === 'warning' ? '#faad14' : color === 'error' ? '#f5222d' : 'inherit'}` }, row.log_level)
    }
  },
  {
    title: '请求体',
    key: 'request_body',
    align: 'center',
    width: 80,
    render: (row) => {
      return h(
        NPopover,
        {
          trigger: 'hover',
          placement: 'right',
        },
        {
          trigger: () =>
            h('div', { style: 'cursor: pointer;' }, [h(TheIcon, { icon: 'carbon:data-view' })]),
          default: () =>
            h(
              'pre',
              {
                style:
                  'max-height: 400px; overflow: auto; background-color: #f5f5f5; padding: 8px; border-radius: 4px;',
              },
              formatJSON(row.request_args)
            ),
        }
      )
    },
  },
  {
    title: '响应体',
    key: 'response_body',
    align: 'center',
    width: 80,
    render: (row) => {
      return h(
        NPopover,
        {
          trigger: 'hover',
          placement: 'right',
        },
        {
          trigger: () =>
            h('div', { style: 'cursor: pointer;' }, [h(TheIcon, { icon: 'carbon:data-view' })]),
          default: () =>
            h(
              'pre',
              {
                style:
                  'max-height: 400px; overflow: auto; background-color: #f5f5f5; padding: 8px; border-radius: 4px;',
              },
              formatJSON(row.response_body)
            ),
        }
      )
    },
  },
  {
    title: '响应时间(ms)',
    key: 'response_time',
    align: 'center',
    width: 110,
    ellipsis: { tooltip: true },
  },
  {
    title: '操作时间',
    key: 'created_at',
    align: 'center',
    width: 160,
    ellipsis: { tooltip: true },
  },
  {
    title: '操作',
    key: 'actions',
    align: 'center',
    width: 80,
    fixed: 'right',
    render: (row) => {
      return h(
        NButton,
        {
          size: 'small',
          type: 'error',
          onClick: () => handleDelete(row.id)
        },
        { default: () => '删除' }
      )
    }
  }
]
</script>

<template>
  <!-- 业务页面 -->
  <CommonPage>
    <!-- 表格工具栏 -->
    <template #action>
      <NSpace>
        <NButton type="primary" @click="handleShowStatistics">
          <TheIcon icon="majesticons:chart-line" />
          <span class="ml-1">统计分析</span>
        </NButton>
        <NButton type="info" @click="handleExport">
          <TheIcon icon="mdi:file-export" />
          <span class="ml-1">导出日志</span>
        </NButton>
        <NButton type="error" @click="handleBatchDelete" :disabled="selectedRowKeys.length === 0">
          <TheIcon icon="material-symbols:delete" />
          <span class="ml-1">批量删除</span>
        </NButton>
        <NButton type="warning" @click="showClearModal = true">
          <TheIcon icon="material-symbols:cleaning-services" />
          <span class="ml-1">清空日志</span>
        </NButton>
      </NSpace>
    </template>
    
    <!-- 表格 -->
    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      v-model:checked-row-keys="selectedRowKeys"
      :columns="columns"
      :get-data="api.auditLogs.getList"
    >
      <template #queryBar>
        <QueryBarItem label="用户名称" :label-width="70">
          <NInput
            v-model:value="queryItems.username"
            clearable
            type="text"
            placeholder="请输入用户名称"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
        <QueryBarItem label="功能模块" :label-width="70">
          <NInput
            v-model:value="queryItems.module"
            clearable
            type="text"
            placeholder="请输入功能模块"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
        <QueryBarItem label="接口概要" :label-width="70">
          <NInput
            v-model:value="queryItems.summary"
            clearable
            type="text"
            placeholder="请输入接口概要"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
        <QueryBarItem label="请求方法" :label-width="70">
          <NSelect
            v-model:value="queryItems.method"
            style="width: 180px"
            :options="methodOptions"
            clearable
            placeholder="请选择请求方法"
          />
        </QueryBarItem>
        <QueryBarItem label="IP地址" :label-width="70">
          <NInput
            v-model:value="queryItems.ip_address"
            clearable
            type="text"
            placeholder="请输入IP地址"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
        <QueryBarItem label="操作类型" :label-width="70">
          <NSelect
            v-model:value="queryItems.operation_type"
            style="width: 180px"
            :options="operationTypeOptions"
            clearable
            placeholder="请选择操作类型"
          />
        </QueryBarItem>
        <QueryBarItem label="日志级别" :label-width="70">
          <NSelect
            v-model:value="queryItems.log_level"
            style="width: 180px"
            :options="logLevelOptions"
            clearable
            placeholder="请选择日志级别"
          />
        </QueryBarItem>
        <QueryBarItem label="操作时间" :label-width="70">
          <NDatePicker
            v-model:value="datetimeRange"
            type="datetimerange"
            clearable
            style="width: 380px"
            @update:value="handleDateRangeChange"
          />
        </QueryBarItem>
      </template>
    </CrudTable>
    
    <!-- 清空日志弹窗 -->
    <NModal v-model:show="showClearModal" preset="dialog" title="清空日志">
      <div>确定要清空日志吗？此操作不可恢复。</div>
      <div class="mt-4">
        <NInputNumber
          v-model:value="clearDays"
          :min="1"
          :max="365"
          placeholder="清空多少天前的日志"
        >
          <template #prefix>清空</template>
          <template #suffix>天前的日志</template>
        </NInputNumber>
        <div class="text-gray-400 mt-2">不填则清空所有日志</div>
      </div>
      <template #action>
        <NButton type="default" @click="showClearModal = false">取消</NButton>
        <NButton type="error" @click="handleClear">确定清空</NButton>
      </template>
    </NModal>
    
    <!-- 统计分析弹窗 -->
    <NModal 
      v-model:show="showStatisticsModal" 
      preset="card" 
      style="width: 800px" 
      title="审计日志统计分析"
      @update:show="val => !val && handleModalClose()"
    >
      <template #header>
        <div class="flex justify-between items-center">
          <span>审计日志统计分析</span>
          <NInputNumber
            v-model:value="statisticsDays"
            :min="3"
            :max="30"
            :disabled="isLoading"
            style="width: 200px"
            @update:value="handleStatisticsDaysChange"
          >
            <template #suffix>天</template>
          </NInputNumber>
        </div>
      </template>
      
      <div class="p-4">
        <NCard v-if="Object.keys(statisticsData).length > 0">
          <div class="flex justify-around mb-6">
            <NStatistic label="总日志数">
              {{ Object.values(statisticsData).reduce((sum, value) => sum + value, 0) }}
            </NStatistic>
            <NStatistic label="平均每日日志数">
              {{ Math.round(
                Object.values(statisticsData).reduce((sum, value) => sum + value, 0) / 
                Object.keys(statisticsData).length
              ) }}
            </NStatistic>
            <NStatistic label="最高日志数">
              {{ Math.max(...Object.values(statisticsData)) }}
            </NStatistic>
            <NStatistic label="最低日志数">
              {{ Math.min(...Object.values(statisticsData)) }}
            </NStatistic>
          </div>
          
          <NDivider />
          
          <!-- ECharts图表 -->
          <div ref="chartRef" style="height: 400px; width: 100%;"></div>
        </NCard>
        <div v-else class="text-center py-8">暂无统计数据</div>
      </div>
    </NModal>
  </CommonPage>
</template>

<style scoped>
</style>
