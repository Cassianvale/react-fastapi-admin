import { useState, useEffect } from 'react'
import {
  Table,
  Button,
  Space,
  Modal,
  Form,
  Input,
  Select,
  Card,
  Row,
  Col,
  Tag,
  Popconfirm,
  Pagination,
  Divider,
  Tooltip
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  SearchOutlined,
  ReloadOutlined,
  UserOutlined,
  LockOutlined,
  ClearOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons'
import api from '@/api'
import { useErrorHandler } from '@/hooks/useErrorHandler'
import PasswordStrengthIndicator from '@/components/PasswordStrengthIndicator'

const UserManagement = () => {
  // 基础状态
  const [loading, setLoading] = useState(false)
  const [passwordStrength, setPasswordStrength] = useState(null)
  const [users, setUsers] = useState([])
  const [total, setTotal] = useState(0)
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  
  // 搜索状态
  const [searchForm] = Form.useForm()
  const [searchParams, setSearchParams] = useState({})
  
  // 模态框状态
  const [modalVisible, setModalVisible] = useState(false)
  const [modalForm] = Form.useForm()
  const [editingUser, setEditingUser] = useState(null)
  const [modalLoading, setModalLoading] = useState(false)
  
  // 角色和部门数据
  const [roles, setRoles] = useState([])
  const [departments, setDepartments] = useState([])
  
  const { handleError, handleBusinessError, showSuccess } = useErrorHandler()

  // 获取用户列表
  const fetchUsers = async (page = currentPage, size = pageSize, search = searchParams) => {
    setLoading(true)
    try {
      const params = {
        page,
        page_size: size,
        ...search
      }
      const response = await api.users.getList(params)
      setUsers(response.data || [])
      setTotal(response.total || 0)
      setCurrentPage(response.page || page)
      setPageSize(response.page_size || size)
    } catch (error) {
      handleError(error, '获取用户列表失败')
    } finally {
      setLoading(false)
    }
  }

  // 获取角色列表
  const fetchRoles = async () => {
    try {
      const response = await api.roles.getList({ page: 1, page_size: 1000 })
      setRoles(response.data || [])
    } catch (error) {
      console.error('获取角色列表失败:', error)
    }
  }

  // 获取部门列表
  const fetchDepartments = async () => {
    try {
      const response = await api.departments.getList({ page: 1, page_size: 1000 })
      setDepartments(response.data || [])
    } catch (error) {
      console.error('获取部门列表失败:', error)
    }
  }

  // 初始化数据
  useEffect(() => {
    fetchUsers()
    fetchRoles()
    fetchDepartments()
  }, [])

  // 处理模态框表单数据设置
  useEffect(() => {
    if (modalVisible) {
      if (editingUser) {
        // 编辑模式，确保空值显示为空字符串
        modalForm.setFieldsValue({
          id: editingUser.id,
          username: editingUser.username || '',
          email: editingUser.email || '',
          nickname: editingUser.nickname || '',
          phone: editingUser.phone || '',
          is_active: editingUser.is_active,
          is_superuser: editingUser.is_superuser,
          dept_id: editingUser.dept?.id,
          role_ids: editingUser.roles?.map(role => role.id) || []
        })
      } else {
        // 添加模式
        modalForm.resetFields()
        modalForm.setFieldsValue({
          is_active: true,
          is_superuser: false
        })
      }
    }
  }, [modalVisible, editingUser, modalForm])

  // 搜索处理
  const handleSearch = async (values) => {
    const params = {}
    if (values.username) params.username = values.username
    if (values.nickname) params.nickname = values.nickname
    if (values.dept_id) params.dept_id = values.dept_id
    
    setSearchParams(params)
    setCurrentPage(1)
    await fetchUsers(1, pageSize, params)
  }

  // 清空搜索
  const handleClearSearch = async () => {
    searchForm.resetFields()
    setSearchParams({})
    setCurrentPage(1)
    await fetchUsers(1, pageSize, {})
  }

  // 分页处理
  const handlePageChange = async (page, size) => {
    setCurrentPage(page)
    setPageSize(size)
    await fetchUsers(page, size, searchParams)
  }

  // 打开添加/编辑模态框
  const handleOpenModal = (user = null) => {
    setEditingUser(user)
    setModalVisible(true)
  }

  // 关闭模态框
  const handleCloseModal = () => {
    setModalVisible(false)
    setEditingUser(null)
    modalForm.resetFields()
  }

  // 保存用户
  const handleSaveUser = async (values) => {
    setModalLoading(true)
    try {
      // 处理空值，当字段为空时删除该字段，避免后端验证错误
      const processedValues = { ...values }
      
      // 清理字段值
      if (values.email !== undefined) {
        processedValues.email = values.email?.trim() || undefined
      }
      if (values.phone !== undefined) {
        processedValues.phone = values.phone?.trim() || undefined
      }
      if (values.nickname !== undefined) {
        processedValues.nickname = values.nickname?.trim() || undefined
      }
      
      if (editingUser) {
        // 更新用户
        await api.users.update(processedValues)
        showSuccess('用户更新成功')
      } else {
        // 创建用户
        await api.users.create(processedValues)
        showSuccess('用户创建成功')
      }
      handleCloseModal()
      await fetchUsers()
    } catch (error) {
      handleBusinessError(error, editingUser ? '用户更新失败' : '用户创建失败')
    } finally {
      setModalLoading(false)
    }
  }

  // 删除用户
  const handleDeleteUser = async (userId) => {
    try {
      await api.users.delete({ user_id: userId })
      showSuccess('用户删除成功')
      await fetchUsers()
    } catch (error) {
      handleBusinessError(error, '用户删除失败')
    }
  }

  // 重置密码
  const handleResetPassword = async (userId) => {
    try {
      await api.users.resetPassword({ user_id: userId })
      showSuccess('密码重置成功，新密码为: 123456')
    } catch (error) {
      handleBusinessError(error, '密码重置失败')
    }
  }

  // 表格列定义
  const columns = [
    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
      width: 120,
      render: (text) => (
        <div className="flex items-center">
          <UserOutlined className="mr-2 text-blue-500" />
          <span className="font-medium">{text || '-'}</span>
        </div>
      )
    },
    {
      title: '昵称',
      dataIndex: 'nickname',
      key: 'nickname',
      width: 120,
      render: (text) => text || '-'
    },
    {
      title: '邮箱',
      dataIndex: 'email',
      key: 'email',
      width: 200,
      render: (text) => text || '-'
    },
    {
      title: '手机号',
      dataIndex: 'phone',
      key: 'phone',
      width: 120,
      render: (text) => text || '-'
    },
    {
      title: '部门',
      key: 'dept',
      width: 120,
      render: (_, record) => (
        <Tag color="blue">
          {record.dept?.name || '未分配'}
        </Tag>
      )
    },
    {
      title: '角色',
      key: 'roles',
      width: 150,
      render: (_, record) => (
        <div className="flex flex-wrap gap-1">
          {record.roles?.length > 0 ? (
            record.roles.map(role => (
              <Tag key={role.id} color="green" className="mb-1">
                {role.name}
              </Tag>
            ))
          ) : (
            <Tag>未分配角色</Tag>
          )}
        </div>
      )
    },
    {
      title: '状态',
      key: 'status',
      width: 100,
      render: (_, record) => (
        <div className="flex flex-col gap-1">
          <Tag color={record.is_active ? 'success' : 'error'}>
            {record.is_active ? '正常' : '禁用'}
          </Tag>
          {record.is_superuser && (
            <Tag color="gold">超级管理员</Tag>
          )}
        </div>
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
      width: 200,
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
          <Tooltip title="重置密码">
            <Popconfirm
              title="确认重置密码？"
              description="密码将重置为：123456"
              onConfirm={() => handleResetPassword(record.id)}
              okText="确认"
              cancelText="取消"
            >
              <Button
                size="small"
                icon={<LockOutlined />}
                className="text-orange-500 border-orange-500 hover:bg-orange-50"
              />
            </Popconfirm>
          </Tooltip>
          <Tooltip title="删除">
            <Popconfirm
              title="确认删除用户？"
              description="删除后无法恢复，请谨慎操作"
              onConfirm={() => handleDeleteUser(record.id)}
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
          <h1 className="text-2xl font-bold text-gray-800">用户管理</h1>
          <p className="text-gray-500 mt-1">管理系统用户账户、角色权限和基本信息</p>
        </div>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => handleOpenModal()}
          className="bg-gradient-to-r from-blue-500 to-blue-600"
        >
          新增用户
        </Button>
      </div>

      {/* 用户管理主卡片 */}
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
            <Form.Item name="username" className="mb-2">
              <Input
                id="search_username"
                placeholder="用户名"
                prefix={<UserOutlined />}
                allowClear
                style={{ width: 160 }}
                autoComplete="username"
              />
            </Form.Item>
            <Form.Item name="nickname" className="mb-2">
              <Input
                id="search_nickname"
                placeholder="昵称"
                allowClear
                style={{ width: 180 }}
                autoComplete="off"
              />
            </Form.Item>
            <Form.Item name="dept_id" className="mb-2">
              <Select
                id="search_dept_id"
                placeholder="选择部门"
                allowClear
                style={{ width: 150 }}
                options={departments.map(dept => ({
                  label: dept.name,
                  value: dept.id
                }))}
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
                  onClick={() => fetchUsers()}
                  loading={loading}
                >
                  刷新
                </Button>
              </Space>
            </Form.Item>
          </Form>
        </div>

        {/* 用户列表 */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center">
              <UserOutlined className="mr-2 text-blue-500" />
              <span className="font-medium text-gray-700">用户列表</span>
            </div>
            <div className="text-sm text-gray-500">
              共 {total} 条记录
            </div>
          </div>
          
          <Table
            columns={columns}
            dataSource={users}
            rowKey="id"
            loading={loading}
            pagination={false}
            scroll={{ x: 1200 }}
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

      {/* 添加/编辑用户模态框 */}
      <Modal
        title={
          <div className="flex items-center">
            <UserOutlined className="mr-2 text-blue-500" />
            {editingUser ? '编辑用户' : '新增用户'}
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
            {editingUser ? '更新' : '创建'}
          </Button>
        ]}
        width={600}
        destroyOnHidden
      >
        <Form
          form={modalForm}
          layout="vertical"
          onFinish={handleSaveUser}
          className="mt-4"
        >
          {editingUser && (
            <Form.Item name="id" hidden>
              <Input />
            </Form.Item>
          )}
          
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="用户名"
                name="username"
                rules={[
                  { required: true, message: '请输入用户名' },
                  { min: 3, max: 20, message: '用户名长度为3-20个字符' },
                  { pattern: /^[a-zA-Z0-9_]+$/, message: '用户名只能包含字母、数字和下划线' }
                ]}
              >
                <Input
                  id="modal_username"
                  placeholder="请输入用户名"
                  disabled={!!editingUser}
                  autoComplete="username"
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="昵称"
                name="nickname"
                rules={[
                  { max: 30, message: '昵称不能超过30个字符' }
                ]}
              >
                <Input 
                  id="modal_nickname"
                  placeholder="请输入昵称"
                  autoComplete="nickname"
                />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="邮箱"
                name="email"
                rules={[
                  { required: true, message: '请输入邮箱地址' },
                  { type: 'email', message: '请输入正确的邮箱格式' }
                ]}
              >
                <Input 
                  id="modal_email"
                  placeholder="请输入邮箱地址"
                  autoComplete="email"
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="手机号"
                name="phone"
                rules={[
                  { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号格式' }
                ]}
              >
                <Input 
                  id="modal_phone"
                  placeholder="请输入手机号"
                  autoComplete="tel"
                />
              </Form.Item>
            </Col>
          </Row>

          {!editingUser && (
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  label="密码"
                  name="password"
                  rules={[
                    { required: true, message: '请输入密码' },
                    () => ({
                      validator(_, value) {
                        if (!value) return Promise.resolve()
                        
                        // 检查密码长度
                        if (value.length < 8) {
                          return Promise.reject(new Error('密码长度不能少于8个字符'))
                        }
                        
                        // 检查大写字母
                        if (!/[A-Z]/.test(value)) {
                          return Promise.reject(new Error('密码必须包含至少一个大写字母'))
                        }
                        
                        // 检查小写字母
                        if (!/[a-z]/.test(value)) {
                          return Promise.reject(new Error('密码必须包含至少一个小写字母'))
                        }
                        
                        // 检查数字
                        if (!/\d/.test(value)) {
                          return Promise.reject(new Error('密码必须包含至少一个数字'))
                        }
                        
                        // 检查特殊字符
                        if (!/[!@#$%^&*(),.?":{}|<>]/.test(value)) {
                          return Promise.reject(new Error('密码必须包含至少一个特殊字符'))
                        }
                        
                        return Promise.resolve()
                      }
                    })
                  ]}
                >
                  <Input.Password 
                    id="modal_password"
                    placeholder="请输入密码"
                    autoComplete="new-password"
                  />
                </Form.Item>
                <Form.Item noStyle shouldUpdate={(prevValues, currentValues) => prevValues.password !== currentValues.password}>
                  {({ getFieldValue }) => (
                    <PasswordStrengthIndicator 
                      password={getFieldValue('password')}
                      onStrengthChange={setPasswordStrength}
                      showSuggestions={true}
                    />
                  )}
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  label="确认密码"
                  name="confirmPassword"
                  dependencies={['password']}
                  rules={[
                    { required: true, message: '请确认密码' },
                    ({ getFieldValue }) => ({
                      validator(_, value) {
                        if (!value || getFieldValue('password') === value) {
                          return Promise.resolve()
                        }
                        return Promise.reject(new Error('两次输入的密码不一致'))
                      }
                    })
                  ]}
                >
                  <Input.Password 
                    id="modal_confirm_password"
                    placeholder="请再次输入密码"
                    autoComplete="new-password"
                  />
                </Form.Item>
              </Col>
            </Row>
          )}

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="所属部门"
                name="dept_id"
              >
                <Select
                  id="modal_dept_id"
                  placeholder="请选择部门"
                  allowClear
                  options={departments.map(dept => ({
                    label: dept.name,
                    value: dept.id
                  }))}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="用户角色"
                name="role_ids"
              >
                <Select
                  id="modal_role_ids"
                  mode="multiple"
                  placeholder="请选择角色"
                  allowClear
                  options={roles.map(role => ({
                    label: role.name,
                    value: role.id
                  }))}
                />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="账户状态"
                name="is_active"
              >
                <Select
                  id="modal_is_active"
                  options={[
                    { label: '正常', value: true },
                    { label: '禁用', value: false }
                  ]}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="超级管理员"
                name="is_superuser"
              >
                <Select
                  id="modal_is_superuser"
                  options={[
                    { label: '否', value: false },
                    { label: '是', value: true }
                  ]}
                />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>
    </div>
  )
}

export default UserManagement 