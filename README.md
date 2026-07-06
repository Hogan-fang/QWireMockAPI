# QWireMockAPI

一个功能完整、测试充分的订单支付与回调模拟系统，采用 FastAPI + MySQL 实现，遵循 OpenAPI 3.0 规范和 Requirement-Schema-Spec 三层工程方法论。

## 🎯 项目概述

QWireMockAPI 包含两个主要服务：

- **Order Server** (`order_service.py`) — 订单创建与查询服务，模拟支付处理、卡号规则验证、订单状态流转与回调。
- **Callback Server** (`callback_service.py`) — 商户回调接收服务，模拟接收订单状态通知并支持查询已接收的回调数据。

### 核心特性

✅ **完整的订单生命周期** — 从创建、业务验证、到状态推进（SUCCESS → SHIPPED → DELIVERED → COMPLETED）  
✅ **卡号规则验证** — 支持 4* 和 5* 卡号的业务失败场景（Card invalid / Insufficient balance）  
✅ **数据安全** — 卡号前 6 后 4 掩码、敏感字段脱敏、无 CVV/expiry 返回  
✅ **事件驱动回调** — 订单状态变化自动触发 ORDER_SUCCESS / ORDER_SHIPPED / ORDER_DELIVERED / ORDER_COMPLETED  
✅ **内存与日志存储** — Callback Server 采用内存 + 日志式存储，支持查询  
✅ **标准化错误处理** — 统一的 HTTP 错误结构（code + detail）与业务失败区分  
✅ **充分的测试覆盖** — 16 个单元/功能测试 + 集成测试，源码与测试代码量 1:1  

## 📋 快速开始

### 环境要求

- Python 3.10+
- MySQL 5.7+ 或 8.0+
- FastAPI, Pydantic v2

### 安装与运行

```bash
# 克隆或进入项目目录
cd /Users/hao/vs-workspace/QWireMockAPI

# 创建虚拟环境并激活
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置数据库（修改 config.yaml 或 config.properties）
# 默认：MySQL localhost:3306, database=qwire_test

# 初始化数据库
python -m qwire_mock.order_db  # 自动创建表

# 启动两个服务（两个终端）
# 终端 1 - Order Server (port 9100)
PYTHONPATH=src python -m qwire_mock.order_service

# 终端 2 - Callback Server (port 8100)
PYTHONPATH=src python -m qwire_mock.callback_service
```

### 测试

```bash
# 运行所有单元测试（非集成）
PYTHONPATH=src .venv/bin/python -m pytest tests/ -m "not integration" -v

# 运行集成测试
PYTHONPATH=src .venv/bin/python -m pytest tests/ -m "integration" -v

# 生成测试执行报告
pytest tests/ -m "v2_" --html=tests/reports/report.html
```

## 📁 项目结构

```
QWireMockAPI/
├── blueprint/                           # 设计文档
│   ├── requirement/
│   │   ├── requirement.md              # 业务需求（中文）
│   │   └── requirement.en.md           # 业务需求（英文）
│   ├── schema/
│   │   ├── order_service.yaml          # Order API 契约（中文）
│   │   ├── order_server.en.yaml        # Order API 契约（英文）
│   │   ├── callback_service.yaml       # Callback API 契约（中文）
│   │   └── callback_server.en.yaml     # Callback API 契约（英文）
│   ├── spec/
│   │   ├── order-service.spec.yaml     # Order 行为规范（中文）
│   │   ├── order-service.spec.en.yaml  # Order 行为规范（英文）
│   │   ├── callback-service.spec.yaml  # Callback 行为规范（中文）
│   │   ├── callback-service.spec.en.yaml # Callback 行为规范（英文）
│   │   ├── shared-contracts.spec.yaml  # 共享契约（中文）
│   │   └── shared-contracts.spec.en.yaml # 共享契约（英文）
│   ├── implementation-plan.md           # 实现计划（中文）
│   ├── implementation-plan.en.md        # 实现计划（英文）
│   ├── example/                         # 接口请求/响应示例
│   │   ├── order/                       # Order Server 示例
│   │   └── callback/                    # Callback Server 示例
│   └── README.md                        # 设计文档说明
├── src/qwire_mock/
│   ├── __main__.py                      # 启动入口
│   ├── config.py                        # 配置管理 (yaml / properties)
│   ├── schemas.py                       # Pydantic 数据模型（共享）
│   ├── order_service.py                 # Order Server (FastAPI)
│   ├── order_db.py                      # Order Server DB 层 (MySQL)
│   └── callback_service.py              # Callback Server (FastAPI)
├── tests/
│   ├── conftest.py                      # pytest 配置与报告生成
│   ├── test_order_service.py            # Order Server 单元测试 (11 个)
│   ├── test_callback_service.py         # Callback Server 单元测试 (5 个)
│   ├── test_execution_report.py         # 报告生成测试
│   ├── test_order_service_integration.py # 集成测试 (跳过)
│   └── reports/                         # 测试执行报告
├── config.yaml / config.properties      # 应用配置
├── requirements.txt                     # Python 依赖
├── pom.xml                              # Maven 配置 (历史)
└── README.md / README.en.md             # 项目文档 (本文)
```

## 🔌 API 文档

### Order Server (Port 9100)

#### POST /order — 创建订单

```bash
curl -X POST http://127.0.0.1:9100/order \
  -H "Content-Type: application/json" \
  -d '{
    "reference": "d290f1ee-6c54-4b01-90e6-d701748f0851",
    "name": "Widget Order",
    "mid": "M123456789",
    "callback": "http://localhost:8100/callback",
    "cardNumber": "6222222222222222",
    "cvv": "123",
    "expiry": "12/28",
    "amount": 99.99,
    "currency": "USD",
    "products": [{"productId": "P1", "count": 2, "spec": "M"}],
    "signature": "8f14e45fceea167a5a36dedd4bea2543"
  }'
```

**成功响应 (201)**
```json
{
  "reference": "d290f1ee-6c54-4b01-90e6-d701748f0851",
  "orderId": "PX39280930012",
  "name": "Widget Order",
  "status": "SUCCESS",
  "cardNumber": "622222******2222",
  "products": [...],
  "amount": 99.99,
  "currency": "USD",
  "orderDate": "2024-01-10T10:15:30Z"
}
```

**卡号规则 (400)**
- 4 开头 → failReason: "Card invalid"
- 5 开头 → failReason: "Insufficient balance"

#### GET /order — 查询订单

```bash
curl http://127.0.0.1:9100/order?reference=d290f1ee-6c54-4b01-90e6-d701748f0851
```

### Callback Server (Port 8100)

#### POST /callback — 接收回调

```bash
curl -X POST http://127.0.0.1:8100/callback \
  -H "Content-Type: application/json" \
  -d '{ "reference": "...", "status": "SUCCESS", ... }'
```

#### GET /callback/latest — 查询最近一次回调

```bash
curl http://127.0.0.1:8100/callback/latest?orderId=550e8400-e29b-41d4-a716-446655440000
```

完整 API 文档见 `blueprint/schema/order_service.yaml` 和 `blueprint/schema/callback_service.yaml` (OpenAPI 3.0 格式).

## 📊 代码统计

| 分类 | 文件数 | 代码行数 |
|------|--------|---------|
| **源码** | 7 | 894 |
| 　- schemas.py | 1 | 53 |
| 　- config.py | 1 | 104 |
| 　- order_service.py | 1 | 189 |
| 　- order_db.py | 1 | 382 |
| 　- callback_service.py | 1 | 108 |
| **测试** | 5 | 878 |
| 　- 功能测试 | 3 | 459 |
| 　- 集成测试 | 1 | 332 |
| **文档** | 14 | 1,172 |
| 　- Schema + Spec | 6 | 616 |
| 　- Requirement + Plan | 4 | 210 |
| **总计** | **26** | **2,944** |

## 🎓 工程方法论

本项目采用**Plan → Spec → Implementation → Verification** 的四层核心设计流程：

1. **Plan 层** (`blueprint/requirement/` + `blueprint/implementation-plan.md`) — 需求整理与设计规划
2. **Spec 层** (`blueprint/schema/` + `blueprint/spec/`) — 接口契约与行为规范
   - Schema 确保接口结构严格性
   - Spec 定义业务规则与行为
3. **Implementation 层** (`src/`) — 代码实现
4. **Verification 层** (`tests/`) — 单元 + 集成测试验证

所有设计文档同时提供**中文版**和**英文版** (`.en` 后缀)，便于团队协作。详见 [implementation-plan.md](blueprint/implementation-plan.md)。

## ✅ 测试覆盖

- **Order Service** — 11 个单元测试
  - POST /order 成功、冲突、卡号验证、UUID 验证
  - GET /order 成功、404、422、状态推进
- **Callback Service** — 5 个单元测试
  - POST /callback 成功、失败
  - GET /check 成功、404、422
- **集成测试** — 生命周期、回调流转（可选）

```bash
# 查看测试执行报告
pytest tests/ --co -q  # 列出所有测试
pytest tests/ -v       # 运行并显示详细结果
```

## 📝 配置

### config.yaml (推荐)

```yaml
database:
  host: localhost
  port: 3306
  user: root
  password: root
  db_name: qwire_test

server:
  order_port: 9100
  callback_port: 8100

logging:
  order_log: logs/order.log
  callback_log: logs/callback.log
```

### config.properties (备选)

```properties
db.host=localhost
db.port=3306
db.user=root
db.password=root
db.name=qwire_test
```

## 🔧 开发指南

### 本地开发流程

1. 编辑代码或测试
2. `pytest tests/ -m "not integration"` 运行单元测试
3. 修复失败的测试
4. 提交前运行完整测试

### 常见问题

**Q: 如何修改卡号规则？**  
A: 编辑 `src/qwire_mock/order_service.py` 中的 `_check_card_rules()` 函数，规则定义也见 `blueprint/spec/order-service.spec.yaml`。

**Q: 如何修改状态推进时间？**  
A: 编辑 `src/qwire_mock/order_service.py` 中的 `PROCESSING_TO_SHIPPED_DELAY` 和 `SHIPPED_TO_DELIVERED_DELAY` 常量。

**Q: 数据库连接失败？**  
A: 检查 `config.yaml` 或 `config.properties`，确保 MySQL 已启动且用户名密码正确。

## 📜 许可证

Apache License 2.0

## 📧 联系方式

QWire Project Team  
Email: you@your-company.com
# QWireMockAPI

一个功能完整、测试充分的订单支付与回调模拟系统，采用 FastAPI + MySQL 实现，遵循 OpenAPI 3.0 规范和 Requirement-Schema-Spec 三层工程方法论。

## 🎯 项目概述

QWireMockAPI 包含两个主要服务：

- Order API (`POST /order`, `GET /order`) with MySQL persistence
- Callback API (`POST /callback`, `GET /check`) for callback receiving and log-only check behavior

Current package version: `2.0.0`.

Core configuration is now centralized in `config.yaml`.

## Requirements

- Python 3.9+
- MySQL (default database: `qwire`)

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
pip install -r requirements.txt
```

## Run Services

Run both services (default):

```bash
python -m qwire_mock
```

Run one service only:

```bash
python -m qwire_mock --service callback
python -m qwire_mock --service order
```

Set host:

```bash
python -m qwire_mock --host 127.0.0.1 --service all
```

Default ports:

- Callback API: `8100`
- Order API: `9100`

## API Summary

### Order API (`:9100`)

- `POST /order`
  - Success: `201`, `status="SUCCESS"` (for supported card prefixes such as `6*`)
  - Unsupported card type (`cardNumber` starts with `4`): `400`, `status="FAIL"`, `failReason="Unsupported card type"`
  - Insufficient balance (`cardNumber` starts with `5`): `400`, `status="FAIL"`, `failReason="Insufficient balance"`
  - Duplicate reference: `409`, `{ "code": "order_conflict", "detail": "Order already exists" }`
  - Request validation failure: `422`, `{ "code": "invalid_request", "detail": "Request validation failed" }`
- `GET /order?reference=<uuid>`
  - Found: `200`
  - Invalid UUID: `422`, `{ "code": "invalid_reference", "detail": "invalid UUID string" }`
  - Not found: `404`, `{ "code": "order_not_found", "detail": "Order not found" }`

Order status lifecycle:

- Order: `SUCCESS -> COMPLETED` (or `FAIL` on create failure)
- Product: `PROCESSING -> SHIPPED -> DELIVERED`

Scheduler transition rules:

- after 30s: product `PROCESSING -> SHIPPED`
- after 60s: product `SHIPPED/PROCESSING -> DELIVERED`
- when all products are `DELIVERED`: order `SUCCESS -> COMPLETED`

Callback events sent by Order API:

- `ORDER_SUCCESS`
- `ORDER_SHIPPED`
- `ORDER_DELIVERED`
- `ORDER_COMPLETED`

If order `amount >= QWIRE_V2_CALLBACK_SKIP_AMOUNT_GTE` (default `1000`), callback dispatch is skipped.

### Callback API (`:8100`)

- `POST /callback`
  - Valid payload: `200`, body `{ "message": "OK" }`
  - Invalid payload: `400`, body `{ "code": "invalid_request", "detail": "Invalid order payload" }`
- `GET /check?reference=<uuid>`
  - Missing record: `404`, body `{ "code": "resource_not_found", "detail": "Callback records are log-only and not queryable" }`

## Naming Conventions

- API request/response fields and code variables use `camelCase`
- Database table/column names use `snake_case`
- Cross-layer mapping must be explicit in data access code (for example: `failReason` <-> `fail_reason`)

## Logging

Service logs are written to project root:

- `order.log`
- `callback.log`

Logged events include:

- service startup/shutdown
- request payloads
- response payloads
- callback dispatch and callback response details

JSON bodies are pretty-printed in logs.

Optional log path environment variables:

- `QWIRE_V2_ORDER_LOG` (default `order.log`)
- `QWIRE_V2_CALLBACK_LOG` (default `callback.log`)

## Configuration

### Configuration File (`config.yaml`)

The project root `config.yaml` is the primary configuration source for:

- server host and ports
- MySQL connection
- order scheduler and callback threshold
- log format and log file paths

Example:

```yaml
order:
  poll_interval_seconds: 5
  callback_skip_amount_gte: 1000
  process_historical_on_startup: false
```

Use a custom file path with:

- `QWIRE_CONFIG_FILE=/path/to/your-config.yaml`

### Environment Variable Overrides

Environment variables are still supported as overrides for compatibility:

MySQL:

- `QWIRE_MYSQL_HOST` (default `localhost`)
- `QWIRE_MYSQL_PORT` (default `3306`)
- `QWIRE_MYSQL_USER` (default `qwire`)
- `QWIRE_MYSQL_PASSWORD` (default `Qwire2026`)
- `QWIRE_MYSQL_DATABASE` (default `qwire`)

Order scheduler and callback policy:

- `QWIRE_V2_POLL_INTERVAL_SECONDS` (default `5`)
- `QWIRE_V2_CALLBACK_SKIP_AMOUNT_GTE` (default `1000`)
- `QWIRE_V2_PROCESS_HISTORICAL_ON_STARTUP` (default `false`; when false, scheduler only processes orders created after this process starts)

Tests:

- `QWIRE_V2_CLEAR_DB_BEFORE_TEST=1` to clear `orders` before each integration test (default is no clearing)

## Development

Run tests:

```bash
pytest
```

Run a specific group:

```bash
pytest -m v2_integration
```

## Project Structure

```text
QWireMock/
├── config.yaml
├── src/qwire_mock/
│   ├── __main__.py
│   ├── callback_service.py
│   ├── order_service.py
│   ├── order_db.py
│   └── schemas.py
├── tests/
├── blueprint/
│   ├── blueprint-guide.md
│   ├── schema/
│   ├── spec/
│   ├── example/
│   └── structure/
└── README.md
```
