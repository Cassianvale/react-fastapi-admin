import { useUserStore } from '@/store'

export function addBaseParams(params) {
  if (!params.userId) {
    params.userId = useUserStore().userId
  }
}

/**
 * 处理常见的错误码和错误消息
 * @param {number} code - 错误码
 * @param {string} msg - 错误消息
 * @returns {string} - 处理后的错误消息
 */
export function resolveResError(code, msg) {
  // 如果后端提供了明确的错误消息，优先使用
  if (msg) {
    return msg;
  }
  
  // 只有当后端没有提供错误消息时，才使用通用错误映射
  const codeMsgMap = {
    400: '请求错误',
    401: '未授权，请重新登录',
    403: '拒绝访问',
    404: '请求地址不存在',
    500: '服务器内部错误',
    501: '服务未实现',
    502: '网关错误',
    503: '服务不可用',
    504: '网关超时',
    505: 'HTTP版本不支持',
  }
  
  return codeMsgMap[code] || '未知错误'
}

/**
 * 处理业务错误并显示错误消息
 * @param {object} error - 错误对象
 * @param {function} customHandler - 自定义处理特定错误的函数，返回true表示已处理
 */
export function handleBusinessError(error, customHandler) {
  // 如果不是业务错误或没有错误对象，直接返回
  if (!error) {
    return false
  }
  
  // 如果提供了自定义处理函数并且处理了错误，则返回
  if (customHandler && customHandler(error)) {
    return true
  }
  
  // 默认显示错误消息 - 直接使用错误的message属性
  if (window.$message && error.message) {
    window.$message.error(error.message)
    return true
  }
  
  return false
}

