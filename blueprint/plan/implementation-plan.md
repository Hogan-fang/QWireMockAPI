# QwireMockAPI Plan Copy

> **备注：文档定位**
> 本文件是 `../implementation-plan.md` 的执行视图版本，保留 Markdown 格式，便于在 `plan/` 目录下直接查看与推进。
>
> **备注：来源说明**
> - **来源：需求**：直接来自用户目标、功能要求和补充规则
> - **来源：schema**：直接来自 `../schema/*.yaml`
> - **来源：工程化补充**：为便于实现、测试、运行和维护而增加的设计约束

## 1. 计划目标

- 用 Markdown 形式维护 QwireMockAPI 的主计划与阶段路线图。
- 作为后续 `schema`、`spec`、代码实现与测试样例生成的总入口。
- 服务范围固定为 `order_server` 与 `callback_server`。

> 备注：来源：需求

## 2. 核心需求摘录

### `order_server`
- 创建订单：`POST /order`
- 查询订单：`GET /order?reference={uuid}`
- `4` 开头卡号返回 `400`
- `5` 开头卡号返回 `400`，并携带 `failReason=Insufficient balance`
- 成功状态：`SUCCESS / PROCESSING`
- `30s -> SHIPPED`，`60s -> DELIVERED`，最终 `COMPLETED`
- 关键状态变化触发 `ORDER_*` 回调
- 订单与商品数据写入 DB，卡号需掩码，不返回 `cvv/expiry`

> 备注：业务规则来源：需求；接口路径来源：schema

### `callback_server`
- `POST /callback`：校验成功后写入内存并返回 `200`，否则 `400`
- `GET /check`：UUID 错误返回 `422`，存在返回 `200`，不存在返回 `404`
- callback 数据仅保存在内存和日志中
- 数据结构必须符合 `OrderResponse`

> 备注：来源：需求

## 3. 生成顺序

1. 固化 `schema` 基线
2. 细化 `spec` 文档
3. 生成 Python 工程骨架
4. 生成测试样例和测试报告模板

> 备注：第 1 步来源：schema；第 2～4 步为需求落实与工程化补充

## 4. 关联文档

- 总纲：`../implementation-plan.md`
- 路线图：`./blueprint-roadmap.md`
- Order 规格：`../spec/order-service.spec.yaml`
- Callback 规格：`../spec/callback-service.spec.yaml`
- Shared 规格：`../spec/shared-contracts.spec.yaml`

> 备注：本节为工程化补充，用于便于检索与执行

