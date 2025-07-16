import { App } from 'antd'
import { parseError, globalErrorHandler, ERROR_TYPES } from '@/utils/errorHandler'

/**
 * 错误处理Hook
 * 使用Ant Design的App组件提供的message API，避免静态函数警告
 * 支持自定义错误处理器和全局错误处理
 */
export const useErrorHandler = () => {
    const { message } = App.useApp()

    /**
     * 处理API错误的通用方法
     * @param {Object} error - 原始错误对象
     * @param {string} defaultMessage - 默认错误消息
     * @param {Function} customHandler - 自定义错误处理函数
     * @returns {Object} 标准化的错误对象
     */
    const handleError = (error, defaultMessage = '操作失败，请重试', customHandler = null) => {
        // 解析错误对象
        const standardError = parseError(error, defaultMessage)

        // 如果有自定义处理器，使用自定义处理器
        if (customHandler && typeof customHandler === 'function') {
            return customHandler(standardError)
        }

        // 使用全局错误处理器
        const result = globalErrorHandler.handle(standardError)

        // 如果全局处理器没有处理，使用默认处理逻辑
        if (result === standardError) {
            handleDefaultError(standardError)
        }

        return standardError
    }

    /**
     * 默认错误处理逻辑
     * @param {Object} standardError - 标准化错误对象
     */
    const handleDefaultError = (standardError) => {
        switch (standardError.type) {
            case ERROR_TYPES.BUSINESS_ERROR:
                message.error(standardError.message)
                break
            case ERROR_TYPES.NETWORK_ERROR:
                message.error(standardError.message)
                break
            case ERROR_TYPES.AUTH_ERROR:
                message.error(standardError.message)
                break
            case ERROR_TYPES.SYSTEM_ERROR:
                message.error(standardError.message)
                break
            default:
                message.error(standardError.message)
        }
    }

    /**
     * 处理业务错误（始终显示错误消息）
     * @param {Object} error - 错误对象
     * @param {string} defaultMessage - 默认错误消息
     * @param {Function} customHandler - 自定义错误处理函数
     * @returns {Object} 标准化的错误对象
     */
    const handleBusinessError = (error, defaultMessage = '操作失败，请重试', customHandler = null) => {
        const standardError = parseError(error, defaultMessage)

        if (customHandler && typeof customHandler === 'function') {
            return customHandler(standardError)
        }

        message.error(standardError.message)
        return standardError
    }

    /**
     * 静默处理错误（不显示消息）
     * @param {Object} error - 错误对象
     * @param {string} defaultMessage - 默认错误消息
     * @returns {Object} 标准化的错误对象
     */
    const handleSilentError = (error, defaultMessage = '操作失败，请重试') => {
        return parseError(error, defaultMessage)
    }

    /**
     * 处理网络错误
     * @param {Object} error - 错误对象
     * @param {Function} customHandler - 自定义错误处理函数
     * @returns {Object} 标准化的错误对象
     */
    const handleNetworkError = (error, customHandler = null) => {
        const standardError = parseError(error, '网络连接失败，请检查网络设置')

        if (customHandler && typeof customHandler === 'function') {
            return customHandler(standardError)
        }

        if (standardError.type === ERROR_TYPES.NETWORK_ERROR) {
            message.error(standardError.message)
        }

        return standardError
    }

    /**
     * 注册全局错误处理器
     * @param {string} errorType - 错误类型
     * @param {Function} handler - 处理函数
     */
    const registerGlobalHandler = (errorType, handler) => {
        globalErrorHandler.register(errorType, handler)
    }

    /**
     * 设置默认全局错误处理器
     * @param {Function} handler - 默认处理函数
     */
    const setDefaultGlobalHandler = (handler) => {
        globalErrorHandler.setDefault(handler)
    }

    /**
     * 显示成功消息
     * @param {string} msg - 成功消息
     */
    const showSuccess = (msg) => {
        message.success(msg)
    }

    /**
     * 显示警告消息
     * @param {string} msg - 警告消息
     */
    const showWarning = (msg) => {
        message.warning(msg)
    }

    /**
     * 显示信息消息
     * @param {string} msg - 信息消息
     */
    const showInfo = (msg) => {
        message.info(msg)
    }

    /**
     * 显示加载消息
     * @param {string} msg - 加载消息
     * @param {number} duration - 持续时间
     */
    const showLoading = (msg = '加载中...', duration = 0) => {
        return message.loading(msg, duration)
    }

    return {
        // 错误处理方法
        handleError,
        handleBusinessError,
        handleSilentError,
        handleNetworkError,

        // 全局错误处理器管理
        registerGlobalHandler,
        setDefaultGlobalHandler,

        // 消息显示方法
        showSuccess,
        showWarning,
        showInfo,
        showLoading,

        // 原始API（备用）
        message,
    }
} 