/**
 * 全局错误处理器初始化配置
 * 在应用启动时注册不同类型错误的处理函数
 */

import { globalErrorHandler, ERROR_TYPES, parseError } from './errorHandler'

/**
 * 初始化全局错误处理器
 * @param {Object} messageApi - Ant Design的message API实例（可选）
 */
export const initializeGlobalErrorHandler = (messageApi = null) => {
    // 注册业务错误处理器
    globalErrorHandler.register(ERROR_TYPES.BUSINESS_ERROR, (error) => {
        if (messageApi) {
            messageApi.error(error.message)
        } else {
            console.error('Business Error:', error.message)
        }
        return error
    })

    // 注册网络错误处理器
    globalErrorHandler.register(ERROR_TYPES.NETWORK_ERROR, (error) => {
        if (messageApi) {
            messageApi.error(error.message)
        } else {
            console.error('Network Error:', error.message)
        }
        return error
    })

    // 注册认证错误处理器
    globalErrorHandler.register(ERROR_TYPES.AUTH_ERROR, (error) => {
        if (messageApi) {
            messageApi.error(error.message)
        } else {
            console.error('Auth Error:', error.message)
        }
        // 认证错误的重定向已在errorHandler中处理
        return error
    })

    // 注册系统错误处理器
    globalErrorHandler.register(ERROR_TYPES.SYSTEM_ERROR, (error) => {
        if (messageApi) {
            messageApi.error(error.message)
        } else {
            console.error('System Error:', error.message)
        }

        // 系统错误可以进行额外的处理，如上报错误
        reportSystemError(error)
        return error
    })

    // 设置默认错误处理器
    globalErrorHandler.setDefault((error) => {
        if (messageApi) {
            messageApi.error(error.message || '未知错误')
        } else {
            console.error('Unknown Error:', error)
        }
        return error
    })
}

/**
 * 上报系统错误（示例函数）
 * @param {Object} error - 错误对象
 */
const reportSystemError = (error) => {
    // 这里可以集成错误监控服务，如Sentry等
    console.group('System Error Report')
    console.error('Error Type:', error.type)
    console.error('Error Message:', error.message)
    console.error('Error Code:', error.code)
    console.error('Timestamp:', error.timestamp)
    console.error('Original Error:', error.originalError)
    console.groupEnd()
}

/**
 * 创建带有全局错误处理的API调用包装器
 * @param {Function} apiCall - API调用函数
 * @param {string} errorMessage - 默认错误消息
 * @param {Function} customHandler - 自定义错误处理函数
 * @returns {Function} 包装后的API调用函数
 */
export const createApiWrapper = (apiCall, errorMessage = '操作失败', customHandler = null) => {
    return async (...args) => {
        try {
            return await apiCall(...args)
        } catch (error) {
            const standardError = parseError(error, errorMessage)

            if (customHandler) {
                return customHandler(standardError)
            }

            globalErrorHandler.handle(standardError)
            throw standardError
        }
    }
}

/**
 * 错误边界组件的错误处理函数
 * @param {Error} error - JavaScript错误对象
 * @param {Object} errorInfo - 错误信息
 */
export const handleErrorBoundaryError = (error, errorInfo) => {
    const standardError = {
        type: ERROR_TYPES.SYSTEM_ERROR,
        message: error.message || '应用程序发生未知错误',
        code: 0,
        data: {
            stack: error.stack,
            componentStack: errorInfo.componentStack,
        },
        originalError: error,
        timestamp: new Date().toISOString(),
    }

    globalErrorHandler.handle(standardError)

    // 上报错误到监控服务
    reportSystemError(standardError)
} 