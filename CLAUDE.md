# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

React FastAPI Admin is a full-stack admin panel with React frontend and FastAPI backend, featuring role-based permissions, audit logging, and comprehensive user management.

## Quick Commands

### Backend (Python)

```bash
# Install dependencies
uv add pyproject.toml
# or
pip install -r requirements.in

# Start development server
python main.py
# or
make start

# Database operations
make migrate      # Generate migrations
make upgrade     # Apply migrations
make clean-db    # Reset database

# Code quality
make check       # Format + lint check
make format      # Auto-format code
make lint        # Run ruff linter
make test        # Run test suite
```

### Frontend (React)

```bash
cd web
pnpm install     # or npm install
pnpm dev         # Development server
pnpm build       # Production build
pnpm lint        # ESLint check
```

### Docker

```bash
# Build and run
docker build -t react-fastapi-admin .
docker run -p 9999:80 react-fastapi-admin

# From Docker Hub
docker pull mizhexiaoxiao/react-fastapi-admin:latest
docker run -p 9999:80 mizhexiaoxiao/react-fastapi-admin
```

## Architecture Key Points

### Backend Structure

- **Entry Point**: `main.py` – Granian ASGI server on port 9999
- **API Routes**: `app/api/v1/` - RESTful endpoints for users, roles, menus, APIs, depts, audit logs
- **Models**: `app/models/admin.py` - User, Role, Menu, Api, Dept, AuditLog with relationships
- **Controllers**: `app/controllers/` - Business logic layer with CRUDBase generic controller
- **Schemas**: `app/schemas/` - Pydantic models for validation
- **Authentication**: JWT-based with role-based permissions (RBAC)

### Frontend Structure

- **Entry**: `web/src/main.jsx` – React Router with protected routes
- **Layout**: Tab-based interface with Ant Design Pro layout
- **Pages**: User/Role/Menu/API/Dept management, Dashboard, Audit logs
- **API**: `web/src/api/index.js` - Axios client with interceptors
- **Authentication**: Token-based with dynamic menu loading

### Key Patterns

- **Permission System**: Role-Menu-API associations for granular access control
- **Audit Logging**: All operations tracked via HttpAuditLogMiddleware
- **File Upload**: OSS cloud storage (production) or local storage (development)
- **Database**: Tortoise ORM with Aerich migrations, supports SQLite/MySQL/PostgreSQL

### Development URLs

- **Backend API**: http://localhost:9999/docs (Swagger UI)
- **Frontend Dev**: http://localhost:5173 (Vite dev server)
- **Production**: http://localhost:9999 (combined build)
