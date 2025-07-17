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
  Tooltip,
  Switch,
  InputNumber,
  Divider
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  SearchOutlined,
  ReloadOutlined,
  ClearOutlined,
  MenuOutlined,
  FolderOutlined,
  AppstoreOutlined,
  NodeIndexOutlined,
  QuestionCircleOutlined
} from '@ant-design/icons'
import { Icon } from '@iconify/react'
import api from '@/api'
import { useErrorHandler } from '@/hooks/useErrorHandler'
import IconSelector from '@/components/IconSelector'

const MenuManagement = () => {
  // 基础状态
  const [loading, setLoading] = useState(false)
  const [menus, setMenus] = useState([])
  const [expandedRowKeys, setExpandedRowKeys] = useState([])
  
  // 搜索状态
  const [searchForm] = Form.useForm()
  const [filteredMenus, setFilteredMenus] = useState([])
  
  // 模态框状态
  const [modalVisible, setModalVisible] = useState(false)
  const [modalForm] = Form.useForm()
  const [editingMenu, setEditingMenu] = useState(null)
  const [modalLoading, setModalLoading] = useState(false)
  const [parentMenuId, setParentMenuId] = useState(null) // 用于添加子菜单
  
  const { handleError, handleBusinessError, showSuccess } = useErrorHandler()

  // 菜单类型选项
  const menuTypeOptions = [
    { label: '目录', value: 'catalog' },
    { label: '菜单', value: 'menu' },
    { label: '按钮', value: 'button' }
  ]

  // 获取菜单列表
  const fetchMenus = async () => {
    setLoading(true)
    try {
      const response = await api.menus.getList()
      const menuData = response.data || []
      setMenus(menuData)
      setFilteredMenus(menuData) // 初始化过滤数据
      
      // 默认展开所有顶级菜单
      const topLevelKeys = menuData
        .filter(menu => menu.parent_id === 0)
        .map(menu => menu.id)
      setExpandedRowKeys(topLevelKeys)
    } catch (error) {
      handleError(error, '获取菜单列表失败')
    } finally {
      setLoading(false)
    }
  }

  // 初始化数据
  useEffect(() => {
    fetchMenus()
  }, [])

  // 将后端树形数据转换为前端需要的格式
  const convertToTreeData = (treeData) => {
    // 后端已经返回了树形结构，但需要清理空的children字段
    const cleanTreeData = (nodes) => {
      return nodes.map(node => {
        const cleanedNode = { ...node }
        
        // 如果children存在但为空数组，则删除children字段
        if (cleanedNode.children && Array.isArray(cleanedNode.children)) {
          if (cleanedNode.children.length > 0) {
            // 递归清理子节点
            cleanedNode.children = cleanTreeData(cleanedNode.children)
          } else {
            // 删除空的children字段
            delete cleanedNode.children
          }
        }
        
        return cleanedNode
      })
    }
    
    return cleanTreeData(treeData || [])
  }

  // 将树形数据扁平化
  const flattenTreeData = (treeData, result = []) => {
    treeData.forEach(item => {
      result.push(item)
      if (item.children && item.children.length > 0) {
        flattenTreeData(item.children, result)
      }
    })
    return result
  }

  // 在树形结构中搜索并保持树形结构
  const searchInTree = (treeData, searchValues) => {
    const filterNode = (node) => {
      let nodeMatches = true
      
      if (searchValues.name) {
        nodeMatches = nodeMatches && node.name.toLowerCase().includes(searchValues.name.toLowerCase())
      }
      
      if (searchValues.menu_type) {
        nodeMatches = nodeMatches && node.menu_type === searchValues.menu_type
      }

      // 递归检查子节点
      let filteredChildren = []
      if (node.children && node.children.length > 0) {
        filteredChildren = node.children.map(child => filterNode(child)).filter(child => child !== null)
      }

      // 如果当前节点匹配，或者有匹配的子节点，则包含此节点
      if (nodeMatches || filteredChildren.length > 0) {
        return {
          ...node,
          children: filteredChildren
        }
      }

      return null
    }

    return treeData.map(node => filterNode(node)).filter(node => node !== null)
  }

  // 处理模态框表单数据设置
  useEffect(() => {
    if (modalVisible) {
      if (editingMenu) {
        // 编辑模式
        modalForm.setFieldsValue({
          id: editingMenu.id,
          name: editingMenu.name || '',
          path: editingMenu.path || '',
          icon: editingMenu.icon || '',
          menu_type: editingMenu.menu_type || 'catalog',
          order: editingMenu.order || 1,
          parent_id: editingMenu.parent_id || 0,
          is_hidden: editingMenu.is_hidden ?? false,
          component: editingMenu.component || '',
          keepalive: editingMenu.keepalive ?? true,
          redirect: editingMenu.redirect || ''
        })
      } else {
        // 添加模式
        modalForm.resetFields()
        modalForm.setFieldsValue({
          menu_type: 'catalog',
          order: 1,
          parent_id: parentMenuId || 0,
          is_hidden: false,
          component: 'Layout',
          keepalive: true,
          redirect: ''
        })
      }
    }
  }, [modalVisible, editingMenu, parentMenuId, modalForm])

  // 搜索处理
  const handleSearch = (values) => {
    if (!values.name && !values.menu_type) {
      // 如果没有搜索条件，显示所有菜单
      setFilteredMenus(menus)
      return
    }

    // 在树形结构中搜索
    const filtered = searchInTree(menus, values)
    setFilteredMenus(filtered)
  }

  // 清空搜索
  const handleClearSearch = () => {
    searchForm.resetFields()
    setFilteredMenus(menus)
  }

  // 打开添加/编辑模态框
  const handleOpenModal = (menu = null, parentId = null) => {
    setEditingMenu(menu)
    setParentMenuId(parentId)
    setModalVisible(true)
  }

  // 关闭模态框
  const handleCloseModal = () => {
    setModalVisible(false)
    setEditingMenu(null)
    setParentMenuId(null)
    modalForm.resetFields()
  }

  // 保存菜单
  const handleSaveMenu = async (values) => {
    setModalLoading(true)
    try {
      // 处理空字符串
      const processedValues = {
        ...values,
        icon: values.icon?.trim() || null,
        redirect: values.redirect?.trim() || null,
        component: values.component?.trim() || 'Layout'
      }
      
      if (editingMenu) {
        // 更新菜单
        await api.menus.update(processedValues)
        showSuccess('菜单更新成功')
      } else {
        // 创建菜单
        await api.menus.create(processedValues)
        showSuccess('菜单创建成功')
      }
      handleCloseModal()
      await fetchMenus()
      
      // 刷新左侧导航栏菜单
      if (window.refreshUserMenu) {
        window.refreshUserMenu()
      }
    } catch (error) {
      handleBusinessError(error, editingMenu ? '菜单更新失败' : '菜单创建失败')
    } finally {
      setModalLoading(false)
    }
  }

  // 删除菜单
  const handleDeleteMenu = async (menuId) => {
    try {
      await api.menus.delete({ id: menuId })
      showSuccess('菜单删除成功')
      await fetchMenus()
      
      // 刷新左侧导航栏菜单
      if (window.refreshUserMenu) {
        window.refreshUserMenu()
      }
    } catch (error) {
      handleBusinessError(error, '菜单删除失败')
    }
  }

  // 获取菜单类型图标
  const getMenuTypeIcon = (type) => {
    switch (type) {
      case 'catalog':
        return <FolderOutlined className="text-orange-500" />
      case 'menu':
        return <MenuOutlined className="text-blue-500" />
      case 'button':
        return <AppstoreOutlined className="text-green-500" />
      default:
        return <MenuOutlined className="text-gray-500" />
    }
  }

  // 获取菜单类型标签颜色
  const getMenuTypeColor = (type) => {
    switch (type) {
      case 'catalog':
        return 'orange'
      case 'menu':
        return 'blue'
      case 'button':
        return 'green'
      default:
        return 'default'
    }
  }

  // 表格列定义
  const columns = [
    {
      title: '菜单名称',
      dataIndex: 'name',
      key: 'name',
      width: 200,
      render: (text, record) => (
        <div className="flex items-center space-x-2">
          {record.icon ? (
            <Icon icon={record.icon} width="16" height="16" className="text-gray-600" />
          ) : (
            getMenuTypeIcon(record.menu_type)
          )}
          <span className="font-medium">{text || '-'}</span>
        </div>
      )
    },
    {
      title: '类型',
      dataIndex: 'menu_type',
      key: 'menu_type',
      width: 100,
      render: (type) => (
        <Tag color={getMenuTypeColor(type)}>
          {menuTypeOptions.find(opt => opt.value === type)?.label || type}
        </Tag>
      )
    },
    {
      title: '路径',
      dataIndex: 'path',
      key: 'path',
      width: 200,
      render: (text) => (
        <code className="bg-gray-100 px-2 py-1 rounded text-sm">
          {text || '-'}
        </code>
      )
    },
    {
      title: '组件',
      dataIndex: 'component',
      key: 'component',
      width: 150,
      render: (text) => (
        <span className="text-sm text-gray-600">
          {text || '-'}
        </span>
      )
    },
    {
      title: '排序',
      dataIndex: 'order',
      key: 'order',
      width: 80,
      render: (value, record) => {
        // 根据菜单层级和类型设置不同颜色
        const getOrderTagColor = () => {
          if (record.parent_id === 0) {
            // 顶级菜单
            switch (record.menu_type) {
              case 'catalog':
                return 'volcano' // 橙红色 - 顶级目录
              case 'menu':
                return 'purple' // 紫色 - 顶级菜单
              default:
                return 'magenta' // 洋红色 - 其他顶级
            }
          } else {
            // 子菜单
            switch (record.menu_type) {
              case 'catalog':
                return 'orange' // 橙色 - 子目录
              case 'menu':
                return 'blue' // 蓝色 - 子菜单
              case 'button':
                return 'cyan' // 青色 - 按钮
              default:
                return 'geekblue' // 极客蓝 - 其他子级
            }
          }
        }
        
        return (
          <Tag color={getOrderTagColor()}>
            {value}
          </Tag>
        )
      }
    },
    {
      title: '状态',
      key: 'status',
      width: 150,
      render: (_, record) => (
        <div className="flex flex-col gap-1">
          <Tag color={record.is_hidden ? 'red' : 'green'}>
            {record.is_hidden ? '隐藏' : '显示'}
          </Tag>
          {record.keepalive && (
            <Tag color="blue">缓存</Tag>
          )}
        </div>
      )
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="添加子菜单">
            <Button
              type="dashed"
              size="small"
              icon={<NodeIndexOutlined />}
              onClick={() => handleOpenModal(null, record.id)}
              className="text-green-500 border-green-500 hover:bg-green-50"
            />
          </Tooltip>
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
              title="确认删除菜单？"
              description="删除后无法恢复，子菜单也会被删除"
              onConfirm={() => handleDeleteMenu(record.id)}
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
          <h1 className="text-2xl font-bold text-gray-800">菜单管理</h1>
          <p className="text-gray-500 mt-1">管理系统菜单结构、权限控制和导航层级</p>
        </div>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => handleOpenModal()}
          className="bg-gradient-to-r from-blue-500 to-blue-600"
        >
          新增菜单
        </Button>
      </div>

      {/* 菜单管理主卡片 */}
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
            <Form.Item name="name" className="mb-2">
              <Input
                placeholder="菜单名称"
                prefix={<MenuOutlined />}
                allowClear
                style={{ width: 160 }}
              />
            </Form.Item>
            <Form.Item name="menu_type" className="mb-2">
              <Select
                placeholder="选择类型"
                allowClear
                style={{ width: 120 }}
                options={menuTypeOptions}
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
                  onClick={fetchMenus}
                  loading={loading}
                >
                  刷新
                </Button>
              </Space>
            </Form.Item>
          </Form>
        </div>

        {/* 菜单树形表格 */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center">
              <MenuOutlined className="mr-2 text-blue-500" />
              <span className="font-medium text-gray-700">菜单树形结构</span>
            </div>
            <div className="text-sm text-gray-500">
              共 {flattenTreeData(filteredMenus).length} 个菜单项
            </div>
          </div>
          
          <Table
            columns={columns}
            dataSource={convertToTreeData(filteredMenus)}
            rowKey="id"
            loading={loading}
            pagination={false}
            scroll={{ x: 1000 }}
            size="middle"
            expandable={{
              expandedRowKeys,
              onExpandedRowsChange: setExpandedRowKeys,
              indentSize: 20
            }}
          />
        </div>
      </Card>

      {/* 添加/编辑菜单模态框 */}
      <Modal
        title={
          <div className="flex items-center">
            <MenuOutlined className="mr-2 text-blue-500" />
            {editingMenu ? '编辑菜单' : parentMenuId ? '新增子菜单' : '新增菜单'}
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
            {editingMenu ? '更新' : '创建'}
          </Button>
        ]}
        width={700}
        destroyOnHidden
      >
        <Form
          form={modalForm}
          layout="vertical"
          onFinish={handleSaveMenu}
          className="mt-4"
        >
          {editingMenu && (
            <Form.Item name="id" hidden>
              <Input />
            </Form.Item>
          )}

          <Form.Item name="parent_id" hidden>
            <InputNumber />
          </Form.Item>
          
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="菜单名称"
                name="name"
                rules={[
                  { required: true, message: '请输入菜单名称' },
                  { max: 50, message: '菜单名称不能超过50个字符' }
                ]}
              >
                <Input placeholder="请输入菜单名称" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="菜单类型"
                name="menu_type"
                rules={[{ required: true, message: '请选择菜单类型' }]}
              >
                <Select options={menuTypeOptions} />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="菜单路径"
                name="path"
                rules={[
                  { required: true, message: '请输入菜单路径' },
                  { max: 200, message: '路径不能超过200个字符' }
                ]}
              >
                <Input placeholder="如：/system/user" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="菜单图标"
                name="icon"
              >
                <IconSelector placeholder="选择菜单图标" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="排序号"
                name="order"
                rules={[{ required: true, message: '请输入排序号' }]}
              >
                <InputNumber 
                  min={1} 
                  max={999} 
                  placeholder="排序号" 
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="组件路径"
                name="component"
                rules={[{ required: true, message: '请输入组件路径' }]}
              >
                <Input placeholder="如：Layout 或 /system/user" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={24}>
              <Form.Item
                label="重定向路径"
                name="redirect"
              >
                <Input placeholder="重定向路径（可选）" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={24}>
              <div className="flex space-x-10">
                <div className="flex items-center space-x-3">
                  <Form.Item
                    name="is_hidden"
                    valuePropName="checked"
                    style={{ margin: 0, marginRight: 10 }}
                  >
                    <Switch size="middle" />
                  </Form.Item>
                  <span className="text-gray-700">隐藏菜单</span>
                </div>
                <div className="flex items-center space-x-3">
                  <Form.Item
                    name="keepalive"
                    valuePropName="checked"
                    style={{ margin: 0, marginRight: 10 }}
                  >
                    <Switch size="middle" />
                  </Form.Item>
                  <span className="text-gray-700">页面缓存</span>
                  <Tooltip
                    title={
                      <div className="text-sm max-w-sm">
                        <div className="font-bold mb-2">页面缓存说明：</div>
                        <div>• 启用：离开页面后再次访问时保留之前的状态（搜索条件、分页位置等）</div>
                        <div>• 禁用：每次访问都重新加载页面，获取最新数据</div>
                        <div>• 建议：数据管理页面启用，实时数据页面禁用</div>
                      </div>
                    }
                    placement="right"
                  >
                    <QuestionCircleOutlined className="ml-2 text-gray-400 hover:text-blue-500 cursor-help text-base" />
                  </Tooltip>
                </div>
              </div>
            </Col>
          </Row>

          {parentMenuId && (
            <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded">
              <div className="flex items-center text-blue-700">
                <NodeIndexOutlined className="mr-2" />
                <span className="font-medium">
                  将作为子菜单添加到父菜单下
                </span>
              </div>
            </div>
          )}
        </Form>
      </Modal>
    </div>
  )
}

export default MenuManagement 