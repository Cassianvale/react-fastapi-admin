<p align="center">

</p>

<h1 align="center">react-fastapi-admin</h1>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.10+-blue">
  <img alt="License" src="https://img.shields.io/badge/License-MIT-blue">
</p>

### 快速开始

#### 方法一：dockerhub 拉取镜像

```sh
docker pull mizhexiaoxiao/react-fastapi-admin:latest
docker run -d --restart=always --name=react-fastapi-admin -p 9999:80 mizhexiaoxiao/react-fastapi-admin
```

#### 方法二：dockerfile 构建镜像

##### docker 安装(版本 17.05+)

```sh
yum install -y docker-ce
systemctl start docker
```

##### 构建镜像

```sh
git clone https://github.com/mizhexiaoxiao/react-fastapi-admin.git
cd react-fastapi-admin
docker build --no-cache . -t react-fastapi-admin
```

##### 启动容器

```sh
docker run -d --restart=always --name=react-fastapi-admin -p 9999:80 react-fastapi-admin
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
