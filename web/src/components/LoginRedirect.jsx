import { Navigate } from 'react-router-dom'
import Login from '@/pages/Login'

const LoginRedirect = () => {
  const token = localStorage.getItem('token')
  
  if (token) {
    return <Navigate to="/dashboard" replace />
  }
  
  return <Login />
}

export default LoginRedirect 