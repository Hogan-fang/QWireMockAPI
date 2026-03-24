# Python Mock 服务建设计划

## 1. 目标与范围

### 1.1 目标
构建可独立运行的 API Mock 平台，支持：
1. 接收并处理模拟订单请求（创建、查询、状态推进）。
2. 以可根据服务规范发起异步回调，模拟真实发起方通知链路。
3. 提供稳定可复现的测试行为（可控延迟、失败注入、重试）。

### 1.2 范围内
- HTTP API（订单接口 + 回调接收接口）
- 订单状态机与持久层（MySQL 数据库存储）
- 回调信息记录（日志文件输出，不做数据库持久化）
- 回调调度器（重试、退避、超时）
- 统一配置、日志、错误码、健康检查
- 测试与契约校验骨架
- 所有请求和响应记录直观可读的日志

### 1.3 范围外（本阶段）
- 生产级认证授权（如 OAuth2）
- 分布式消息队列与多实例一致性
- 真正业务系统对接

## 2. 核心架构
- `order-service`：负责订单生命周期与查询。
- `callback-server`：接收回调并输出可读日志，不对回调内容做数据库存储。
- `shared`：共享模型、错误码、配置与工具。
- `scheduler`：异步回调任务编排。
- `tests`：单测、集成测试、契约测试。

### 2.1 接口契约基线（参考现有定义）
- 订单服务：`order_server.yaml`
	- `GET /order?reference={uuid}`
	- `POST /order`
- 回调服务：`callback_server.yaml`
	- `GET /check?reference={uuid}`
	- `POST /callback`
- 本计划及所有 spec 文档均以以上接口路径、字段及响应码为基线。

### 2.2 Blueprint 目录基线

当前 blueprint 至少应包含以下目录与文件：

- `schema/`
  - `order_server.yaml`
  - `callback_server.yaml`
- `spec/`
  - `order-service.spec.yaml`
  - `order-service.spec.en.yaml`
  - `callback-server.spec.yaml`
  - `callback-server.spec.en.yaml`
  - `shared-contracts.spec.yaml`
  - `shared-contracts.spec.en.yaml`
- `examples/`
  - `order/`
  - `callback/`
- `structure/`
  - `target-directory-structure.md`
  - `target-directory-structure.en.md`
- 根目录文档
  - `blueprint-guide.md`
  - `PLAN.en.md`
  - `README.md`

说明：

- `schema/` 负责接口契约基线
- `spec/` 负责行为、时序与模块职责约束
- `examples/` 负责样例 request / response
- `structure/` 负责目标工程目录规划
- 根目录文档负责总纲、计划与索引

## 3. 关键能力清单
1. **订单管理**：创建订单、查询订单（状态由订单系统处理并通过回调体现）。
2. **回调仿真**：按照规则发送回调，支持重试与死信记录。
3. **故障注入**：配置化模拟 4xx/5xx。
4. **可观测性**：结构化日志、请求追踪 ID、指标埋点占位。
5. **可测试性**：固定随机种子、时间控制、场景脚本化。

## 4. 分阶段实施

### Phase 0：工程骨架
- 建立目录结构、依赖管理、配置样板。
- 定义共享数据模型与错误码。

### Phase 1：订单服务 MVP
- 完成订单创建/查询 API。
- 实现订单状态机和基础校验。

### Phase 2：回调链路 MVP
- 实现回调接收端与发送端。
- 完成重试策略（指数退避）与超时机制。

### Phase 3：稳定性与测试
- 完成单测、集成测试与契约测试样例。

### Phase 4：运行与交付
- 完善健康检查与运行脚本。
- 输出使用手册与示例场景。

## 5. 关键约束

- 接口契约以 `schema/order_server.yaml` 和 `schema/callback_server.yaml` 为准
- 行为规则以 `spec/` 下文档为准
- 所有返回状态统一使用大写字符串
- 订单主数据和订单商品数据必须持久化到数据库
- 回调记录默认写入日志，不提供数据库查询能力
- 响应中的 `cardNumber` 必须为前6后4掩码格式
- 响应与回调中不得暴露 `cvv` 和 `expiry`

## 6. 交付物

- `schema/` 下接口契约文件
- `spec/` 下服务行为与共享约束文件
- `examples/` 下 request / response 样例
- `structure/` 下目录结构设计文档
- 可运行的 Python Mock 服务代码
- 单测、集成测试、契约测试与测试报告

## 7. 验收标准（DoD）
- 所有公开 API 有明确请求/响应契约。
- 订单状态转换规则有自动化测试覆盖。
- 回调重试与失败路径可配置并可验证。
- 日志可关联一次订单全链路。
- 文档可支撑新成员在 30 分钟内本地启动。
- 编写全面的测试用例，并在测试完成后能输出一个具体测试执行内容的报告，说明每一步执行了什么，涉及到的订单关键字信息
- 回调请求与响应可在日志文件中检索与审计。

## 8. 数据库连接信息
- host: localhost
- port: 3306
- user: qwire
- password: Qwire2026
- database: qwire

## 9. 文档规范
- 除 `blueprint-guide.md` 和 `spec/` 下中英双语 spec 外，其他文档都用英文
