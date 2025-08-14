import { createBrowserRouter, Navigate } from 'react-router-dom'
import Layout from '@/components/Layout'
import ProtectedRoute from '@/components/ProtectedRoute'
import LoginRedirect from '@/components/LoginRedirect'

// 页面组件
import Login from '@/pages/Login'
import Dashboard from '@/pages/Dashboard'
import Profile from '@/pages/Profile'
import UserManagement from '@/pages/UserManagement'
import RoleManagement from '@/pages/RoleManagement'
import ApiManagement from '@/pages/ApiManagement'
import { NotFoundPage } from '@/pages/ErrorPages'

const router = createBrowserRouter([
  {
    path: '/login',
    element: <Login />,
  },
  {
    path: '/',
    element: (
      <ProtectedRoute>
        <Layout />
      </ProtectedRoute>
    ),
    children: [
      {
        index: true,
        element: <Navigate to="/dashboard" replace />,
      },
      {
        path: 'dashboard',
        element: <Dashboard />,
      },
      {
        path: 'profile',
        element: <Profile />,
      },
      // 系统管理路由
      {
        path: 'system',
        children: [
          {
            path: 'users',
            element: <UserManagement />,
          },
          {
            path: 'roles',
            element: <RoleManagement />,
          },
          {
            path: 'apis',
            element: <ApiManagement />,
          },
          {
            path: 'departments',
            element: <div>部门管理页面</div>,
          },
          {
            path: 'audit',
            element: <div>审计日志页面</div>,
          },
          {
            path: 'upload',
            element: <div>文件管理页面</div>,
          },
        ],
      },
      // 404页面 - 在Layout内容区域显示
      {
        path: '*',
        element: <NotFoundPage />,
      },
    ],
  },
  // 登录重定向处理
  {
    path: '/auth/callback',
    element: <LoginRedirect />,
  },
])

export default router 