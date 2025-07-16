import { useEffect, useState } from 'react'
import { Row, Col, Card, Statistic, Progress, Table, Badge, Space } from 'antd'
import {
  UserOutlined,
  TeamOutlined,
  ApartmentOutlined,
  FileTextOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
} from '@ant-design/icons'

const Dashboard = () => {
  const [loading, setLoading] = useState(false)

  // 模拟统计数据
  const statistics = [
    {
      title: '用户总数',
      value: 1128,
      icon: <UserOutlined />,
      color: '#1890ff',
      growth: 12.5,
    },
    {
      title: '角色数量',
      value: 8,
      icon: <TeamOutlined />,
      color: '#52c41a',
      growth: 8.2,
    },
    {
      title: '部门数量',
      value: 15,
      icon: <ApartmentOutlined />,
      color: '#722ed1',
      growth: -2.1,
    },
    {
      title: '今日访问',
      value: 2847,
      icon: <FileTextOutlined />,
      color: '#fa8c16',
      growth: 15.8,
    },
  ]

  // 最近活动数据
  const recentActivities = [
    {
      key: '1',
      user: 'admin',
      action: '创建用户',
      target: 'user_001',
      time: '2024-01-15 10:30:25',
      status: 'success',
    },
    {
      key: '2',
      user: 'manager',
      action: '更新角色权限',
      target: 'role_editor',
      time: '2024-01-15 09:45:12',
      status: 'success',
    },
    {
      key: '3',
      user: 'editor',
      action: '删除菜单',
      target: 'menu_test',
      time: '2024-01-15 09:15:33',
      status: 'warning',
    },
    {
      key: '4',
      user: 'user_001',
      action: '登录系统',
      target: '系统',
      time: '2024-01-15 08:30:15',
      status: 'success',
    },
  ]

  const activityColumns = [
    {
      title: '用户',
      dataIndex: 'user',
      key: 'user',
    },
    {
      title: '操作',
      dataIndex: 'action',
      key: 'action',
    },
    {
      title: '目标',
      dataIndex: 'target',
      key: 'target',
    },
    {
      title: '时间',
      dataIndex: 'time',
      key: 'time',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status) => (
        <Badge 
          status={status === 'success' ? 'success' : 'warning'} 
          text={status === 'success' ? '成功' : '警告'} 
        />
      ),
    },
  ]

  useEffect(() => {
    // 这里可以加载实际的统计数据
    setLoading(false)
  }, [])

  return (
    <div className="space-y-6">
      {/* 欢迎标题 */}
      <div className="bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg p-6 text-white">
        <h1 className="text-2xl font-bold mb-2">欢迎来到 FastAPI Admin 管理系统</h1>
        <p className="opacity-90">现代化的前后端分离管理平台，基于 React + Ant Design + Tailwind CSS</p>
      </div>

      {/* 统计卡片 */}
      <Row gutter={[16, 16]}>
        {statistics.map((stat, index) => (
          <Col xs={24} sm={12} lg={6} key={index}>
            <Card hoverable className="h-full">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <p className="text-gray-500 text-sm mb-1">{stat.title}</p>
                  <Statistic 
                    value={stat.value} 
                    valueStyle={{ fontSize: '24px', fontWeight: 'bold' }}
                  />
                  <div className="flex items-center mt-2">
                    {stat.growth > 0 ? (
                      <ArrowUpOutlined className="text-green-500 text-xs mr-1" />
                    ) : (
                      <ArrowDownOutlined className="text-red-500 text-xs mr-1" />
                    )}
                    <span 
                      className={`text-xs ${
                        stat.growth > 0 ? 'text-green-500' : 'text-red-500'
                      }`}
                    >
                      {Math.abs(stat.growth)}%
                    </span>
                    <span className="text-gray-400 text-xs ml-1">较上周</span>
                  </div>
                </div>
                <div 
                  className="w-12 h-12 rounded-lg flex items-center justify-center text-white text-xl"
                  style={{ backgroundColor: stat.color }}
                >
                  {stat.icon}
                </div>
              </div>
            </Card>
          </Col>
        ))}
      </Row>

      {/* 图表和活动 */}
      <Row gutter={[16, 16]}>
        {/* 系统状态 */}
        <Col xs={24} lg={12}>
          <Card title="系统状态" hoverable>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span>CPU 使用率</span>
                  <span className="text-blue-500 font-medium">45%</span>
                </div>
                <Progress percent={45} strokeColor="#1890ff" />
              </div>
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span>内存使用率</span>
                  <span className="text-green-500 font-medium">68%</span>
                </div>
                <Progress percent={68} strokeColor="#52c41a" />
              </div>
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span>磁盘使用率</span>
                  <span className="text-orange-500 font-medium">32%</span>
                </div>
                <Progress percent={32} strokeColor="#fa8c16" />
              </div>
            </div>
          </Card>
        </Col>

        {/* 快速操作 */}
        <Col xs={24} lg={12}>
          <Card title="快速操作" hoverable>
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 bg-blue-50 rounded-lg hover:bg-blue-100 cursor-pointer transition-colors">
                <UserOutlined className="text-2xl text-blue-500 mb-2" />
                <div className="text-sm font-medium">创建用户</div>
              </div>
              <div className="p-4 bg-green-50 rounded-lg hover:bg-green-100 cursor-pointer transition-colors">
                <TeamOutlined className="text-2xl text-green-500 mb-2" />
                <div className="text-sm font-medium">添加角色</div>
              </div>
              <div className="p-4 bg-purple-50 rounded-lg hover:bg-purple-100 cursor-pointer transition-colors">
                <ApartmentOutlined className="text-2xl text-purple-500 mb-2" />
                <div className="text-sm font-medium">新建部门</div>
              </div>
              <div className="p-4 bg-orange-50 rounded-lg hover:bg-orange-100 cursor-pointer transition-colors">
                <FileTextOutlined className="text-2xl text-orange-500 mb-2" />
                <div className="text-sm font-medium">查看日志</div>
              </div>
            </div>
          </Card>
        </Col>
      </Row>

      {/* 最近活动 */}
      <Card title="最近活动" hoverable>
        <Table
          columns={activityColumns}
          dataSource={recentActivities}
          pagination={{ pageSize: 5 }}
          loading={loading}
          size="small"
        />
      </Card>
    </div>
  )
}

export default Dashboard 