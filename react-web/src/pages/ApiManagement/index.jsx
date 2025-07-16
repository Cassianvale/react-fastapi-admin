import { useState, useEffect } from 'react'
import {
  Table,
  Button,
  Space,
  Modal,
  Form,
  Input,
  Card,
  Row,
  Col,
  Tag,
  Popconfirm,
  Pagination,
  Tooltip,
  Select
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  SearchOutlined,
  ReloadOutlined,
  ClearOutlined,
  ApiOutlined,
  SyncOutlined,
  QuestionCircleOutlined
} from '@ant-design/icons'
import api from '@/api'
import { useErrorHandler } from '@/hooks/useErrorHandler'

const { TextArea } = Input
const { Option } = Select

const ApiManagement = () => {
  // 基础状态
  const [loading, setLoading] = useState(false)
  const [apis, setApis] = useState([])
  const [total, setTotal] = useState(0)
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  
  // 搜索状态
  const [searchForm] = Form.useForm()
  const [searchParams, setSearchParams] = useState({})
  
  // 模态框状态
  const [modalVisible, setModalVisible] = useState(false)
  const [modalForm] = Form.useForm()
  const [editingApi, setEditingApi] = useState(null)
  const [modalLoading, setModalLoading] = useState(false)
  
  // 刷新状态
  const [refreshLoading, setRefreshLoading] = useState(false)
  
  const { handleError, handleBusinessError, showSuccess } = useErrorHandler()

  // HTTP方法选项
  const httpMethods = [
    { label: 'GET', value: 'GET', color: 'green' },
    { label: 'POST', value: 'POST', color: 'blue' },
    { label: 'PUT', value: 'PUT', color: 'orange' },
    { label: 'DELETE', value: 'DELETE', color: 'red' },
    { label: 'PATCH', value: 'PATCH', color: 'purple' }
  ]

  // 获取API列表
  const fetchApis = async (page = currentPage, size = pageSize, search = searchParams) => {
    setLoading(true)
    try {
      const params = {
        page,
        page_size: size,
        ...search
      }
      const response = await api.apis.getList(params)
      setApis(response.data || [])
      setTotal(response.total || 0)
      setCurrentPage(response.page || page)
      setPageSize(response.page_size || size)
    } catch (error) {
      handleError(error, '获取API列表失败')
    } finally {
      setLoading(false)
    }
  }

  // 初始化数据
  useEffect(() => {
    fetchApis()
  }, [])

  // 搜索处理
  const handleSearch = async (values) => {
    const params = {}
    if (values.path) params.path = values.path
    if (values.summary) params.summary = values.summary
    if (values.tags) params.tags = values.tags
    
    setSearchParams(params)
    setCurrentPage(1)
    await fetchApis(1, pageSize, params)
  }

  // 清空搜索
  const handleClearSearch = async () => {
    searchForm.resetFields()
    setSearchParams({})
    setCurrentPage(1)
    await fetchApis(1, pageSize, {})
  }

  // 分页处理
  const handlePageChange = async (page, size) => {
    setCurrentPage(page)
    setPageSize(size)
    await fetchApis(page, size, searchParams)
  }

  // 打开添加/编辑模态框
  const handleOpenModal = (apiItem = null) => {
    setEditingApi(apiItem)
    setModalVisible(true)
    
    if (apiItem) {
      // 编辑模式
      modalForm.setFieldsValue({
        id: apiItem.id,
        path: apiItem.path || '',
        method: apiItem.method || 'GET',
        summary: apiItem.summary || '',
        tags: apiItem.tags || ''
      })
    } else {
      // 添加模式
      modalForm.resetFields()
      modalForm.setFieldsValue({
        method: 'GET'
      })
    }
  }

  // 关闭模态框
  const handleCloseModal = () => {
    setModalVisible(false)
    setEditingApi(null)
    modalForm.resetFields()
  }

  // 保存API
  const handleSaveApi = async (values) => {
    setModalLoading(true)
    try {
      if (editingApi) {
        // 更新API
        await api.apis.update({ ...values, id: editingApi.id })
        showSuccess('API更新成功')
      } else {
        // 创建API
        await api.apis.create(values)
        showSuccess('API创建成功')
      }
      handleCloseModal()
      await fetchApis()
    } catch (error) {
      handleBusinessError(error, editingApi ? 'API更新失败' : 'API创建失败')
    } finally {
      setModalLoading(false)
    }
  }

  // 删除API
  const handleDeleteApi = async (apiId) => {
    try {
      await api.apis.delete({ api_id: apiId })
      showSuccess('API删除成功')
      await fetchApis()
    } catch (error) {
      handleBusinessError(error, 'API删除失败')
    }
  }

  // 刷新API列表
  const handleRefreshApis = async () => {
    setRefreshLoading(true)
    try {
      await api.apis.refresh()
      showSuccess('API列表刷新成功')
      await fetchApis()
    } catch (error) {
      handleBusinessError(error, 'API刷新失败')
    } finally {
      setRefreshLoading(false)
    }
  }

  // 获取方法颜色
  const getMethodColor = (method) => {
    const methodObj = httpMethods.find(m => m.value === method)
    return methodObj ? methodObj.color : 'default'
  }

  // 表格列定义
  const columns = [
    {
      title: 'API路径',
      dataIndex: 'path',
      key: 'path',
      width: 300,
      render: (text) => (
        <div className="flex items-center">
          <ApiOutlined className="mr-2 text-blue-500" />
          <code className="bg-gray-100 px-2 py-1 rounded text-sm">{text || '-'}</code>
        </div>
      )
    },
    {
      title: '请求方法',
      dataIndex: 'method',
      key: 'method',
      width: 100,
      render: (method) => (
        <Tag color={getMethodColor(method)} className="font-mono">
          {method}
        </Tag>
      )
    },
    {
      title: 'API描述',
      dataIndex: 'summary',
      key: 'summary',
      width: 250,
      render: (text) => text || '-'
    },
    {
      title: 'API标签',
      dataIndex: 'tags',
      key: 'tags',
      width: 120,
      render: (tags) => (
        <Tag color="cyan">{tags || '未分类'}</Tag>
      )
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (text) => text ? new Date(text).toLocaleString('zh-CN') : '-'
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="编辑">
            <Button
              type="primary"
              size="small"
              icon={<EditOutlined />}
              onClick={() => handleOpenModal(record)}
            />
          </Tooltip>
          <Tooltip title="删除">
            <Popconfirm
              title="确认删除API？"
              description="删除后无法恢复，请谨慎操作"
              onConfirm={() => handleDeleteApi(record.id)}
              okText="确认"
              cancelText="取消"
              okType="danger"
            >
              <Button
                danger
                size="small"
                icon={<DeleteOutlined />}
              />
            </Popconfirm>
          </Tooltip>
        </Space>
      )
    }
  ]

  return (
    <div className="space-y-4">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center">
            <h1 className="text-2xl font-bold text-gray-800">API管理</h1>
            <Tooltip
              title={
                <div className="text-sm">
                  <div className="font-medium mb-1">API管理说明：</div>
                  <div>点击'刷新API'按钮可以自动从系统中扫描所有API接口并同步到数据库。</div>
                  <div>手动添加的API接口主要用于权限控制配置。</div>
                </div>
              }
              placement="right"
              overlayStyle={{ maxWidth: 350 }}
            >
              <QuestionCircleOutlined className="ml-2 text-gray-400 hover:text-blue-500 cursor-help text-base" />
            </Tooltip>
          </div>
          <p className="text-gray-500 mt-1">管理系统API接口，控制接口访问权限</p>
        </div>
        <Space>
          <Button
            type="default"
            icon={<SyncOutlined spin={refreshLoading} />}
            onClick={handleRefreshApis}
            loading={refreshLoading}
            className="border-green-500 text-green-500 hover:bg-green-50"
          >
            刷新API
          </Button>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => handleOpenModal()}
            className="bg-gradient-to-r from-blue-500 to-blue-600"
          >
            新增API
          </Button>
        </Space>
      </div>

      {/* API管理主卡片 */}
      <Card className="shadow-sm">
        {/* 搜索表单 */}
        <div className="mb-6 pb-4 border-b border-gray-200">
          <div className="flex items-center mb-3">
            <SearchOutlined className="mr-2 text-blue-500" />
            <span className="font-medium text-gray-700">筛选条件</span>
          </div>
          <Form
            form={searchForm}
            layout="inline"
            onFinish={handleSearch}
            className="w-full"
          >
                         <Form.Item name="path" className="mb-2">
               <Input
                 id="search_api_path"
                 placeholder="API路径"
                 prefix={<ApiOutlined />}
                 allowClear
                 style={{ width: 200 }}
               />
             </Form.Item>
             <Form.Item name="summary" className="mb-2">
               <Input
                 id="search_api_summary"
                 placeholder="API描述"
                 allowClear
                 style={{ width: 180 }}
               />
             </Form.Item>
             <Form.Item name="tags" className="mb-2">
               <Input
                 id="search_api_tags"
                 placeholder="API标签"
                 allowClear
                 style={{ width: 150 }}
               />
             </Form.Item>
            <Form.Item className="mb-2">
              <Space>
                <Button
                  type="primary"
                  htmlType="submit"
                  icon={<SearchOutlined />}
                  loading={loading}
                >
                  搜索
                </Button>
                <Button
                  icon={<ClearOutlined />}
                  onClick={handleClearSearch}
                >
                  清空
                </Button>
                <Button
                  icon={<ReloadOutlined />}
                  onClick={() => fetchApis()}
                  loading={loading}
                >
                  刷新
                </Button>
              </Space>
            </Form.Item>
          </Form>
        </div>

        {/* API列表 */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center">
              <ApiOutlined className="mr-2 text-blue-500" />
              <span className="font-medium text-gray-700">API列表</span>
            </div>
            <div className="text-sm text-gray-500">
              共 {total} 条记录
            </div>
          </div>
          
          <Table
            columns={columns}
            dataSource={apis}
            rowKey="id"
            loading={loading}
            pagination={false}
            scroll={{ x: 1000 }}
            size="middle"
            className="mb-4"
          />
          
          {/* 分页 */}
          <div className="flex justify-center pt-4 border-t border-gray-200">
            <Pagination
              current={currentPage}
              pageSize={pageSize}
              total={total}
              showSizeChanger
              showQuickJumper
              showTotal={(total, range) => 
                `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
              }
              onChange={handlePageChange}
              pageSizeOptions={['10', '20', '50', '100']}
            />
          </div>
        </div>
      </Card>

      {/* 添加/编辑API模态框 */}
      <Modal
        title={
          <div className="flex items-center">
            <ApiOutlined className="mr-2 text-blue-500" />
            {editingApi ? '编辑API' : '新增API'}
          </div>
        }
        open={modalVisible}
        onCancel={handleCloseModal}
        footer={[
          <Button key="cancel" onClick={handleCloseModal}>
            取消
          </Button>,
          <Button
            key="submit"
            type="primary"
            loading={modalLoading}
            onClick={() => modalForm.submit()}
          >
            {editingApi ? '更新' : '创建'}
          </Button>
        ]}
        width={600}
        destroyOnHidden
      >
        <Form
          form={modalForm}
          layout="vertical"
          onFinish={handleSaveApi}
          className="mt-4"
        >
          <Row gutter={16}>
            <Col span={16}>
                               <Form.Item
                   label="API路径"
                   name="path"
                   rules={[
                     { required: true, message: '请输入API路径' },
                     { pattern: /^\//, message: 'API路径必须以/开头' }
                   ]}
                 >
                   <Input 
                     id="modal_api_path"
                     placeholder="例如: /api/v1/users" 
                   />
                 </Form.Item>
               </Col>
               <Col span={8}>
                 <Form.Item
                   label="请求方法"
                   name="method"
                   rules={[{ required: true, message: '请选择请求方法' }]}
                 >
                   <Select 
                     id="modal_api_method"
                     placeholder="请选择"
                   >
                     {httpMethods.map(method => (
                       <Option key={method.value} value={method.value}>
                         <Tag color={method.color}>{method.label}</Tag>
                       </Option>
                     ))}
                   </Select>
                 </Form.Item>
            </Col>
          </Row>

                     <Form.Item
             label="API描述"
             name="summary"
             rules={[
               { required: true, message: '请输入API描述' },
               { max: 500, message: 'API描述不能超过500个字符' }
             ]}
           >
             <Input 
               id="modal_api_summary"
               placeholder="请输入API功能描述" 
             />
           </Form.Item>
           
           <Form.Item
             label="API标签"
             name="tags"
             rules={[
               { required: true, message: '请输入API标签' },
               { max: 100, message: 'API标签不能超过100个字符' }
             ]}
           >
             <Input 
               id="modal_api_tags"
               placeholder="例如: User, Role, System" 
             />
           </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default ApiManagement 