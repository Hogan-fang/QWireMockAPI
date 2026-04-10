# QwireMockAPI Master Blueprint Plan

> **备注：文档定位**
> 本文作为后续 `schema`、`spec`、实现代码和测试样例生成的总纲文档，用于统一范围、接口行为、目录结构和交付顺序。
>
> **备注：来源说明**
> - **来源：需求**：直接来自用户目标、功能要求和补充规则
> - **来源：schema**：直接来自 `blueprint/schema/*.yaml`
> - **来源：工程化补充**：为便于实现、测试、运行和维护而增加的设计约束

## 1. 项目概述

- **项目名称**：`QwireMockAPI`
- **开发语言**：`Python`
- **项目目标**：构建一个最简化 API 服务，模拟线上购物订单支付、状态推进、回调通知和查询，用于在自动化测试框架完成后验证该框架对 API 测试能力的支撑效果。

> 备注：本节来源：需求

## 2. 服务范围

### 2.1 支持的服务端
- `order_server`
- `callback_server`

> 备注：来源：需求

### 2.2 范围内
- `order_server` 的订单创建与查询接口
- 支付结果判定、订单状态推进和 `ORDER_*` 回调
- `callback_server` 的回调接收与查询接口
- 基于 Python 的后续实现、测试样例和示例数据生成依据

> 备注：来源：需求

### 2.3 范围外
- 真实支付网关、鉴权、风控与外部三方集成
- 分布式部署、消息队列、缓存集群和高可用架构

> 备注：来源：工程化补充

## 3. 接口基线与核心规则

### 3.1 `order_server`
- `POST /order`：创建订单并触发支付判定
- `GET /order?reference={uuid}`：按 `reference` 查询订单

> 备注：接口路径来源：`schema/order_server.yaml`

#### 业务规则
1. 卡号 **4 开头** → 返回 `400`，业务失败原因为 `Unsupported card type`
2. 卡号 **5 开头** → 返回 `400`，业务失败原因为 `Insufficient balance`
3. 创建成功时，订单状态为 `SUCCESS`，商品状态为 `PROCESSING`
4. 失败场景统一返回 `FAIL`，并带 `failReason`
5. 订单创建后约 `30s`，商品状态推进为 `SHIPPED`
6. 订单创建后约 `60s`，商品状态推进为 `DELIVERED`
7. 全部商品均为 `DELIVERED` 后，订单状态推进为 `COMPLETED`
8. 订单创建成功及关键状态变化时都要触发 `ORDER_*` 回调

> 备注：业务规则来源：需求；响应结构基线来源：schema

### 3.2 `callback_server`
- `POST /callback`：校验回调请求，合法则写入内存并返回 `200`，否则返回 `400`
- `GET /check?reference={uuid}`：查询已缓存的 callback 数据

> 备注：接口路径来源：`schema/callback_server.yaml`；查询语义来源：需求

#### 业务规则
1. `reference` 非法 UUID 时返回 `422`
2. `reference` 存在时返回 `200 + OrderResponse`
3. `reference` 不存在时返回 `404`
4. callback 数据结构必须符合 `OrderResponse`
5. callback 数据仅使用**内存存储 + 日志输出**

> 备注：来源：需求

## 4. 数据与安全约束

- 订单主数据与商品明细必须做 **DB 持久化**
- callback 数据不做 DB 持久化，仅保存在**内存与日志**中
- `cardNumber` 必须掩码为**前 6 后 4**
- 任意响应与回调中不得暴露 `cvv` 与 `expiry`

> 备注：来源：需求；字段模型基线来源：schema

## 5. Blueprint 目录要求

- `schema/`：维护 `order_server.yaml` 和 `callback_server.yaml`
- `spec/`：维护 `order-server.spec.yaml`、`callback-server.spec.yaml`、`shared-contracts.spec.yaml`
- `examples/`：维护订单与回调样例
- `structure/`：维护 Python 目标目录结构设计
- `plan/`：维护阶段拆分、路线图和执行顺序

> 备注：`schema/` 来自契约定义，其余目录为支撑后续生成工作的工程化补充

## 6. 分阶段生成顺序

1. 固化 `schema` 契约基线
2. 细化 `spec` 行为规范
3. 生成 Python 目录结构与实现骨架
4. 生成测试样例、测试报告与示例数据

> 备注：第 1 步来源：schema；第 2～4 步为需求落实与工程化补充

## 7. 验收标准

- `order_server` 与 `callback_server` 的接口行为与本计划及 schema 保持一致
- 所有失败响应均返回 `FAIL + failReason`
- callback 查询满足 `422 / 200 / 404` 三种分支
- 文档能够直接支撑后续 schema、spec、实现代码和测试生成

> 备注：来源：需求

## 8. 同步提醒

- `POST /order` 的业务失败分支需覆盖两类 `400`：`Unsupported card type` 与 `Insufficient balance`
- callback 查询逻辑以本计划为准：存在返回 `200`，不存在返回 `404`

> 备注：来源：工程化补充

