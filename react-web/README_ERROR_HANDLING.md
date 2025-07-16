# 错误处理系统使用指南

## 概述

本项目采用了完善的错误处理系统，明确区分了不同类型的错误，提供了统一的错误处理机制，并支持自定义错误处理器。

## 错误类型分类

### 1. 业务错误 (BUSINESS_ERROR)

- **定义**: 业务逻辑相关的错误，如表单验证失败、数据冲突等
- **HTTP 状态码**: 400, 422, 409, 412
- **处理方式**: 显示具体的错误消息给用户

### 2. 网络错误 (NETWORK_ERROR)

- **定义**: 网络连接失败、请求超时等网络层面的错误
- **特征**: 没有 response 对象
- **处理方式**: 显示网络错误提示

### 3. 认证错误 (AUTH_ERROR)

- **定义**: 认证和授权相关的错误
- **HTTP 状态码**: 401, 403
- **处理方式**: 清除认证信息，重定向到登录页

### 4. 系统错误 (SYSTEM_ERROR)

- **定义**: 服务器内部错误、网关错误等系统级错误
- **HTTP 状态码**: 500, 502, 503, 504
- **处理方式**: 显示系统错误提示，可选择上报错误

## 使用方法

### 1. 基础使用

```jsx
import { useErrorHandler } from "@/hooks/useErrorHandler";

const MyComponent = () => {
  const { handleError, handleBusinessError, showSuccess } = useErrorHandler();

  const handleSubmit = async (values) => {
    try {
      await api.submitForm(values);
      showSuccess("提交成功！");
    } catch (error) {
      // 自动识别错误类型并处理
      handleError(error, "提交失败，请重试");
    }
  };
};
```

### 2. 业务错误处理

```jsx
const handleBusinessAction = async () => {
  try {
    await api.businessAction();
  } catch (error) {
    // 始终显示错误消息
    handleBusinessError(error, "操作失败");
  }
};
```

### 3. 自定义错误处理

```jsx
const handleCustomAction = async () => {
  try {
    await api.customAction();
  } catch (error) {
    handleBusinessError(error, "操作失败", (standardError) => {
      // 自定义处理逻辑
      if (standardError.message.includes("特定关键词")) {
        showWarning("特定的警告消息");
      } else {
        message.error(standardError.message);
      }
      return standardError;
    });
  }
};
```

### 4. 静默错误处理

```jsx
const handleSilentAction = async () => {
  try {
    await api.silentAction();
  } catch (error) {
    // 不显示错误消息，只记录错误
    const standardError = handleSilentError(error);
    console.log("Silent error:", standardError);
  }
};
```

## 响应拦截器优化

新的响应拦截器在 `resResolve` 中处理业务错误，在 `error` 中处理网络错误：

```javascript
// 响应成功处理
(response) => {
  // 检查业务成功
  if (isBusinessSuccess(response)) {
    return response.data;
  }

  // 检查业务错误（在正常HTTP响应中）
  if (isBusinessError(response)) {
    const error = new Error("Business Error");
    error.response = response;
    return Promise.reject(error);
  }
};

// 网络错误处理
(error) => {
  // 处理认证错误
  if (error.response?.status === 401) {
    handleAuthError(error.response.status);
  }

  return Promise.reject(error);
};
```

## 全局错误处理器

### 注册全局处理器

```jsx
import { useErrorHandler } from "@/hooks/useErrorHandler";

const App = () => {
  const { registerGlobalHandler } = useErrorHandler();

  useEffect(() => {
    // 注册业务错误的全局处理器
    registerGlobalHandler(ERROR_TYPES.BUSINESS_ERROR, (error) => {
      console.log("Global business error handler:", error);
      // 可以进行错误上报等操作
      return error;
    });
  }, []);
};
```

### 设置默认处理器

```jsx
const { setDefaultGlobalHandler } = useErrorHandler();

setDefaultGlobalHandler((error) => {
  console.error("Default error handler:", error);
  // 上报到错误监控服务
  reportError(error);
  return error;
});
```

## 错误对象结构

标准化的错误对象包含以下字段：

```javascript
{
  type: 'business_error',           // 错误类型
  message: '用户友好的错误消息',      // 错误消息
  code: 422,                       // HTTP状态码
  data: { /* 附加数据 */ },         // 后端返回的数据
  originalError: Error,            // 原始错误对象
  timestamp: '2024-01-01T00:00:00Z' // 时间戳
}
```

## 最佳实践

### 1. 错误处理优先级

1. 优先使用后端返回的错误消息 (`data.msg`)
2. 其次使用其他错误字段 (`data.message`, `data.detail`)
3. 最后使用通用错误映射

### 2. 错误类型选择

- **表单提交**: 使用 `handleBusinessError`
- **数据获取**: 使用 `handleError`
- **不需要提示**: 使用 `handleSilentError`
- **需要特殊处理**: 使用自定义处理器

### 3. 消息显示

- **成功操作**: `showSuccess`
- **警告信息**: `showWarning`
- **一般信息**: `showInfo`
- **加载状态**: `showLoading`

### 4. 错误上报

对于系统错误，建议集成错误监控服务：

```javascript
const reportSystemError = (error) => {
  // 集成 Sentry、LogRocket 等错误监控服务
  Sentry.captureException(error.originalError, {
    tags: {
      errorType: error.type,
      errorCode: error.code,
    },
    extra: {
      message: error.message,
      data: error.data,
      timestamp: error.timestamp,
    },
  });
};
```

## API 包装器

使用 `createApiWrapper` 为 API 调用添加统一的错误处理：

```javascript
import { createApiWrapper } from "@/utils/errorInit";

const wrappedApiCall = createApiWrapper(
  api.someEndpoint,
  "操作失败",
  (error) => {
    // 自定义错误处理
    console.log("Custom error handling:", error);
    return error;
  }
);

// 使用包装后的API
await wrappedApiCall(params);
```

## 总结

这个错误处理系统的主要优势：

1. **类型明确**: 清楚区分不同类型的错误
2. **处理统一**: 提供一致的错误处理接口
3. **扩展性强**: 支持自定义处理器和全局配置
4. **用户友好**: 优先显示后端提供的具体错误信息
5. **开发友好**: 避免了 Ant Design 静态函数警告
6. **维护性好**: 集中管理错误处理逻辑
