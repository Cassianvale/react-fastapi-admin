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
  Drawer,
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
  const [permissionDrawerVisible, setPermissionDrawerVisible] = useState(false)
  const [currentRole, setCurrentRole] = useState(null)
  const [menus, setMenus] = useState([])
  const [apis, setApis] = useState([])
  const [selectedMenus, setSelectedMenus] = useState([])
  const [selectedApis, setSelectedApis] = useState([])
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

  // 获取菜单列表
  const fetchMenus = async () => {
    try {
      const response = await api.menus.getList({ page: 1, page_size: 1000 })
      setMenus(response.data || [])
    } catch (error) {
      console.error('获取菜单列表失败:', error)
    }
  }

  // 获取API列表
  const fetchApis = async () => {
    try {
      const response = await api.apis.getList({ page: 1, page_size: 1000 })
      setApis(response.data || [])
    } catch (error) {
      console.error('获取API列表失败:', error)
    }
  }

  // 初始化数据
  useEffect(() => {
    fetchRoles()
    fetchMenus()
    fetchApis()
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
  const handleOpenPermissionDrawer = async (role) => {
    setCurrentRole(role)
    setPermissionDrawerVisible(true)
    setPermissionLoading(true)
    
    try {
      // 获取角色的权限信息
      const response = await api.roles.getAuthorized(role.id)
      const roleData = response.data
      
      // 设置已选择的菜单和API
      setSelectedMenus(roleData.menus?.map(m => m.id.toString()) || [])
      setSelectedApis(roleData.apis?.map(a => ({ id: a.id, path: a.path, method: a.method })) || [])
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
      const apiInfos = selectedApis.map(api => ({
        id: api.id,
        path: api.path,
        method: api.method
      }))
      
      await api.roles.updateAuthorized({
        id: currentRole.id,
        menu_ids: selectedMenus.map(id => parseInt(id)), // 转换回数字
        api_infos: apiInfos
      })
      
      showSuccess('权限配置保存成功')
      setPermissionDrawerVisible(false)
    } catch (error) {
      handleBusinessError(error, '权限配置保存失败')
    } finally {
      setPermissionLoading(false)
    }
  }

  // 构建菜单树
  const buildMenuTree = (menus, parentId = 0) => {
    return menus
      .filter(menu => menu.parent_id === parentId)
      .map(menu => ({
        title: menu.name,
        key: menu.id.toString(), // 确保 key 为字符串
        children: buildMenuTree(menus, menu.id)
      }))
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
              onClick={() => handleOpenPermissionDrawer(record)}
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

      {/* 权限配置抽屉 */}
      <Drawer
        title={
          <div className="flex items-center">
            <SettingOutlined className="mr-2 text-purple-500" />
            权限配置 - {currentRole?.name}
          </div>
        }
        placement="right"
        onClose={() => setPermissionDrawerVisible(false)}
        open={permissionDrawerVisible}
        width={600}
        footer={
          <div className="flex justify-end space-x-2">
            <Button onClick={() => setPermissionDrawerVisible(false)}>
              取消
            </Button>
            <Button
              type="primary"
              loading={permissionLoading}
              onClick={handleSavePermission}
            >
              保存配置
            </Button>
          </div>
        }
      >
        <Tabs 
          defaultActiveKey="menus"
          items={[
            {
              key: 'menus',
              label: (
                <span>
                  <MenuOutlined />
                  菜单权限
                </span>
              ),
              children: (
                <Tree
                  checkable
                  checkedKeys={selectedMenus}
                  onCheck={setSelectedMenus}
                  treeData={buildMenuTree(menus)}
                  height={400}
                />
              )
            },
            {
              key: 'apis',
              label: (
                <span>
                  <ApiOutlined />
                  API权限
                </span>
              ),
              children: (
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {apis.map(api => (
                    <div
                      key={api.id}
                      className={`p-3 border rounded cursor-pointer transition-colors ${
                        selectedApis.find(a => a.id === api.id)
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                      onClick={() => {
                        const isSelected = selectedApis.find(a => a.id === api.id)
                        if (isSelected) {
                          setSelectedApis(selectedApis.filter(a => a.id !== api.id))
                        } else {
                          setSelectedApis([...selectedApis, {
                            id: api.id,
                            path: api.path,
                            method: api.method
                          }])
                        }
                      }}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <span className="font-medium">{api.summary}</span>
                          <div className="text-sm text-gray-500">
                            <Tag color={
                              api.method === 'GET' ? 'green' :
                              api.method === 'POST' ? 'blue' :
                              api.method === 'PUT' ? 'orange' :
                              api.method === 'DELETE' ? 'red' : 'default'
                            }>
                              {api.method}
                            </Tag>
                            {api.path}
                          </div>
                        </div>
                        <div className="text-xs text-gray-400">
                          {api.tags}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )
            }
          ]}
        />
      </Drawer>
    </div>
  )
}

export default RoleManagement 