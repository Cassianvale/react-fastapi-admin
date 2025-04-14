import { getToken } from '@/utils'
import { resolveResError } from './helpers'
import { useUserStore } from '@/store'

export function reqResolve(config) {
  // 处理不需要token的请求
  if (config.noNeedToken) {
    return config
  }

  const token = getToken()
  if (token) {
    config.headers.token = config.headers.token || token
  }

  return config
}

export function reqReject(error) {
  return Promise.reject(error)
}

export function resResolve(response) {
  const { data, status, statusText } = response
  
  // 非200状态码数据，转换成标准错误对象但不显示消息
  if (data?.code !== 200) {
    const code = data?.code ?? status
    
    // 直接使用后端返回的错误消息，不再通过resolveResError处理
    const message = data?.msg ?? statusText
    
    // 构造标准错误对象，但不自动显示错误消息
    // 由业务代码决定如何处理这个错误
    return Promise.reject({
      code, 
      message, 
      error: data || response,
      // 添加类型标记，表明这是业务错误而非网络错误
      type: 'business_error'
    })
  }
  
  return Promise.resolve(data)
}

export async function resReject(error) {
  // 处理网络或请求错误（非业务逻辑错误）
  if (!error || !error.response) {
    const code = error?.code
    const message = error?.message || '网络连接错误'
    
    // 网络错误自动显示通知
    window.$message?.error(message)
    return Promise.reject({ 
      code, 
      message, 
      error,
      type: 'network_error'
    })
  }
  
  const { data, status } = error.response

  // 处理401认证错误
  if (data?.code === 401) {
    try {
      const userStore = useUserStore()
      userStore.logout()
      window.$message?.error('登录已过期，请重新登录')
      return Promise.reject({
        code: 401,
        message: '登录已过期，请重新登录',
        type: 'auth_error'
      })
    } catch (error) {
      console.log('resReject error', error)
      return
    }
  }
  
  // 构造业务错误对象，直接使用后端返回的错误消息
  const code = data?.code ?? status
  const message = data?.msg ?? error.message
  
  return Promise.reject({
    code, 
    message, 
    error: error.response?.data || error.response,
    type: 'business_error'
  })
}
