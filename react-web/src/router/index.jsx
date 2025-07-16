import { createBrowserRouter, Navigate } from 'react-router-dom'
import Dashboard from '@/pages/Dashboard'
import AppLayout from '@/components/Layout'
import ProtectedRoute from '@/components/ProtectedRoute'
import LoginRedirect from '@/components/LoginRedirect'

const router = createBrowserRouter([
  {
    path: '/login',
    element: <LoginRedirect />,
  },
  {
    path: '/',
    element: (
      <ProtectedRoute>
        <AppLayout />
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
      // 系统管理路由
      {
        path: 'system',
        children: [
          {
            path: 'users',
            element: <div>用户管理页面</div>,
          },
          {
            path: 'roles',
            element: <div>角色管理页面</div>,
          },
          {
            path: 'menus',
            element: <div>菜单管理页面</div>,
          },
          {
            path: 'apis',
            element: <div>API管理页面</div>,
          },
          {
            path: 'departments',
            element: <div>部门管理页面</div>,
          },
        ],
      },
      // 其他路由
      {
        path: 'audit',
        element: <div>审计日志页面</div>,
      },
      {
        path: 'upload',
        element: <div>文件管理页面</div>,
      },
      {
        path: 'profile',
        element: <div>个人中心页面</div>,
      },
    ],
  },
  // 404页面
  {
    path: '*',
    element: <div className="flex items-center justify-center h-screen">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-800 mb-4">404</h1>
        <p className="text-gray-600">页面不存在</p>
      </div>
    </div>,
  },
])

export default router 