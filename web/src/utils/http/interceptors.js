import { getToken } from '@/utils'
import { resolveResError } from './helpers'
import { useUserStore } from '@/store'
import { router } from '@/router'

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
  if (data?.code !== 200) {
    const code = data?.code ?? status
    /** 根据code处理对应的操作，并返回处理后的message */
    const message = resolveResError(code, data?.msg ?? statusText)
    window.$message?.error(message, { keepAliveOnHover: true })
    return Promise.reject({ code, message, error: data || response })
  }
  return Promise.resolve(data)
}

export async function resReject(error) {
  if (!error || !error.response) {
    const code = error?.code
    /** 根据code处理对应的操作，并返回处理后的message */
    const message = resolveResError(code, error.message)
    window.$message?.error(message)
    return Promise.reject({ code, message, error })
  }
  const { data, status } = error.response
  const code = data?.code ?? status

  // 根据错误码跳转到对应的错误页面
  if (code === 401) {
    try {
      const userStore = useUserStore()
      userStore.logout()
    } catch (error) {
      console.log('resReject error', error)
    }
  } else if (code === 403) {
    router.replace('/403')
  } else if (code === 404) {
    router.replace('/404')
  } else if (code >= 500) {
    router.replace('/500')
  }

  // 后端返回的response数据
  const message = resolveResError(code, data?.msg ?? error.message)
  window.$message?.error(message, { keepAliveOnHover: true })
  return Promise.reject({ code, message, error: error.response?.data || error.response })
}
