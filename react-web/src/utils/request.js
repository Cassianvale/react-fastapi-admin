import axios from 'axios'
import { message } from 'antd'

// 创建axios实例
const request = axios.create({
    baseURL: '/api', // API基础路径
    timeout: 10000,
    headers: {
        'Content-Type': 'application/json',
    },
})

// 请求拦截器
request.interceptors.request.use(
    (config) => {
        // 从localStorage获取token
        const token = localStorage.getItem('token')
        if (token && !config.noNeedToken) {
            config.headers.token = token
        }
        return config
    },
    (error) => {
        return Promise.reject(error)
    }
)

// 响应拦截器
request.interceptors.response.use(
    (response) => {
        const { data } = response

        // 如果是文件下载等特殊响应，直接返回
        if (response.config.responseType === 'blob') {
            return response
        }

        return data
    },
    (error) => {
        const { response } = error

        if (response) {
            const { status, data } = response

            switch (status) {
                case 401:
                    message.error('登录已过期，请重新登录')
                    localStorage.removeItem('token')
                    localStorage.removeItem('userInfo')
                    window.location.href = '/login'
                    break
                case 403:
                    message.error('没有权限访问')
                    break
                case 404:
                    message.error('请求的资源不存在')
                    break
                case 500:
                    message.error('服务器内部错误')
                    break
                default:
                    message.error(data?.message || '请求失败')
            }
        } else {
            message.error('网络连接失败')
        }

        return Promise.reject(error)
    }
)

export default request 