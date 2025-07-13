<p align="center">
  <a href="https://github.com/mizhexiaoxiao/vue-fastapi-admin">
    <img alt="Vue FastAPI Admin Logo" width="200" src="https://github.com/mizhexiaoxiao/vue-fastapi-admin/blob/main/deploy/sample-picture/logo.svg">
  </a>
</p>

<h1 align="center">vue-fastapi-admin</h1>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.10+-blue">
  <img alt="License" src="https://img.shields.io/badge/License-MIT-blue">
</p>

基于 FastAPI + Vue3 + Naive UI 的现代化前后端分离开发平台，采用 Granian 高性能服务器、Tortoise ORM 异步数据库、Aerich 数据库迁移和 Loguru 智能日志系统，融合了 RBAC 权限管理、动态路由和 JWT 鉴权，助力中小型应用快速搭建，也可用于学习参考。

### 特性

- **现代化技术栈**：
  - **后端框架**：基于 Python 3.11 和 FastAPI 高性能异步框架
  - **数据库 ORM**：使用 Tortoise ORM 异步数据库，配合 Aerich 进行数据库迁移管理
  - **ASGI 服务器**：采用 Granian 高性能 ASGI 服务器，支持热重载和优化的生产环境部署
  - **日志系统**：集成 Loguru 现代化日志库，提供结构化日志记录和丰富的日志管理功能
  - **前端技术**：Vue3 + Vite + Naive UI + Pinia，配合高效的包管理器 pnpm
- **企业级特性**：
  - **数据库迁移**：使用 Aerich 实现版本化数据库迁移，支持多种数据库（SQLite、MySQL、PostgreSQL）
  - **智能日志**：基于 Loguru 的多级日志系统，支持日志轮转、压缩和结构化输出
  - **高性能服务**：Granian 服务器提供优异的并发性能和内存效率
- **代码规范**：项目内置丰富的规范插件，确保代码质量和一致性，有效提高团队协作效率。
- **动态路由**：后端动态路由，结合 RBAC（Role-Based Access Control）权限模型，提供精细的菜单路由控制。
- **JWT 鉴权**：使用 JSON Web Token（JWT）进行身份验证和授权，增强应用的安全性。
- **细粒度权限控制**：实现按钮和接口级别的权限控制，确保不同用户或角色在界面操作和接口访问时具有不同的权限限制。
- **完整审计日志**：记录所有用户操作和系统活动，提供完整的操作追踪和审计功能。

### 在线预览

- http://vue-fastapi-admin.com
- username: admin
- password: 123456

### 登录页

![image](https://github.com/mizhexiaoxiao/vue-fastapi-admin/blob/main/deploy/sample-picture/login.jpg)

### 工作台

![image](https://github.com/mizhexiaoxiao/vue-fastapi-admin/blob/main/deploy/sample-picture/workbench.jpg)

### 用户管理

![image](https://github.com/mizhexiaoxiao/vue-fastapi-admin/blob/main/deploy/sample-picture/user.jpg)

### 角色管理

![image](https://github.com/mizhexiaoxiao/vue-fastapi-admin/blob/main/deploy/sample-picture/role.jpg)

### 菜单管理

![image](https://github.com/mizhexiaoxiao/vue-fastapi-admin/blob/main/deploy/sample-picture/menu.jpg)

### API 管理

![image](https://github.com/mizhexiaoxiao/vue-fastapi-admin/blob/main/deploy/sample-picture/api.jpg)

### 快速开始

#### 方法一：dockerhub 拉取镜像

```sh
docker pull mizhexiaoxiao/vue-fastapi-admin:latest
docker run -d --restart=always --name=vue-fastapi-admin -p 9999:80 mizhexiaoxiao/vue-fastapi-admin
```

#### 方法二：dockerfile 构建镜像

##### docker 安装(版本 17.05+)

```sh
yum install -y docker-ce
systemctl start docker
```

##### 构建镜像

```sh
git clone https://github.com/mizhexiaoxiao/vue-fastapi-admin.git
cd vue-fastapi-admin
docker build --no-cache . -t vue-fastapi-admin
```

##### 启动容器

```sh
docker run -d --restart=always --name=vue-fastapi-admin -p 9999:80 vue-fastapi-admin
```

##### 访问

http://localhost:9999

username：admin

password：123456

### 本地启动

#### 后端

启动项目需要以下环境：

- Python 3.11

#### 方法一（推荐）：使用 uv 安装依赖

1. 安装 uv

```sh
pip install uv
```

2. 创建并激活虚拟环境

```sh
uv venv
source .venv/bin/activate  # Linux/Mac
# 或
.\.venv\Scripts\activate  # Windows
```

3. 安装依赖

```sh
uv add pyproject.toml
```

4. 数据库迁移（可选）

```sh
# 生成迁移文件
aerich migrate

# 应用迁移
aerich upgrade
```

5. 启动服务

```sh
# 直接启动（使用 Granian 服务器）
python main.py

# 或者使用 Make 命令
make start
```

服务现在应该正在运行，访问 http://localhost:9999/docs 查看 API 文档

#### 方法二：使用 pip 安装依赖

```sh
pip install -r requirements.in
python main.py
```

#### 技术栈说明

- **Granian 服务器**：项目使用 Granian 作为 ASGI 服务器，提供高性能的异步处理能力
- **Tortoise ORM**：异步数据库 ORM，支持 SQLite、MySQL、PostgreSQL
- **Aerich**：数据库迁移工具，类似 Django 的 migrations
- **Loguru**：现代化日志库，提供结构化日志和丰富的配置选项

#### 前端

启动项目需要以下环境：

- node v18.8.0+

1. 进入前端目录

```sh
cd web
```

2. 安装依赖(建议使用 pnpm: https://pnpm.io/zh/installation)

```sh
npm i -g pnpm # 已安装可忽略
pnpm i # 或者 npm i
```

3. 启动

```sh
pnpm dev
```
