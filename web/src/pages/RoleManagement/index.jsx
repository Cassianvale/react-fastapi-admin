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
  Divider,
  Tooltip,
  Tree,
  Tabs
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  SearchOutlined,
  ReloadOutlined,
  ClearOutlined,
  SettingOutlined,
  UserOutlined,
  ApiOutlined,
  MenuOutlined
} from '@ant-design/icons'
import api from '@/api'
import { useErrorHandler } from '@/hooks/useErrorHandler'

const { TextArea } = Input

const RoleManagement = () => {
  // 基础状态
  const [loading, setLoading] = useState(false)
  const [roles, setRoles] = useState([])
  const [total, setTotal] = useState(0)
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  
  // 搜索状态
  const [searchForm] = Form.useForm()
  const [searchParams, setSearchParams] = useState({})
  
  // 模态框状态
  const [modalVisible, setModalVisible] = useState(false)
  const [modalForm] = Form.useForm()
  const [editingRole, setEditingRole] = useState(null)
  const [modalLoading, setModalLoading] = useState(false)
  
  // 权限配置状态
  const [permissionModalVisible, setPermissionModalVisible] = useState(false)
  const [currentRole, setCurrentRole] = useState(null)
  const [permissions, setPermissions] = useState([])
  const [selectedPermissions, setSelectedPermissions] = useState([])
  const [permissionLoading, setPermissionLoading] = useState(false)
  
  const { handleError, handleBusinessError, showSuccess } = useErrorHandler()

  // 获取角色列表
  const fetchRoles = async (page = currentPage, size = pageSize, search = searchParams) => {
    setLoading(true)
    try {
      const params = {
        page,
        page_size: size,
        ...search
      }
      const response = await api.roles.getList(params)
      setRoles(response.data || [])
      setTotal(response.total || 0)
      setCurrentPage(response.page || page)
      setPageSize(response.page_size || size)
    } catch (error) {
      handleError(error, '获取角色列表失败')
    } finally {
      setLoading(false)
    }
  }

  // 获取权限数据 - 从现有权限中构建树结构
  const fetchPermissions = async () => {
    try {
      // 从角色权限中获取所有权限或者直接使用静态的权限树结构
      setPermissions([]) // 暂时设为空，权限树将在角色权限分配时动态获取
    } catch (error) {
      handleError(error, '获取权限数据失败')
    }
  }

  // 初始化数据
  useEffect(() => {
    fetchRoles()
    fetchPermissions()
  }, [])

  // 处理模态框表单数据设置
  useEffect(() => {
    if (modalVisible) {
      if (editingRole) {
        // 编辑模式
        modalForm.setFieldsValue({
          id: editingRole.id,
          name: editingRole.name || '',
          desc: editingRole.desc || ''
        })
      } else {
        // 添加模式
        modalForm.resetFields()
      }
    }
  }, [modalVisible, editingRole, modalForm])

  // 搜索处理
  const handleSearch = async (values) => {
    const params = {}
    if (values.role_name) params.role_name = values.role_name
    
    setSearchParams(params)
    setCurrentPage(1)
    await fetchRoles(1, pageSize, params)
  }

  // 清空搜索
  const handleClearSearch = async () => {
    searchForm.resetFields()
    setSearchParams({})
    setCurrentPage(1)
    await fetchRoles(1, pageSize, {})
  }

  // 分页处理
  const handlePageChange = async (page, size) => {
    setCurrentPage(page)
    setPageSize(size)
    await fetchRoles(page, size, searchParams)
  }

  // 打开添加/编辑模态框
  const handleOpenModal = (role = null) => {
    setEditingRole(role)
    setModalVisible(true)
  }

  // 关闭模态框
  const handleCloseModal = () => {
    setModalVisible(false)
    setEditingRole(null)
    modalForm.resetFields()
  }

  // 保存角色
  const handleSaveRole = async (values) => {
    setModalLoading(true)
    try {
      if (editingRole) {
        // 更新角色
        await api.roles.update({ ...values, id: editingRole.id })
        showSuccess('角色更新成功')
      } else {
        // 创建角色
        await api.roles.create(values)
        showSuccess('角色创建成功')
      }
      handleCloseModal()
      await fetchRoles()
    } catch (error) {
      handleBusinessError(error, editingRole ? '角色更新失败' : '角色创建失败')
    } finally {
      setModalLoading(false)
    }
  }

  // 删除角色
  const handleDeleteRole = async (roleId) => {
    try {
      await api.roles.delete({ role_id: roleId })
      showSuccess('角色删除成功')
      await fetchRoles()
    } catch (error) {
      handleBusinessError(error, '角色删除失败')
    }
  }

  // 打开权限配置
  const handleOpenPermissionModal = async (role) => {
    setCurrentRole(role)
    setPermissionModalVisible(true)
    setPermissionLoading(true)

    try {
      // 获取角色的权限信息（树形结构）
      const response = await api.roles.getPermissions(role.id)
      const rolePermissionsTree = response.data || []

      // 从树形结构中提取所有权限ID
      const extractPermissionIds = (tree) => {
        let ids = []
        tree.forEach(item => {
          ids.push(item.id)
          if (item.children && item.children.length > 0) {
            ids = ids.concat(extractPermissionIds(item.children))
          }
        })
        return ids
      }

      const permissionIds = extractPermissionIds(rolePermissionsTree)
      setSelectedPermissions(permissionIds)

      // 同时设置权限树数据供显示使用
      setPermissions(rolePermissionsTree)
    } catch (error) {
      handleError(error, '获取角色权限失败')
    } finally {
      setPermissionLoading(false)
    }
  }

  // 保存权限配置
  const handleSavePermission = async () => {
    setPermissionLoading(true)
    try {
      await api.roles.updatePermissions({
        id: currentRole.id,
        permission_ids: selectedPermissions
      })

      showSuccess('权限配置保存成功')
      setPermissionModalVisible(false)
    } catch (error) {
      handleBusinessError(error, '权限配置保存失败')
    } finally {
      setPermissionLoading(false)
    }
  }



  // 表格列定义
  const columns = [
    {
      title: '角色名称',
      dataIndex: 'name',
      key: 'name',
      width: 150,
      render: (text) => (
        <div className="flex items-center">
          <UserOutlined className="mr-2 text-blue-500" />
          <span className="font-medium">{text || '-'}</span>
        </div>
      )
    },
    {
      title: '角色描述',
      dataIndex: 'desc',
      key: 'desc',
      width: 300,
      render: (text) => text || '-'
    },
    {
      title: '用户数量',
      key: 'user_count',
      width: 100,
      render: (_, record) => (
        <Tag color="blue">
          {record.users?.length || 0} 人
        </Tag>
      )
    },
    {
      title: '权限数量',
      key: 'permission_count',
      width: 150,
      render: (_, record) => (
        <div className="flex gap-2">
          <Tag color="green">
            <MenuOutlined className="mr-1" />
            {record.menus?.length || 0} 菜单
          </Tag>
          <Tag color="orange">
            <ApiOutlined className="mr-1" />
            {record.apis?.length || 0} API
          </Tag>
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
          <Tooltip title="权限配置">
            <Button
              size="small"
              icon={<SettingOutlined />}
              className="text-purple-500 border-purple-500 hover:bg-purple-50"
              onClick={() => handleOpenPermissionModal(record)}
            />
          </Tooltip>
          <Tooltip title="删除">
            <Popconfirm
              title="确认删除角色？"
              description="删除后无法恢复，请谨慎操作"
              onConfirm={() => handleDeleteRole(record.id)}
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
          <h1 className="text-2xl font-bold text-gray-800">角色管理</h1>
          <p className="text-gray-500 mt-1">管理系统角色权限，分配菜单和API访问权限</p>
        </div>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => handleOpenModal()}
          className="bg-gradient-to-r from-blue-500 to-blue-600"
        >
          新增角色
        </Button>
      </div>

      {/* 角色管理主卡片 */}
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
            <Form.Item name="role_name" className="mb-2">
              <Input
                id="search_role_name"
                placeholder="角色名称"
                prefix={<UserOutlined />}
                allowClear
                style={{ width: 200 }}
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
                  onClick={() => fetchRoles()}
                  loading={loading}
                >
                  刷新
                </Button>
              </Space>
            </Form.Item>
          </Form>
        </div>

        {/* 角色列表 */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center">
              <UserOutlined className="mr-2 text-blue-500" />
              <span className="font-medium text-gray-700">角色列表</span>
            </div>
            <div className="text-sm text-gray-500">
              共 {total} 条记录
            </div>
          </div>
          
          <Table
            columns={columns}
            dataSource={roles}
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

      {/* 添加/编辑角色模态框 */}
      <Modal
        title={
          <div className="flex items-center">
            <UserOutlined className="mr-2 text-blue-500" />
            {editingRole ? '编辑角色' : '新增角色'}
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
            {editingRole ? '更新' : '创建'}
          </Button>
        ]}
        width={600}
        destroyOnHidden
      >
        <Form
          form={modalForm}
          layout="vertical"
          onFinish={handleSaveRole}
          className="mt-4"
        >
            <Form.Item
              label="角色名称"
              name="name"
              rules={[
                { required: true, message: '请输入角色名称' },
                { min: 2, max: 20, message: '角色名称长度为2-20个字符' }
              ]}
            >
                             <Input 
                 id="modal_role_name"
                 placeholder="请输入角色名称"
                 autoComplete="off"
               />
            </Form.Item>
            
            <Form.Item
              label="角色描述"
              name="desc"
              rules={[
                { max: 500, message: '角色描述不能超过500个字符' }
              ]}
            >
               <TextArea 
                 id="modal_role_desc"
                 placeholder="请输入角色描述"
                 rows={3}
                 showCount
                 maxLength={500}
                 autoComplete="off"
               />
            </Form.Item>
        </Form>
      </Modal>

      {/* 权限配置模态框 */}
      <Modal
        title={
          <div className="flex items-center">
            <SettingOutlined className="mr-2 text-purple-500" />
            权限配置 - {currentRole?.name}
          </div>
        }
        open={permissionModalVisible}
        onCancel={() => setPermissionModalVisible(false)}
        width={800}
        footer={[
          <Button key="cancel" onClick={() => setPermissionModalVisible(false)}>
            取消
          </Button>,
          <Button
            key="submit"
            type="primary"
            loading={permissionLoading}
            onClick={handleSavePermission}
          >
            保存配置
          </Button>
        ]}
        destroyOnHidden
      >
        <div className="space-y-4">
          <div className="text-sm text-gray-600 mb-4">
            为角色 <strong>{currentRole?.name}</strong> 分配权限。权限采用层次化结构，选择父权限会自动包含子权限。
          </div>

          <Tree
            checkable
            checkedKeys={selectedPermissions}
            onCheck={(checkedKeys) => {
              setSelectedPermissions(Array.isArray(checkedKeys) ? checkedKeys : checkedKeys.checked)
            }}
            treeData={buildPermissionTree(permissions)}
            height={400}
            showIcon
            defaultExpandAll
          />
        </div>
      </Modal>
    </div>
  )
}

// 辅助函数：构建权限树
const buildPermissionTree = (permissions) => {
  if (!permissions || !Array.isArray(permissions)) {
    return []
  }

  const buildTree = (items) => {
    return items.map(item => ({
      title: (
        <div className="flex items-center space-x-2">
          <span className={`inline-block w-2 h-2 rounded-full ${
            item.permission_type === 'module' ? 'bg-blue-500' :
            item.permission_type === 'feature' ? 'bg-green-500' :
            'bg-orange-500'
          }`} />
          <span className="font-medium">{item.name}</span>
          {item.api_path && (
            <span className="text-xs text-blue-400 bg-blue-50 px-2 py-1 rounded">
              {item.api_method} {item.api_path}
            </span>
          )}
          {item.menu_path && (
            <span className="text-xs text-green-400 bg-green-50 px-2 py-1 rounded">
              菜单: {item.menu_path}
            </span>
          )}
        </div>
      ),
      key: item.id,
      children: item.children && item.children.length > 0 ? buildTree(item.children) : undefined
    }))
  }

  return buildTree(permissions)
}

export default RoleManagement