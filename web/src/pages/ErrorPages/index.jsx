import { Button, Result } from 'antd'
import { useNavigate } from 'react-router-dom'
import { HomeOutlined, ArrowLeftOutlined, ReloadOutlined } from '@ant-design/icons'

// 错误类型配置
const errorConfig = {
  403: {
    status: '403',
    title: '403',
    subTitle: '抱歉，您没有权限访问此页面',
  },
  404: {
    status: '404',
    title: '404',
    subTitle: '抱歉，您访问的页面不存在',
  },
  500: {
    status: '500',
    title: '500',
    subTitle: '抱歉，服务器出现了问题',
  },
  warning: {
    status: 'warning',
    title: '警告',
    subTitle: '您的操作可能存在风险',
  },
  info: {
    status: 'info',
    title: '提示',
    subTitle: '请注意相关信息',
  }
}

const ErrorPage = ({ type = '404', title, subTitle, showReload = false }) => {
  const navigate = useNavigate()
  const config = errorConfig[type] || errorConfig['404']

  const handleBackHome = () => {
    navigate('/dashboard')
  }

  const handleGoBack = () => {
    navigate(-1)
  }

  const handleReload = () => {
    window.location.reload()
  }

  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <Result
        status={config.status}
        title={title || config.title}
        subTitle={subTitle || config.subTitle}
        extra={
          <div className="space-x-2">
            <Button 
              type="primary" 
              icon={<HomeOutlined />}
              onClick={handleBackHome}
              className="bg-blue-500 hover:bg-blue-600"
            >
              返回首页
            </Button>
            <Button 
              icon={<ArrowLeftOutlined />}
              onClick={handleGoBack}
            >
              返回上页
            </Button>
            {showReload && (
              <Button 
                icon={<ReloadOutlined />}
                onClick={handleReload}
              >
                重新加载
              </Button>
            )}
          </div>
        }
      />
    </div>
  )
}

// 预定义的错误页面组件
export const NotFoundPage = () => <ErrorPage type="404" />
export const ForbiddenPage = () => <ErrorPage type="403" />
export const ServerErrorPage = () => <ErrorPage type="500" showReload />

export default ErrorPage 