# API 接口定义文档

## 1. 接口概述

### 1.1 基础信息
- **Base URL**: `http://localhost:8501/api/v1` (开发环境)
- **协议**: HTTP/1.1
- **数据格式**: JSON (Content-Type: application/json)
- **字符编码**: UTF-8

### 1.2 认证方式
- **Web UI**: 通过Streamlit Session State管理API Key
- **REST API**: Header中传递 `X-API-Key: {your_api_key}` (未来实现)

## 2. 接口列表

### 2.1 生成仓库模型

#### POST /api/v1/generate

**功能**: 基于图片生成仓库CAD模型

**请求头**:
```
Content-Type: application/json
X-API-Key: {optional_api_key}
```

**请求体**:
```json
{
  "input_type": "image_url | base64 | file_path",
  "image_data": "string",
  "user_prompt": "string (optional, max 500 chars)",
  "override_params": {
    "bay_width": 2500.0,
    "bay_depth": 1000.0,
    "levels": 4
  },
  "options": {
    "export_components": true,
    "export_assembly": true,
    "format": "step | stl | both"
  }
}
```

**请求示例**:
```json
{
  "input_type": "base64",
  "image_data": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
  "user_prompt": "Analyze this warehouse structure and extract all dimensions.",
  "override_params": {
    "levels": 5
  },
  "options": {
    "export_components": true,
    "export_assembly": true,
    "format": "step"
  }
}
```

**响应体** (同步模式):
```json
{
  "status": "success | error",
  "task_id": "uuid_string",
  "result": {
    "warehouse_id": "warehouse_20240101_123456",
    "files": {
      "assembly": "output/warehouse_20240101_123456/assembly/warehouse_assembly.step",
      "components": [
        "output/warehouse_20240101_123456/components/upright_001.step",
        "output/warehouse_20240101_123456/components/beam_001.step"
      ],
      "metadata": "output/warehouse_20240101_123456/metadata.json"
    },
    "download_urls": {
      "assembly": "http://localhost:8501/api/v1/download/warehouse_20240101_123456/assembly",
      "components_zip": "http://localhost:8501/api/v1/download/warehouse_20240101_123456/components.zip"
    },
    "config": {
      "warehouse_config": { ... },
      "racking_system": { ... }
    }
  },
  "elapsed_time": 28.5,
  "timestamp": "2024-01-01T12:34:56Z"
}
```

**响应体** (错误情况):
```json
{
  "status": "error",
  "error_code": "INVALID_IMAGE | AI_TIMEOUT | VALIDATION_ERROR | GENERATION_FAILED",
  "error_message": "Detailed error message",
  "timestamp": "2024-01-01T12:34:56Z"
}
```

**状态码**:
- `200 OK`: 成功生成
- `400 Bad Request`: 请求参数错误
- `422 Unprocessable Entity`: 参数验证失败
- `500 Internal Server Error`: 服务器错误
- `504 Gateway Timeout`: AI服务超时

---

### 2.2 查询任务状态

#### GET /api/v1/status/{task_id}

**功能**: 查询异步任务状态（未来实现）

**请求参数**:
- `task_id` (path): 任务ID

**响应体**:
```json
{
  "task_id": "uuid_string",
  "status": "pending | processing | completed | failed",
  "progress": 75,
  "result": {
    "files": { ... },
    "download_urls": { ... }
  },
  "error": null,
  "created_at": "2024-01-01T12:34:56Z",
  "updated_at": "2024-01-01T12:35:24Z"
}
```

---

### 2.3 下载模型文件

#### GET /api/v1/download/{warehouse_id}/{file_type}

**功能**: 下载生成的模型文件

**请求参数**:
- `warehouse_id` (path): 仓库ID
- `file_type` (path): `assembly | components | metadata | all`

**查询参数**:
- `token` (query, optional): 临时访问Token（未来实现）

**响应**:
- `200 OK`: 返回文件流
- `404 Not Found`: 文件不存在
- `403 Forbidden`: Token无效或过期

**响应头**:
```
Content-Type: application/octet-stream
Content-Disposition: attachment; filename="warehouse_assembly.step"
```

---

### 2.4 参数验证接口

#### POST /api/v1/validate

**功能**: 验证配置参数（不生成模型）

**请求体**:
```json
{
  "warehouse_config": { ... },
  "racking_system": { ... }
}
```

**响应体**:
```json
{
  "valid": true,
  "errors": [],
  "warnings": [
    "beam_spacing is larger than recommended (1500mm > 1200mm)"
  ],
  "suggestions": {
    "total_height": "Consider reducing to 4500mm for better stability"
  }
}
```

---

## 3. 数据模型Schema

### 3.1 完整配置Schema (JSON Schema)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["warehouse_config", "racking_system"],
  "properties": {
    "warehouse_config": {
      "type": "object",
      "required": ["overall_layout"],
      "properties": {
        "overall_layout": {
          "type": "object",
          "required": ["rows"],
          "properties": {
            "rows": {
              "type": "integer",
              "minimum": 1,
              "maximum": 20,
              "default": 1
            },
            "row_spacing": {
              "type": "number",
              "minimum": 1000,
              "maximum": 5000,
              "default": 1500
            },
            "orientation": {
              "type": "string",
              "enum": ["north-south", "east-west"],
              "default": "north-south"
            }
          }
        }
      }
    },
    "racking_system": {
      "type": "object",
      "required": ["dimensions", "structure", "components"],
      "properties": {
        "dimensions": {
          "type": "object",
          "required": ["bay_width", "bay_depth", "total_height"],
          "properties": {
            "bay_width": {
              "type": "number",
              "minimum": 1000,
              "maximum": 4000,
              "default": 2500
            },
            "bay_depth": {
              "type": "number",
              "minimum": 800,
              "maximum": 2000,
              "default": 1000
            },
            "total_height": {
              "type": "number",
              "minimum": 2000,
              "maximum": 10000,
              "default": 5000
            }
          }
        },
        "structure": {
          "type": "object",
          "required": ["levels"],
          "properties": {
            "levels": {
              "type": "integer",
              "minimum": 2,
              "maximum": 10,
              "default": 3
            },
            "first_beam_height": {
              "type": "number",
              "minimum": 100,
              "maximum": 500,
              "default": 200
            },
            "beam_spacing": {
              "type": "number",
              "minimum": 400,
              "maximum": 2000,
              "default": 1200
            }
          }
        },
        "components": {
          "type": "object",
          "properties": {
            "upright": {
              "type": "object",
              "properties": {
                "type": {
                  "type": "string",
                  "enum": ["L-beam", "C-channel", "square-tube"],
                  "default": "L-beam"
                },
                "section_size": {
                  "type": "string",
                  "pattern": "^\\d+x\\d+$",
                  "default": "80x60"
                },
                "color": {
                  "type": "string",
                  "default": "blue"
                }
              }
            },
            "beam": {
              "type": "object",
              "properties": {
                "type": {
                  "type": "string",
                  "enum": ["P-beam", "box-beam"],
                  "default": "P-beam"
                },
                "section_size": {
                  "type": "string",
                  "default": "50x100"
                },
                "color": {
                  "type": "string",
                  "default": "orange"
                },
                "connection_type": {
                  "type": "string",
                  "enum": ["welded", "bolted", "clip-on"],
                  "default": "clip-on"
                }
              }
            },
            "decking": {
              "type": "object",
              "properties": {
                "has_decking": {
                  "type": "boolean",
                  "default": false
                },
                "type": {
                  "type": "string",
                  "enum": ["wire-mesh", "solid-sheet", "bar-grating"],
                  "default": "wire-mesh"
                },
                "thickness": {
                  "type": "number",
                  "minimum": 10,
                  "maximum": 50,
                  "default": 20
                }
              }
            }
          }
        },
        "connection_details": {
          "type": "object",
          "properties": {
            "beam_to_upright": {
              "type": "object",
              "properties": {
                "method": {
                  "type": "string",
                  "enum": ["welded", "bolted", "clip"],
                  "default": "clip"
                },
                "bolt_count": {
                  "type": "integer",
                  "minimum": 0,
                  "maximum": 8,
                  "default": 4
                }
              }
            }
          }
        }
      }
    }
  }
}
```

### 3.2 Python数据类定义

```python
from dataclasses import dataclass
from typing import Optional, List, Dict

@dataclass
class OverallLayout:
    rows: int = 1
    row_spacing: float = 1500.0
    orientation: str = "north-south"

@dataclass
class Dimensions:
    bay_width: float = 2500.0
    bay_depth: float = 1000.0
    total_height: float = 5000.0

@dataclass
class Structure:
    levels: int = 3
    first_beam_height: float = 200.0
    beam_spacing: float = 1200.0

@dataclass
class UprightComponent:
    type: str = "L-beam"
    section_size: str = "80x60"
    color: str = "blue"
    material: str = "steel"

@dataclass
class BeamComponent:
    type: str = "P-beam"
    section_size: str = "50x100"
    color: str = "orange"
    connection_type: str = "clip-on"

@dataclass
class DeckingComponent:
    has_decking: bool = False
    type: str = "wire-mesh"
    thickness: float = 20.0

@dataclass
class Components:
    upright: Optional[UprightComponent] = None
    beam: Optional[BeamComponent] = None
    decking: Optional[DeckingComponent] = None

@dataclass
class WarehouseConfig:
    warehouse_config: Dict
    racking_system: Dict
```

## 4. 错误码定义

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| `INVALID_IMAGE` | 400 | 图片格式不支持或损坏 |
| `IMAGE_TOO_LARGE` | 400 | 图片大小超过10MB |
| `MISSING_PARAMS` | 400 | 缺少必需参数 |
| `AI_TIMEOUT` | 504 | AI服务调用超时 |
| `AI_ERROR` | 502 | AI服务返回错误 |
| `VALIDATION_ERROR` | 422 | 参数验证失败 |
| `GENERATION_FAILED` | 500 | 几何生成失败 |
| `FILE_WRITE_ERROR` | 500 | 文件写入失败 |
| `INTERNAL_ERROR` | 500 | 服务器内部错误 |

## 5. 调用示例

### 5.1 Python调用示例

```python
import requests
import base64

# 读取图片并编码
with open("warehouse_photo.jpg", "rb") as f:
    image_data = base64.b64encode(f.read()).decode('utf-8')

# 构建请求
url = "http://localhost:8501/api/v1/generate"
payload = {
    "input_type": "base64",
    "image_data": f"data:image/jpeg;base64,{image_data}",
    "user_prompt": "Extract warehouse structure parameters",
    "options": {
        "export_components": True,
        "export_assembly": True,
        "format": "step"
    }
}

# 发送请求
response = requests.post(url, json=payload, timeout=60)
result = response.json()

if result["status"] == "success":
    print(f"Model generated: {result['result']['warehouse_id']}")
    print(f"Download URL: {result['result']['download_urls']['assembly']}")
else:
    print(f"Error: {result['error_message']}")
```

### 5.2 cURL调用示例

```bash
curl -X POST http://localhost:8501/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "input_type": "image_url",
    "image_data": "https://example.com/warehouse.jpg",
    "user_prompt": "Analyze this warehouse",
    "options": {
      "export_components": true,
      "format": "step"
    }
  }'
```

### 5.3 JavaScript调用示例

```javascript
async function generateWarehouse(imageFile) {
  const base64 = await fileToBase64(imageFile);
  
  const response = await fetch('http://localhost:8501/api/v1/generate', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      input_type: 'base64',
      image_data: `data:image/jpeg;base64,${base64}`,
      user_prompt: 'Extract warehouse parameters',
      options: {
        export_components: true,
        format: 'step'
      }
    })
  });
  
  const result = await response.json();
  return result;
}
```

## 6. 限流策略（未来实现）

- **免费用户**: 10次/小时
- **付费用户**: 100次/小时
- **企业用户**: 无限制

响应头包含限流信息:
```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 9
X-RateLimit-Reset: 1640995200
```

