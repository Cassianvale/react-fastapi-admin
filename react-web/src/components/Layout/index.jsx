import { useState, useEffect } from 'react'
import { Layout, Menu, Avatar, Dropdown, Space, Button, theme, Breadcrumb, Tabs } from 'antd'
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
  CloseOutlined,
} from '@ant-design/icons'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'

const { Header, Sider, Content } = Layout

const AppLayout = () => {
  const [collapsed, setCollapsed] = useState(false)
  const [userInfo, setUserInfo] = useState(null)
  const [tabs, setTabs] = useState([
    {
      key: '/dashboard',
      label: '工作台',
      closable: false,
    }
  ])
  const [activeTab, setActiveTab] = useState('/dashboard')
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
    '/profile': '个人中心',
  }

  // 标签页管理函数
  const addTab = (key, label) => {
    const existingTab = tabs.find(tab => tab.key === key)
    if (!existingTab) {
      setTabs(prev => [...prev, { key, label, closable: true }])
    }
    setActiveTab(key)
    navigate(key)
  }

  const removeTab = (targetKey) => {
    if (targetKey === '/dashboard') return // 工作台不可关闭
    
    const newTabs = tabs.filter(tab => tab.key !== targetKey)
    setTabs(newTabs)
    
    if (activeTab === targetKey) {
      const lastTab = newTabs[newTabs.length - 1]
      setActiveTab(lastTab.key)
      navigate(lastTab.key)
    }
  }

  const handleTabChange = (key) => {
    setActiveTab(key)
    navigate(key)
  }

  // 监听路由变化，同步活跃标签页
  useEffect(() => {
    setActiveTab(location.pathname)
  }, [location.pathname])

  // 获取用户信息
  useEffect(() => {
    const storedUserInfo = localStorage.getItem('userInfo')
    if (storedUserInfo) {
      try {
        setUserInfo(JSON.parse(storedUserInfo))
      } catch (error) {
        console.error('解析用户信息失败:', error)
        localStorage.removeItem('userInfo')
      }
    }
  }, [])

  // 监听用户信息变化
  useEffect(() => {
    const handleStorageChange = () => {
      const storedUserInfo = localStorage.getItem('userInfo')
      if (storedUserInfo) {
        try {
          setUserInfo(JSON.parse(storedUserInfo))
        } catch (error) {
          console.error('解析用户信息失败:', error)
        }
      } else {
        setUserInfo(null)
      }
    }

    window.addEventListener('storage', handleStorageChange)
    return () => window.removeEventListener('storage', handleStorageChange)
  }, [])

  // 手动更新用户信息
  const updateUserInfo = () => {
    const storedUserInfo = localStorage.getItem('userInfo')
    if (storedUserInfo) {
      try {
        setUserInfo(JSON.parse(storedUserInfo))
      } catch (error) {
        console.error('解析用户信息失败:', error)
        setUserInfo(null)
      }
    } else {
      setUserInfo(null)
    }
  }

  // 将更新函数暴露给全局，方便其他组件调用
  useEffect(() => {
    window.updateUserInfo = updateUserInfo
    return () => {
      delete window.updateUserInfo
    }
  }, [updateUserInfo])

  // 登出功能
  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('userInfo')
    setUserInfo(null)
    navigate('/login')
  }

  // 用户菜单
  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined className="text-blue-500" />,
      label: (
        <div className="flex flex-col">
          <span className="font-medium">个人中心</span>
          <span className="text-xs text-gray-500">查看和编辑个人信息</span>
        </div>
      ),
      onClick: () => addTab('/profile', '个人中心'),
    },
    {
      type: 'divider',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined className="text-red-500" />,
      label: (
        <div className="flex flex-col">
          <span className="font-medium text-red-600">退出登录</span>
          <span className="text-xs text-gray-500">安全退出系统</span>
        </div>
      ),
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
    <Layout style={{ minHeight: '100vh' }}>
      {/* 侧边栏 */}
      <Sider 
        trigger={null} 
        collapsible 
        collapsed={collapsed}
        className="shadow-lg"
        theme="light"
        style={{ 
          overflow: 'auto',
          height: '100vh',
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0,
        }}
      >
        {/* Logo区域 */}
        <div className="h-14 flex items-center justify-center border-b border-gray-100 bg-gray-50/50">
          {collapsed ? (
            <div className="w-7 h-7 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center shadow-sm">
              <span className="text-white font-bold text-xs">FA</span>
            </div>
          ) : (
            <div className="flex items-center space-x-2">
              <div className="w-7 h-7 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center shadow-sm">
                <span className="text-white font-bold text-xs">FA</span>
              </div>
              <span className="text-base font-bold text-gray-800">FastAPI Admin</span>
            </div>
          )}
        </div>

        {/* 菜单 */}
        <Menu
          theme="light"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => {
            const menuLabel = breadcrumbNameMap[key] || key
            addTab(key, menuLabel)
          }}
          className="border-r-0"
          style={{ height: 'calc(100% - 56px)', borderRight: 0 }}
        />
      </Sider>

      <Layout style={{ marginLeft: collapsed ? 80 : 200, transition: 'margin-left 0.2s' }}>
        {/* 头部区域 */}
        <div>
          {/* Header */}
          <Header 
            style={{ 
              padding: 10, 
              background: 'transparent',
              height: '56px',
              lineHeight: '56px'
            }}
            className="flex items-center justify-between px-4 "
          >
            <div className="flex items-center">
              <Button
                type="text"
                icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
                onClick={() => setCollapsed(!collapsed)}
                className="text-lg w-15 h-15 flex items-center justify-center"
              />
              
              {/* 面包屑 */}
              <Breadcrumb 
                items={generateBreadcrumbs()}
                className="ml-3"
              />
            </div>

            {/* 用户信息 */}
            <Dropdown
              menu={{ items: userMenuItems }}
              placement="bottomRight"
              arrow
              trigger={['click']}
              onOpenChange={(open) => {
                if (open) {
                  updateUserInfo() // 打开下拉菜单时更新用户信息
                }
              }}
            >
              <div className="cursor-pointer group">
                <Space className="px-3 py-2 rounded-lg transition-all duration-200 hover:bg-gradient-to-r hover:from-blue-50 hover:to-purple-50 hover:shadow-sm group-active:scale-95">
                  <div className="relative">
                    <Avatar 
                      size={32}
                      icon={<UserOutlined />}
                      className="bg-gradient-to-br from-blue-500 to-purple-600 transition-all duration-200 group-hover:shadow-md group-hover:scale-105"
                      style={{
                        border: '2px solid transparent',
                        backgroundClip: 'padding-box'
                      }}
                    />
                    {/* 在线状态指示器 */}
                    <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-green-500 border-2 border-white rounded-full"></div>
                  </div>
                  <div className="flex flex-col items-start">
                    <span className="text-gray-800 font-medium text-sm leading-tight group-hover:text-gray-900 transition-colors">
                      {userInfo?.nickname || userInfo?.username || '用户'}
                    </span>
                    <span className="text-gray-500 text-xs leading-tight">
                      {userInfo?.role || '管理员'}
                    </span>
                  </div>
                  <div className="ml-1 text-gray-400 group-hover:text-gray-600 transition-colors">
                    <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor">
                      <path d="M6 8.5L2.5 5H9.5L6 8.5Z"/>
                    </svg>
                  </div>
                </Space>
              </div>
            </Dropdown>
          </Header>

          {/* 标签页区域 - 无缝连接 */}
          <div className="px-2">
            <Tabs
              type="editable-card"
              activeKey={activeTab}
              onChange={handleTabChange}
              onEdit={(targetKey, action) => {
                if (action === 'remove') {
                  removeTab(targetKey)
                }
              }}
              hideAdd
              size="middle"
              className="!mb-0"
              tabBarStyle={{ 
                marginBottom: 0,
                borderBottom: 'none'
              }}
              items={tabs.map(tab => ({
                key: tab.key,
                label: tab.label,
                closable: tab.closable,
              }))}
            />
          </div>
        </div>

        {/* 内容区域 */}
        <Content className="p-2">
          <div
            style={{
              padding: '16px 16px',
              minHeight: 'calc(100vh - 120px)',
              background: colorBgContainer,
              borderRadius: borderRadiusLG,
            }}
            className="shadow-sm border border-gray-100"
          >
            <Outlet />
          </div>
        </Content>
      </Layout>
    </Layout>
  )
}

export default AppLayout 