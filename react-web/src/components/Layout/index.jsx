import { useState, useEffect } from 'react'
import { Layout, Menu, Avatar, Dropdown, Space, Button, theme, Breadcrumb } from 'antd'
import {
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  DashboardOutlined,
  UserOutlined,
  TeamOutlined,
  SettingOutlined,
  LogoutOutlined,
  ApartmentOutlined,
  ApiOutlined,
  FileTextOutlined,
  CloudUploadOutlined,
} from '@ant-design/icons'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'

const { Header, Sider, Content } = Layout

const AppLayout = () => {
  const [collapsed, setCollapsed] = useState(false)
  const [userInfo, setUserInfo] = useState(null)
  const navigate = useNavigate()
  const location = useLocation()
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken()

  // 菜单项配置
  const menuItems = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: '工作台',
    },
    {
      key: '/system',
      icon: <SettingOutlined />,
      label: '系统管理',
      children: [
        {
          key: '/system/users',
          icon: <UserOutlined />,
          label: '用户管理',
        },
        {
          key: '/system/roles',
          icon: <TeamOutlined />,
          label: '角色管理',
        },
        {
          key: '/system/menus',
          icon: <ApartmentOutlined />,
          label: '菜单管理',
        },
        {
          key: '/system/apis',
          icon: <ApiOutlined />,
          label: 'API管理',
        },
        {
          key: '/system/departments',
          icon: <ApartmentOutlined />,
          label: '部门管理',
        },
      ],
    },
    {
      key: '/audit',
      icon: <FileTextOutlined />,
      label: '审计日志',
    },
    {
      key: '/upload',
      icon: <CloudUploadOutlined />,
      label: '文件管理',
    },
  ]

  // 面包屑映射
  const breadcrumbNameMap = {
    '/dashboard': '工作台',
    '/system': '系统管理',
    '/system/users': '用户管理',
    '/system/roles': '角色管理',
    '/system/menus': '菜单管理',
    '/system/apis': 'API管理',
    '/system/departments': '部门管理',
    '/audit': '审计日志',
    '/upload': '文件管理',
  }

  // 获取用户信息
  useEffect(() => {
    const storedUserInfo = localStorage.getItem('userInfo')
    if (storedUserInfo) {
      setUserInfo(JSON.parse(storedUserInfo))
    }
  }, [])

  // 登出功能
  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('userInfo')
    navigate('/login')
  }

  // 用户菜单
  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人中心',
      onClick: () => navigate('/profile'),
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: handleLogout,
    },
  ]

  // 生成面包屑
  const generateBreadcrumbs = () => {
    const pathSnippets = location.pathname.split('/').filter(i => i)
    const breadcrumbItems = pathSnippets.map((_, index) => {
      const url = `/${pathSnippets.slice(0, index + 1).join('/')}`
      return {
        title: breadcrumbNameMap[url],
      }
    })
    return breadcrumbItems
  }

  return (
    <Layout className="min-h-screen">
      {/* 侧边栏 */}
      <Sider 
        trigger={null} 
        collapsible 
        collapsed={collapsed}
        className="shadow-lg"
        theme="light"
      >
        {/* Logo区域 */}
        <div className="h-16 flex items-center justify-center border-b border-gray-200">
          {collapsed ? (
            <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">FA</span>
            </div>
          ) : (
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">FA</span>
              </div>
              <span className="text-lg font-bold text-gray-800">FastAPI Admin</span>
            </div>
          )}
        </div>

        {/* 菜单 */}
        <Menu
          theme="light"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
          className="border-r-0"
        />
      </Sider>

      <Layout>
        {/* 头部 */}
        <Header 
          style={{ padding: 0, background: colorBgContainer }}
          className="shadow-sm border-b border-gray-200 flex items-center justify-between px-4"
        >
          <div className="flex items-center">
            <Button
              type="text"
              icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={() => setCollapsed(!collapsed)}
              className="text-lg w-16 h-16"
            />
            
            {/* 面包屑 */}
            <Breadcrumb 
              items={generateBreadcrumbs()}
              className="ml-4"
            />
          </div>

          {/* 用户信息 */}
          <Dropdown
            menu={{ items: userMenuItems }}
            placement="bottomRight"
            arrow
          >
            <Space className="cursor-pointer hover:bg-gray-50 px-3 py-2 rounded-lg transition-colors">
              <Avatar 
                size="small" 
                icon={<UserOutlined />}
                className="bg-gradient-to-br from-blue-500 to-purple-600"
              />
              <span className="text-gray-700 font-medium">
                {userInfo?.nickname || userInfo?.username || '用户'}
              </span>
            </Space>
          </Dropdown>
        </Header>

        {/* 内容区域 */}
        <Content className="m-4">
          <div
            style={{
              padding: 24,
              minHeight: 280,
              background: colorBgContainer,
              borderRadius: borderRadiusLG,
            }}
            className="shadow-sm"
          >
            <Outlet />
          </div>
        </Content>
      </Layout>
    </Layout>
  )
}

export default AppLayout 