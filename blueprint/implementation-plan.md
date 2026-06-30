# QWireMockAPI Implementation Plan

## 1. 文档定位与模式

- 当前为需求模式文档，用于将 requirement 转化为可执行实现计划，并做 schema 一致性检查。
- 本文不涉及生产代码与测试代码修改，仅约束后续 spec、实现和验证路径。

## 2. 输入基线

- Requirement 基线：`blueprint/requirement/requirement.md`
- Guideline 基线：
	- `QWireGuideline/guideline/project-guideline.md`
	- `QWireGuideline/guideline/methodology.md`
	- `QWireGuideline/guideline/AI-guideline.md`
- Schema 基线：
	- `blueprint/schema/order_service.yaml`
	- `blueprint/schema/callback_service.yaml`

## 3. 目标与范围

### 3.1 目标
- 建立可追溯的实现计划，覆盖 Order Server 与 Callback Server。
- 明确接口行为、数据安全要求、状态流转与回调规则。
- 在实现前完成 schema 满足度检查并记录差距。

### 3.2 范围内
- Order 创建与查询能力。
- 卡号规则导致的业务失败分支。
- 订单状态推进（PROCESSING -> SHIPPED -> DELIVERED -> COMPLETED）。
- 状态变化触发回调。
- Callback 接收与查询能力。
- 数据安全与脱敏约束（卡号掩码、不返回 CVV/expiry）。

### 3.3 范围外
- 真实支付网关、鉴权、风控。
- 分布式与高可用架构。

## 4. 需求映射

### 4.1 Order 接口
- 输入：商户代码、订单参考号、金额币种、商品清单。
- 处理订单（成功或业务失败）都需持久化并返回主要请求信息 + 服务端订单号 + 处理结果。
- 同商户下 reference 唯一，不满足时拒绝处理。
- 无法处理的请求不落库，返回 HTTP 错误结构（code + detail）。

### 4.2 Query 接口
- 通过商户订单参考号查询。
- 业务规则：
	- 卡号 4 开头 -> 400，卡片无效。
	- 卡号 5 开头 -> 400，余额不足。
	- 成功：订单 SUCCESS、商品 PROCESSING。
	- 失败：订单 FAIL + failReason。
	- 成功时不返回空错误信息字段。
- 状态推进：30s -> SHIPPED，60s -> DELIVERED，全部 DELIVERED -> COMPLETED。
- 状态变化触发回调。
- DB 存储与对外返回均需掩码卡号，不得含 CVV/expiry。

### 4.3 Callback Server
- POST：校验通过写入内存并返回 200，否则 400。
- GET：UUID 错误 422，不存在 404，存在 200 且数据符合 OrderResponse。
- 仅内存存储 + 日志。

## 5. 技术约束（来自 Guideline）

- 接口字段命名使用 camelCase；状态枚举使用全大写。
- HTTP/框架错误统一返回结构：
	- `{ "code": "error_code", "detail": "error description" }`
- 业务失败优先用业务结构表达（status=FAIL + failReason），与 HTTP 错误结构严格区分。
- 所有接口数据必须符合 OpenAPI Schema。
- 时间字段使用 ISO 8601 + UTC。

## 6. 分阶段实施计划

### 阶段 A：契约固化
- 产出：order/callback schema 的修订版与差距关闭记录。
- 完成条件：关键差距项全部关闭，字段命名与错误结构与 guideline 一致。

### 阶段 B：行为规范（Spec）
- 产出：
	- `blueprint/spec/order-service.spec.yaml`
	- `blueprint/spec/callback-service.spec.yaml`
	- `blueprint/spec/shared-contracts.spec.yaml`
- 完成条件：状态机、回调时机、错误分层（业务失败 vs HTTP 错误）全部可验证。
- 状态：✓ 已完成

### 阶段 C：实现落地
- 产出：
	- order/callback 服务实现
	- 持久化模型与转换层（camelCase <-> snake_case）
- 完成条件：接口、落库、脱敏、回调逻辑全部按 spec 达成。
- 状态：✓ 已完成

### 阶段 D：验证与回归
- 产出：测试用例、样例数据、验证报告。
- 完成条件：
	- 关键路径与异常路径通过。
	- 回调与查询的 200/400/404/422 行为符合预期。
- 状态：✓ 已完成
- 验证摘要：
	- 修正 `test_v2_create_order_invalid_card_returns_400` 中过时的 `failReason="Unsupported card type"` → `"Card invalid"`（mock 与断言同步修正）。
	- 新增 `test_v2_check_invalid_uuid_returns_422`：GET /check 非法 UUID 返回 422 + HttpErrorResponse。
	- 新增 `test_v2_check_found_returns_200`：POST /callback 写入后 GET /check 返回 200 + OrderResponse。
	- 全部 16 项测试通过（order service 11 + callback service 5）。

## 7. Schema 满足度检查结果

结论：全部差距项已关闭，schema 契约已固化，可进入阶段 B（Spec 生成）。

### 7.1 已满足项
- 已定义 Order 的 POST/GET 与 Callback 的 POST/GET 基础接口。
- 已覆盖 Callback 查询状态码 422/404/200。
- 已定义统一 HTTP 错误结构（code + detail）。
- OrderResponse 与 Callback 的 OrderResponse 均未包含 CVV/expiry 字段。
- 状态枚举使用大写，字段命名符合 camelCase。

### 7.2 差距项（已全部关闭）

1. ~~掩码格式约束缺失~~ ✓ 已关闭
- 关闭方式：在 `order_service.yaml` 与 `callback_service.yaml` 的相关卡号字段统一加入掩码格式约束。

2. ~~failReason 约束不够严格~~ ✓ 已关闭
- 关闭方式：两个 schema 的 `OrderResponse` 均增加 `oneOf` 条件约束——`SUCCESS/COMPLETED` 时不允许出现 `failReason`；`FAIL` 时 `failReason` 必填且 `minLength: 1`。

3. ~~业务失败文案术语差异~~ ✓ 已关闭
- 关闭方式：统一为 `Card invalid` / `Insufficient balance`，与 requirement 语义对齐；具体触发条件从 schema 中移除，由 spec 约束。

4. ~~Mock 仿真逻辑混入接口定义~~ ✓ 已关闭
- 关闭方式：从接口、字段与 response 描述中清除所有 Mock 仿真规则（卡号前缀判定、状态推进时序、实现细节）；schema 仅保留纯契约语义，业务规则统一由 spec 定义。

## 8. 验收标准

- Plan、Spec、Schema 三者可追溯且无冲突。
- 所有接口响应在结构和状态码上满足 requirement + guideline。
- 成功响应不出现空错误字段；失败响应含 failReason；HTTP 错误使用 code/detail。
- 卡号在 DB（存储层）与对外（查询/回调/响应）均按要求掩码，且不包含 CVV/expiry。

## 9. 下一步执行建议

1. ~~完成 schema 修订并提交差距关闭记录。~~ ✓ 已完成
2. ~~基于固化后的 schema 生成 spec，落定状态机、卡号触发规则与回调触发点。~~ ✓ 已完成
3. ~~在开发模式下再进入代码实现与测试落地。~~ ✓ 已完成
4. ~~验证与回归：全部 spec validationChecklist 条目均有对应测试，16/16 通过。~~ ✓ 已完成

