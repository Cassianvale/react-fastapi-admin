import { request } from '@/utils'

export default {
  // 认证相关
  auth: {
    login: (data) => request.post('/base/access_token', data, { noNeedToken: true }),
    getUserInfo: () => request.get('/base/userinfo'),
    getUserMenu: () => request.get('/base/usermenu'),
    getUserApi: () => request.get('/base/userapi'),
    updatePassword: (data = {}) => request.post('/base/update_password', data),
  },
  
  // 用户管理
  users: {
    getList: (params = {}) => request.get('/user/list', { params }),
    getById: (id) => request.get(`/user/get`, { params: { id } }),
    create: (data = {}) => request.post('/user/create', data),
    update: (data = {}) => request.post('/user/update', data),
    delete: (data) => request.delete(`/user/delete`, { params: data }),
    resetPassword: (data = {}) => request.post(`/user/reset_password`, data),
  },
  
  // 角色管理
  roles: {
    getList: (params = {}) => request.get('/role/list', { params }),
    create: (data = {}) => request.post('/role/create', data),
    update: (data = {}) => request.post('/role/update', data),
    delete: (data) => request.delete('/role/delete', { params: data }),
    updateAuthorized: (data = {}) => request.post('/role/authorized', data),
    getAuthorized: (roleId) => request.get('/role/authorized', { params: { id: roleId } }),
  },
  
  // 菜单管理
  menus: {
    getList: (params = {}) => request.get('/menu/list', { params }),
    create: (data = {}) => request.post('/menu/create', data),
    update: (data = {}) => request.post('/menu/update', data),
    delete: (data) => request.delete('/menu/delete', { params: data }),
  },
  
  // API管理
  apis: {
    getList: (params = {}) => request.get('/api/list', { params }),
    create: (data = {}) => request.post('/api/create', data),
    update: (data = {}) => request.post('/api/update', data),
    delete: (data) => request.delete('/api/delete', { params: data }),
    refresh: () => request.post('/api/refresh'),
  },
  
  // 部门管理
  departments: {
    getList: (params = {}) => request.get('/dept/list', { params }),
    create: (data = {}) => request.post('/dept/create', data),
    update: (data = {}) => request.post('/dept/update', data),
    delete: (data) => request.delete('/dept/delete', { params: data }),
  },
  
  // 审计日志
  auditLogs: {
    getList: (params = {}) => request.get('/auditlog/list', { params }),
  },
  
  // 商品分类
  categories: {
    getList: (params = {}) => request.get('/product/categories', { params }),
    getById: (id) => request.get(`/product/categories/${id}`),
    create: (data = {}) => request.post('/product/categories', data),
    update: (id, data = {}) => request.put(`/product/categories/${id}`, data),
    delete: (id) => request.delete(`/product/categories/${id}`),
  },
  
  // 商品管理
  products: {
    getList: (params = {}) => request.get('/product/products', { params }),
    getById: (id) => request.get(`/product/products/${id}`),
    create: (data = {}) => request.post('/product/products', data),
    update: (id, data = {}) => request.put(`/product/products/${id}`, data),
    delete: (id) => request.delete(`/product/products/${id}`),
    updateStatus: (id, status) => request.put(`/product/products/${id}/status`, { status }),
  },
}
