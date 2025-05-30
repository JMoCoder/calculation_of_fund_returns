# 收益分配测算系统 - API接口设计

## 1. API设计概述

### 1.1 设计原则
- **RESTful风格**: 遵循REST架构风格，使用标准HTTP方法
- **统一响应格式**: 所有API返回统一的JSON格式
- **版本控制**: 支持API版本管理，确保向后兼容
- **安全优先**: 实现请求验证、数据校验和安全防护
- **高性能**: 优化响应时间，支持并发处理
- **易于使用**: 提供清晰的接口文档和错误信息

### 1.2 API架构

```
┌─────────────────────────────────────────────────────────┐
│                    API架构层次                           │
├─────────────────────────────────────────────────────────┤
│ 1. 接入层 (Gateway Layer)                               │
│    - 请求路由                                            │
│    - 负载均衡                                            │
│    - 限流控制                                            │
│                                                         │
│ 2. 认证层 (Authentication Layer)                        │
│    - 会话验证                                            │
│    - 权限检查                                            │
│    - 安全防护                                            │
│                                                         │
│ 3. 业务层 (Business Layer)                              │
│    - 参数验证                                            │
│    - 业务逻辑                                            │
│    - 数据处理                                            │
│                                                         │
│ 4. 数据层 (Data Layer)                                  │
│    - 缓存操作                                            │
│    - 文件处理                                            │
│    - 数据存储                                            │
└─────────────────────────────────────────────────────────┘
```

### 1.3 基础URL结构

```
Base URL: http://localhost:8000/api/v1

路径结构:
/api/v1/{module}/{resource}/{action}

示例:
- /api/v1/session/create
- /api/v1/calculation/execute
- /api/v1/file/upload
- /api/v1/export/excel
```

## 2. 通用规范

### 2.1 HTTP状态码

| 状态码 | 含义 | 使用场景 |
|--------|------|----------|
| 200 | OK | 请求成功 |
| 201 | Created | 资源创建成功 |
| 400 | Bad Request | 请求参数错误 |
| 401 | Unauthorized | 未授权访问 |
| 403 | Forbidden | 禁止访问 |
| 404 | Not Found | 资源不存在 |
| 422 | Unprocessable Entity | 数据验证失败 |
| 429 | Too Many Requests | 请求频率超限 |
| 500 | Internal Server Error | 服务器内部错误 |
| 503 | Service Unavailable | 服务不可用 |

### 2.2 统一响应格式

#### 成功响应
```json
{
  "success": true,
  "code": 200,
  "message": "操作成功",
  "data": {
    // 具体数据内容
  },
  "timestamp": "2024-01-15T12:30:45Z",
  "request_id": "req_550e8400-e29b-41d4-a716-446655440000"
}
```

#### 错误响应
```json
{
  "success": false,
  "code": 400,
  "message": "请求参数错误",
  "error": {
    "type": "ValidationError",
    "details": [
      {
        "field": "investment_amount",
        "message": "投资金额必须大于0",
        "code": "INVALID_VALUE"
      }
    ]
  },
  "timestamp": "2024-01-15T12:30:45Z",
  "request_id": "req_550e8400-e29b-41d4-a716-446655440000"
}
```

### 2.3 请求头规范

```http
Content-Type: application/json
Accept: application/json
X-Session-ID: {session_id}
X-Request-ID: {request_id}
User-Agent: {client_info}
```

### 2.4 分页规范

```json
{
  "success": true,
  "data": {
    "items": [...],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total_items": 100,
      "total_pages": 5,
      "has_next": true,
      "has_prev": false
    }
  }
}
```

## 3. 会话管理API

### 3.1 创建会话

**接口信息**
- **URL**: `POST /api/v1/session/create`
- **描述**: 创建新的用户会话
- **认证**: 无需认证

**请求参数**
```json
{
  "client_info": {
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
    "screen_resolution": "1920x1080",
    "timezone": "Asia/Shanghai"
  }
}
```

**响应示例**
```json
{
  "success": true,
  "code": 201,
  "message": "会话创建成功",
  "data": {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "expires_at": "2024-01-15T14:30:45Z",
    "created_at": "2024-01-15T12:30:45Z"
  }
}
```

### 3.2 验证会话

**接口信息**
- **URL**: `GET /api/v1/session/validate`
- **描述**: 验证会话是否有效
- **认证**: 需要Session ID

**请求头**
```http
X-Session-ID: 550e8400-e29b-41d4-a716-446655440000
```

**响应示例**
```json
{
  "success": true,
  "code": 200,
  "message": "会话有效",
  "data": {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "is_valid": true,
    "expires_at": "2024-01-15T14:30:45Z",
    "last_accessed": "2024-01-15T12:30:45Z"
  }
}
```

### 3.3 刷新会话

**接口信息**
- **URL**: `PUT /api/v1/session/refresh`
- **描述**: 刷新会话过期时间
- **认证**: 需要Session ID

**响应示例**
```json
{
  "success": true,
  "code": 200,
  "message": "会话刷新成功",
  "data": {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "expires_at": "2024-01-15T16:30:45Z"
  }
}
```

### 3.4 销毁会话

**接口信息**
- **URL**: `DELETE /api/v1/session/destroy`
- **描述**: 销毁用户会话
- **认证**: 需要Session ID

**响应示例**
```json
{
  "success": true,
  "code": 200,
  "message": "会话销毁成功"
}
```

## 4. 文件管理API

### 4.1 上传文件

**接口信息**
- **URL**: `POST /api/v1/file/upload`
- **描述**: 上传Excel文件
- **认证**: 需要Session ID
- **Content-Type**: `multipart/form-data`

**请求参数**
```
file: [Excel文件]
file_type: "excel"
description: "投资数据文件"
```

**响应示例**
```json
{
  "success": true,
  "code": 201,
  "message": "文件上传成功",
  "data": {
    "file_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "original_name": "investment_data.xlsx",
    "file_size": 2048,
    "upload_time": "2024-01-15T12:30:45Z",
    "status": "uploaded",
    "download_url": "/api/v1/file/download/f47ac10b-58cc-4372-a567-0e02b2c3d479"
  }
}
```

### 4.2 解析文件

**接口信息**
- **URL**: `POST /api/v1/file/parse`
- **描述**: 解析上传的Excel文件
- **认证**: 需要Session ID

**请求参数**
```json
{
  "file_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "parse_options": {
    "sheet_name": "投资数据",
    "header_row": 1,
    "data_start_row": 2
  }
}
```

**响应示例**
```json
{
  "success": true,
  "code": 200,
  "message": "文件解析成功",
  "data": {
    "file_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "parsed_data": {
      "basic_params": {
        "investment_target": "某地产项目",
        "investment_amount": 10000.0,
        "investment_period": 5,
        "hurdle_rate": 8.0,
        "carry_rate": 20.0
      },
      "cash_flows": [
        {"year": 1, "amount": 1000.0},
        {"year": 2, "amount": 2000.0},
        {"year": 3, "amount": 3000.0},
        {"year": 4, "amount": 4000.0},
        {"year": 5, "amount": 5000.0}
      ]
    },
    "parsing_errors": [],
    "parsed_at": "2024-01-15T12:31:00Z"
  }
}
```

### 4.3 下载文件

**接口信息**
- **URL**: `GET /api/v1/file/download/{file_id}`
- **描述**: 下载文件
- **认证**: 需要Session ID

**响应**: 文件流

### 4.4 删除文件

**接口信息**
- **URL**: `DELETE /api/v1/file/{file_id}`
- **描述**: 删除文件
- **认证**: 需要Session ID

**响应示例**
```json
{
  "success": true,
  "code": 200,
  "message": "文件删除成功"
}
```

## 5. 计算引擎API

### 5.1 设置计算参数

**接口信息**
- **URL**: `POST /api/v1/calculation/params`
- **描述**: 设置计算参数
- **认证**: 需要Session ID

**请求参数**
```json
{
  "basic_params": {
    "investment_target": "某地产项目",
    "investment_amount": 10000.0,
    "investment_period": 5,
    "hurdle_rate": 8.0,
    "carry_rate": 20.0
  },
  "cash_flows": [
    {"year": 1, "amount": 1000.0, "description": "第一年回款"},
    {"year": 2, "amount": 2000.0, "description": "第二年回款"},
    {"year": 3, "amount": 3000.0, "description": "第三年回款"},
    {"year": 4, "amount": 4000.0, "description": "第四年回款"},
    {"year": 5, "amount": 5000.0, "description": "第五年回款"}
  ],
  "distribution_params": {
    "mode": "flat_principal_first",
    "options": {
      "priority_return": true,
      "carry_calculation": "cumulative"
    }
  }
}
```

**响应示例**
```json
{
  "success": true,
  "code": 200,
  "message": "参数设置成功",
  "data": {
    "params_id": "params_550e8400-e29b-41d4-a716-446655440000",
    "validation_result": {
      "is_valid": true,
      "warnings": [],
      "errors": []
    },
    "created_at": "2024-01-15T12:30:45Z"
  }
}
```

### 5.2 执行计算

**接口信息**
- **URL**: `POST /api/v1/calculation/execute`
- **描述**: 执行收益分配计算
- **认证**: 需要Session ID

**请求参数**
```json
{
  "calculation_mode": "full",
  "output_options": {
    "include_details": true,
    "include_charts": true,
    "precision": 2
  }
}
```

**响应示例**
```json
{
  "success": true,
  "code": 200,
  "message": "计算完成",
  "data": {
    "calculation_id": "calc_550e8400-e29b-41d4-a716-446655440000",
    "results": {
      "summary": {
        "irr": 15.24,
        "dpi": 1.50,
        "total_distributions": 15000.0,
        "total_carry": 1200.0,
        "calculation_time": 0.125
      },
      "cash_flow_details": [
        {
          "year": 1,
          "net_cash_flow": 1000.0,
          "principal_repayment": 1000.0,
          "remaining_principal": 9000.0,
          "hurdle_accrual": 800.0,
          "hurdle_distribution": 0.0,
          "carry_lp": 0.0,
          "carry_gp": 0.0
        },
        {
          "year": 2,
          "net_cash_flow": 2000.0,
          "principal_repayment": 2000.0,
          "remaining_principal": 7000.0,
          "hurdle_accrual": 1520.0,
          "hurdle_distribution": 0.0,
          "carry_lp": 0.0,
          "carry_gp": 0.0
        }
      ],
      "charts_data": {
        "cash_flow_chart": {
          "type": "bar",
          "data": [...],
          "options": {...}
        },
        "irr_chart": {
          "type": "line",
          "data": [...],
          "options": {...}
        }
      }
    },
    "calculated_at": "2024-01-15T12:31:15Z"
  }
}
```

### 5.3 获取计算结果

**接口信息**
- **URL**: `GET /api/v1/calculation/results`
- **描述**: 获取最新的计算结果
- **认证**: 需要Session ID

**查询参数**
```
format: json|summary
include_details: true|false
```

**响应示例**
```json
{
  "success": true,
  "code": 200,
  "message": "获取结果成功",
  "data": {
    "calculation_id": "calc_550e8400-e29b-41d4-a716-446655440000",
    "results": {
      // 计算结果数据
    },
    "calculated_at": "2024-01-15T12:31:15Z",
    "cache_hit": true
  }
}
```

### 5.4 验证参数

**接口信息**
- **URL**: `POST /api/v1/calculation/validate`
- **描述**: 验证计算参数的有效性
- **认证**: 需要Session ID

**请求参数**
```json
{
  "basic_params": {
    "investment_amount": 10000.0,
    "investment_period": 5,
    "hurdle_rate": 8.0,
    "carry_rate": 20.0
  },
  "cash_flows": [
    {"year": 1, "amount": 1000.0},
    {"year": 2, "amount": 2000.0}
  ]
}
```

**响应示例**
```json
{
  "success": true,
  "code": 200,
  "message": "参数验证完成",
  "data": {
    "is_valid": false,
    "errors": [
      {
        "field": "cash_flows",
        "message": "现金流期数与投资期限不匹配",
        "code": "PERIOD_MISMATCH"
      }
    ],
    "warnings": [
      {
        "field": "hurdle_rate",
        "message": "门槛收益率较低，建议检查",
        "code": "LOW_HURDLE_RATE"
      }
    ],
    "suggestions": [
      {
        "field": "carry_rate",
        "message": "建议Carry比例在15%-25%之间",
        "code": "CARRY_RATE_SUGGESTION"
      }
    ]
  }
}
```

## 6. 导出功能API

### 6.1 导出Excel

**接口信息**
- **URL**: `POST /api/v1/export/excel`
- **描述**: 导出计算结果为Excel文件
- **认证**: 需要Session ID

**请求参数**
```json
{
  "export_options": {
    "include_summary": true,
    "include_details": true,
    "include_charts": true,
    "template": "standard",
    "filename": "收益分配测算结果"
  }
}
```

**响应示例**
```json
{
  "success": true,
  "code": 200,
  "message": "Excel导出成功",
  "data": {
    "export_id": "export_550e8400-e29b-41d4-a716-446655440000",
    "filename": "收益分配测算结果_20240115_123045.xlsx",
    "file_size": 15360,
    "download_url": "/api/v1/export/download/export_550e8400-e29b-41d4-a716-446655440000",
    "expires_at": "2024-01-15T13:30:45Z",
    "created_at": "2024-01-15T12:30:45Z"
  }
}
```

### 6.2 导出PDF

**接口信息**
- **URL**: `POST /api/v1/export/pdf`
- **描述**: 导出计算结果为PDF文件
- **认证**: 需要Session ID

**请求参数**
```json
{
  "export_options": {
    "template": "report",
    "include_charts": true,
    "page_orientation": "portrait",
    "filename": "收益分配测算报告"
  }
}
```

**响应示例**
```json
{
  "success": true,
  "code": 200,
  "message": "PDF导出成功",
  "data": {
    "export_id": "export_550e8400-e29b-41d4-a716-446655440001",
    "filename": "收益分配测算报告_20240115_123045.pdf",
    "file_size": 25600,
    "download_url": "/api/v1/export/download/export_550e8400-e29b-41d4-a716-446655440001",
    "expires_at": "2024-01-15T13:30:45Z",
    "created_at": "2024-01-15T12:30:45Z"
  }
}
```

### 6.3 下载导出文件

**接口信息**
- **URL**: `GET /api/v1/export/download/{export_id}`
- **描述**: 下载导出的文件
- **认证**: 需要Session ID

**响应**: 文件流

### 6.4 获取导出历史

**接口信息**
- **URL**: `GET /api/v1/export/history`
- **描述**: 获取导出文件历史记录
- **认证**: 需要Session ID

**查询参数**
```
page: 1
page_size: 20
file_type: excel|pdf|all
```

**响应示例**
```json
{
  "success": true,
  "code": 200,
  "message": "获取导出历史成功",
  "data": {
    "items": [
      {
        "export_id": "export_550e8400-e29b-41d4-a716-446655440000",
        "filename": "收益分配测算结果_20240115_123045.xlsx",
        "file_type": "excel",
        "file_size": 15360,
        "status": "completed",
        "download_url": "/api/v1/export/download/export_550e8400-e29b-41d4-a716-446655440000",
        "created_at": "2024-01-15T12:30:45Z",
        "expires_at": "2024-01-15T13:30:45Z"
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total_items": 5,
      "total_pages": 1,
      "has_next": false,
      "has_prev": false
    }
  }
}
```

## 7. 系统管理API

### 7.1 健康检查

**接口信息**
- **URL**: `GET /api/v1/system/health`
- **描述**: 系统健康状态检查
- **认证**: 无需认证

**响应示例**
```json
{
  "success": true,
  "code": 200,
  "message": "系统运行正常",
  "data": {
    "status": "healthy",
    "version": "1.0.0",
    "uptime": 86400,
    "services": {
      "redis": {
        "status": "healthy",
        "response_time": 2
      },
      "calculation_engine": {
        "status": "healthy",
        "response_time": 15
      },
      "file_storage": {
        "status": "healthy",
        "available_space": "85%"
      }
    },
    "timestamp": "2024-01-15T12:30:45Z"
  }
}
```

### 7.2 系统信息

**接口信息**
- **URL**: `GET /api/v1/system/info`
- **描述**: 获取系统信息
- **认证**: 无需认证

**响应示例**
```json
{
  "success": true,
  "code": 200,
  "message": "获取系统信息成功",
  "data": {
    "application": {
      "name": "收益分配测算系统",
      "version": "1.0.0",
      "build_time": "2024-01-15T10:00:00Z",
      "environment": "production"
    },
    "capabilities": {
      "supported_file_types": ["xlsx", "xls"],
      "max_file_size": 10485760,
      "max_investment_period": 30,
      "calculation_modes": ["flat_principal_first", "flat_periodic", "structured"]
    },
    "limits": {
      "session_timeout": 7200,
      "max_concurrent_calculations": 10,
      "rate_limit": {
        "requests_per_minute": 60,
        "requests_per_hour": 1000
      }
    }
  }
}
```

### 7.3 系统统计

**接口信息**
- **URL**: `GET /api/v1/system/stats`
- **描述**: 获取系统使用统计
- **认证**: 管理员权限

**响应示例**
```json
{
  "success": true,
  "code": 200,
  "message": "获取系统统计成功",
  "data": {
    "sessions": {
      "active_count": 25,
      "total_created_today": 150,
      "average_duration": 1800
    },
    "calculations": {
      "total_today": 89,
      "average_time": 0.125,
      "success_rate": 0.98
    },
    "files": {
      "uploaded_today": 45,
      "total_size": 52428800,
      "average_size": 1165084
    },
    "exports": {
      "excel_count": 32,
      "pdf_count": 18,
      "total_size": 15728640
    },
    "performance": {
      "average_response_time": 150,
      "cache_hit_rate": 0.85,
      "error_rate": 0.02
    }
  }
}
```

## 8. 错误处理

### 8.1 错误代码定义

| 错误代码 | 错误类型 | 描述 |
|----------|----------|------|
| E001 | ValidationError | 参数验证失败 |
| E002 | AuthenticationError | 认证失败 |
| E003 | AuthorizationError | 权限不足 |
| E004 | ResourceNotFound | 资源不存在 |
| E005 | FileUploadError | 文件上传失败 |
| E006 | FileParseError | 文件解析失败 |
| E007 | CalculationError | 计算执行失败 |
| E008 | ExportError | 导出失败 |
| E009 | SessionExpired | 会话过期 |
| E010 | RateLimitExceeded | 请求频率超限 |
| E011 | ServiceUnavailable | 服务不可用 |
| E012 | InternalError | 内部服务器错误 |

### 8.2 详细错误信息

#### 参数验证错误
```json
{
  "success": false,
  "code": 422,
  "message": "参数验证失败",
  "error": {
    "type": "ValidationError",
    "code": "E001",
    "details": [
      {
        "field": "investment_amount",
        "message": "投资金额必须大于0",
        "code": "INVALID_VALUE",
        "received_value": -1000
      },
      {
        "field": "cash_flows",
        "message": "现金流数据不能为空",
        "code": "REQUIRED_FIELD"
      }
    ]
  }
}
```

#### 会话过期错误
```json
{
  "success": false,
  "code": 401,
  "message": "会话已过期",
  "error": {
    "type": "SessionExpired",
    "code": "E009",
    "details": {
      "session_id": "550e8400-e29b-41d4-a716-446655440000",
      "expired_at": "2024-01-15T14:30:45Z",
      "action_required": "请重新创建会话"
    }
  }
}
```

#### 计算错误
```json
{
  "success": false,
  "code": 500,
  "message": "计算执行失败",
  "error": {
    "type": "CalculationError",
    "code": "E007",
    "details": {
      "error_message": "现金流数据异常，无法计算IRR",
      "error_location": "irr_calculation",
      "suggested_action": "请检查现金流数据的正负号和数值"
    }
  }
}
```

## 9. API安全

### 9.1 请求验证

#### 会话验证
```python
# 会话验证中间件
async def session_validation_middleware(request: Request, call_next):
    session_id = request.headers.get("X-Session-ID")
    
    if not session_id:
        return JSONResponse(
            status_code=401,
            content={
                "success": False,
                "code": 401,
                "message": "缺少会话ID",
                "error": {
                    "type": "AuthenticationError",
                    "code": "E002"
                }
            }
        )
    
    # 验证会话有效性
    session = await session_service.validate_session(session_id)
    if not session:
        return JSONResponse(
            status_code=401,
            content={
                "success": False,
                "code": 401,
                "message": "会话无效或已过期",
                "error": {
                    "type": "SessionExpired",
                    "code": "E009"
                }
            }
        )
    
    # 更新会话访问时间
    await session_service.update_last_accessed(session_id)
    
    response = await call_next(request)
    return response
```

#### 输入验证
```python
# 输入验证装饰器
def validate_input(schema: BaseModel):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                # 验证输入数据
                validated_data = schema(**kwargs.get('data', {}))
                kwargs['validated_data'] = validated_data
                return await func(*args, **kwargs)
            except ValidationError as e:
                return JSONResponse(
                    status_code=422,
                    content={
                        "success": False,
                        "code": 422,
                        "message": "参数验证失败",
                        "error": {
                            "type": "ValidationError",
                            "code": "E001",
                            "details": e.errors()
                        }
                    }
                )
        return wrapper
    return decorator
```

### 9.2 限流控制

```python
# 限流中间件
class RateLimitMiddleware:
    def __init__(self, redis_client, requests_per_minute: int = 60):
        self.redis = redis_client
        self.requests_per_minute = requests_per_minute
    
    async def __call__(self, request: Request, call_next):
        client_ip = request.client.host
        session_id = request.headers.get("X-Session-ID")
        
        # 使用IP和会话ID作为限流键
        rate_limit_key = f"rate_limit:{client_ip}:{session_id}"
        
        # 检查当前请求数
        current_requests = await self.redis.get(rate_limit_key)
        
        if current_requests and int(current_requests) >= self.requests_per_minute:
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "code": 429,
                    "message": "请求频率超限",
                    "error": {
                        "type": "RateLimitExceeded",
                        "code": "E010",
                        "details": {
                            "limit": self.requests_per_minute,
                            "window": "1分钟",
                            "retry_after": 60
                        }
                    }
                }
            )
        
        # 增加请求计数
        await self.redis.incr(rate_limit_key)
        await self.redis.expire(rate_limit_key, 60)
        
        response = await call_next(request)
        return response
```

### 9.3 数据安全

```python
# 敏感数据处理
class DataSanitizer:
    @staticmethod
    def sanitize_input(data: dict) -> dict:
        """清理输入数据"""
        sanitized = {}
        for key, value in data.items():
            if isinstance(value, str):
                # 移除潜在的恶意字符
                value = re.sub(r'[<>"\'\/]', '', value)
                # 限制字符串长度
                value = value[:1000]
            elif isinstance(value, (int, float)):
                # 数值范围检查
                if key in ['investment_amount', 'cash_flow_amount']:
                    value = max(0, min(value, 1e12))  # 限制在合理范围内
            sanitized[key] = value
        return sanitized
    
    @staticmethod
    def sanitize_output(data: dict) -> dict:
        """清理输出数据"""
        # 移除敏感信息
        sensitive_fields = ['client_ip', 'user_agent', 'internal_id']
        return {k: v for k, v in data.items() if k not in sensitive_fields}
```

## 10. API测试

### 10.1 单元测试示例

```python
import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

class TestSessionAPI:
    def test_create_session(self):
        """测试创建会话"""
        response = client.post("/api/v1/session/create", json={
            "client_info": {
                "user_agent": "test-agent",
                "screen_resolution": "1920x1080"
            }
        })
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "session_id" in data["data"]
        assert "expires_at" in data["data"]
    
    def test_validate_session(self):
        """测试验证会话"""
        # 先创建会话
        create_response = client.post("/api/v1/session/create")
        session_id = create_response.json()["data"]["session_id"]
        
        # 验证会话
        response = client.get(
            "/api/v1/session/validate",
            headers={"X-Session-ID": session_id}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["is_valid"] is True

class TestCalculationAPI:
    def test_set_calculation_params(self):
        """测试设置计算参数"""
        # 创建会话
        session_response = client.post("/api/v1/session/create")
        session_id = session_response.json()["data"]["session_id"]
        
        # 设置参数
        params = {
            "basic_params": {
                "investment_amount": 10000.0,
                "investment_period": 5,
                "hurdle_rate": 8.0,
                "carry_rate": 20.0
            },
            "cash_flows": [
                {"year": 1, "amount": 1000.0},
                {"year": 2, "amount": 2000.0}
            ]
        }
        
        response = client.post(
            "/api/v1/calculation/params",
            json=params,
            headers={"X-Session-ID": session_id}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_execute_calculation(self):
        """测试执行计算"""
        # 创建会话并设置参数
        session_response = client.post("/api/v1/session/create")
        session_id = session_response.json()["data"]["session_id"]
        
        # 设置完整的计算参数
        params = {
            "basic_params": {
                "investment_amount": 10000.0,
                "investment_period": 5,
                "hurdle_rate": 8.0,
                "carry_rate": 20.0
            },
            "cash_flows": [
                {"year": 1, "amount": 1000.0},
                {"year": 2, "amount": 2000.0},
                {"year": 3, "amount": 3000.0},
                {"year": 4, "amount": 4000.0},
                {"year": 5, "amount": 5000.0}
            ]
        }
        
        client.post(
            "/api/v1/calculation/params",
            json=params,
            headers={"X-Session-ID": session_id}
        )
        
        # 执行计算
        response = client.post(
            "/api/v1/calculation/execute",
            json={"calculation_mode": "full"},
            headers={"X-Session-ID": session_id}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "results" in data["data"]
        assert "irr" in data["data"]["results"]["summary"]
```

### 10.2 集成测试

```python
class TestAPIIntegration:
    def test_complete_workflow(self):
        """测试完整的工作流程"""
        # 1. 创建会话
        session_response = client.post("/api/v1/session/create")
        session_id = session_response.json()["data"]["session_id"]
        headers = {"X-Session-ID": session_id}
        
        # 2. 上传文件
        with open("test_data.xlsx", "rb") as f:
            files = {"file": ("test_data.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
            upload_response = client.post(
                "/api/v1/file/upload",
                files=files,
                headers=headers
            )
        
        assert upload_response.status_code == 201
        file_id = upload_response.json()["data"]["file_id"]
        
        # 3. 解析文件
        parse_response = client.post(
            "/api/v1/file/parse",
            json={"file_id": file_id},
            headers=headers
        )
        
        assert parse_response.status_code == 200
        
        # 4. 执行计算
        calc_response = client.post(
            "/api/v1/calculation/execute",
            json={"calculation_mode": "full"},
            headers=headers
        )
        
        assert calc_response.status_code == 200
        
        # 5. 导出结果
        export_response = client.post(
            "/api/v1/export/excel",
            json={"export_options": {"include_summary": True}},
            headers=headers
        )
        
        assert export_response.status_code == 200
        export_id = export_response.json()["data"]["export_id"]
        
        # 6. 下载文件
        download_response = client.get(
            f"/api/v1/export/download/{export_id}",
            headers=headers
        )
        
        assert download_response.status_code == 200
        assert download_response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
```

这个API接口设计文档详细定义了系统的所有API接口，包括请求格式、响应格式、错误处理、安全机制和测试方案，为前后端开发提供了完整的接口规范。