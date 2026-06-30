# QWireMockAPI Requirement

本章将以一个订单支付系统为业务场景，结合 QWireCore 提供的自动化测试能力，构建一套完整的订单支付自动化测试系统，以验证自动化测试框架在真实业务场景下的可用性、稳定性以及扩展能力。

在支付业务中，系统通常需要与第三方支付平台进行交互，包括发起支付请求、查询支付状态以及接收支付结果回调等。为了避免测试过程中依赖真实的第三方支付服务，本章引入 QWireMockAPI 作为模拟服务，为 QWireCore 和 QWireAPI 提供稳定、可控的测试环境。

QWireMockAPI 提供以下核心能力：

- Order Service：模拟第三方支付接口，完成支付请求处理，并根据预设规则推进订单状态，例如待支付、支付中、支付成功、支付失败等。
- Merchant Service：模拟商户系统，接收支付平台发送的支付结果回调，以及订单状态变化的回调。

通过引入 Mock 服务，可以在无需依赖真实业务系统的情况下，构建稳定、可控的测试环境，快速验证 QWireCore 自动化测试框架的实现效果。同时，基于可配置的模拟能力，可以针对不同业务场景开发定向测试用例，并灵活编排复杂测试流程，为自动化测试框架的持续优化和能力验证提供有力支撑。

---

## 11.1 功能说明

### 11.1.1 Order Service

Order Service 负责订单创建、订单查询以及订单生命周期管理。

#### 创建订单

商户提交订单时，需要提供商户编号、订单参考号、支付信息以及商品信息。

通过校验后进入支付流程，无论支付成功还是失败，订单都会保存至数据库，并返回系统生成的支付单编号及当前处理结果；若请求本身无法处理，则直接返回 HTTP 错误，不进行数据持久化。

主要规则如下：

- 支持多商户支付接入。
- 同一 Merchant 下校验 Reference 必须唯一。
- 请求校验失败直接返回 HTTP 错误。
- 成功和业务失败订单均写入数据库。
- 数据库存储卡号掩码，不保存 CVV 与有效期。
- 模拟签名操作，但不真正处理签名校验。

由于支付请求中包含持卡人信息等敏感数据，在真实的支付系统中，除了使用 HTTPS 保障传输安全外，通常还会对卡号、CVV 等敏感字段进行应用层加密后再作为 API 请求数据发送。为了突出本书对自动化测试框架设计的介绍，而非支付安全实现，本章不实现完整的数据加密流程，仅通过在 HTTP Header 中增加模拟的请求签名，对 TransportProcessor 的处理流程进行示例性演示。若实际项目需要对请求数据进行加密、签名或其他安全处理，其实现方式与本书一致，均可通过 TransportProcessor 在请求发送前后完成相应的数据处理。

订单请求：

```json
{
   "reference": "string",
   "merchantId": "string",
   "amount": "number",
   "currency": "string",
   "status": "string",
   "paymentStatus": "string",
   "cardholderName": "string",
   "cardNumber": "string",
   "cvv": "string",
   "expiry": "string",
   "products": [
      {
         "sku": "string",
         "quantity": "integer",
         "unitPrice": "number",
         "amount": "number"
      }
   ]
}
```

订单响应：

```json
{
   "orderId": "550e8400-e29b-41d4-a716-446655440000",
   "reference": "ORDER20260001",
   "merchantId": "M10001",
   "amount": 100.00,
   "currency": "CAD",
   "paymentStatus": "PAID",
   "failReason": "仅订单失败时提供",
   "createTime": "2026-06-25T20:30:00Z",
   "finishTime": "2026-06-25T20:30:10Z"
}
```

#### 查询订单

订单查询支持使用商户订单号（Reference）或平台订单号（Order ID）作为查询条件。为了保证数据隔离，请求中需同时提供 merchantId。

查询接口始终返回订单在数据库中的最新状态。响应中的银行卡号采用掩码方式显示，不返回 CVV、有效期、持卡人姓名等任何敏感支付信息。

请求（按 Reference 查询）：

```json
{
   "reference": "string",
   "merchantId": "string"
}
```

请求（按 Order ID 查询）：

```json
{
   "orderId": "UUID",
   "merchantId": "string"
}
```

响应：

```json
{
   "orderId": "UUID",
   "reference": "string",
   "merchantId": "string",
   "amount": "number",
   "currency": "string",
   "cardNumber": "string(masked)",
   "paymentStatus": "PROCESSING | PAID | FAILED | TIMEOUT",
   "orderStatus": "PROCESSING | DELIVERED",
   "products": [
      {
         "sku": "string",
         "name": "string",
         "quantity": "integer",
         "unitPrice": "number",
         "amount": "number"
      }
   ]
}
```

---

#### 订单状态模拟

支付请求处理成功后，订单的支付状态立即更新为 PAID。随后，系统由后台调度器自动推进订单履约状态，整个状态流转过程无需人工干预。

状态推进规则如下：

- 支付成功后：paymentStatus 更新为 PAID，orderStatus 保持为 PROCESSING。
- 30 秒后：订单商品状态更新为 DELIVERED，同时 orderStatus 更新为 DELIVERED。

当订单状态发生变化后，系统会向商户模拟系统发送一次回调通知，用于模拟真实支付平台中的异步状态通知机制。

### 11.1.2 商户服务

商户服务用于模拟真实商户系统在支付流程中的行为，主要承担接收支付平台回调和提供回调查询能力两类职责。商户服务提供两个核心接口。

#### 1. 接收订单回调

接收订单状态变化的回调通知。当订单支付状态或履约状态发生变化时，订单服务会向该接口发送回调请求。商户服务在接收到回调后，会记录回调内容、回调时间以及对应的订单标识，便于在测试过程中进行调试和问题分析。

请求：

```json
{
   "orderId": "550e8400-e29b-41d4-a716-446655440000",
   "reference": "ORDER202600001",
   "merchantId": "M10001",
   "paymentStatus": "PAID",
   "orderStatus": "PROCESSING",
   "finishTime": "2026-06-25T20:30:10Z"
}
```

响应：

```json
{
   "status": "SUCCESS"
}
```

---

#### 2. 查询最近一次回调

该接口供 QWireCore Callback Checker 调用，用于查询指定订单最近一次收到的回调内容。测试框架可以通过该接口查询指定订单最近一次收到的回调信息，从而验证回调是否被正确触发、回调内容是否符合预期，以及是否存在重复回调等问题。

为了简化示例系统的实现，商户服务不对回调数据进行持久化处理，而是将收到的回调信息临时记录在内存中。Callback 检查器完成查询后，商户服务会清理该订单对应的已查询回调记录。通过这种方式，可以保证后续测试步骤能够继续检查是否出现新的重复回调，避免旧回调数据对测试结果造成干扰。

请求：

```json
{
   "orderId": "550e8400-e29b-41d4-a716-446655440000"
}
```

响应：

```json
{
   "callbackId": "d44d96df-9b0f-4b39-b0c8-dc47af6d74d",
   "callbackTime": "2026-06-25T20:30:11Z",
   "orderId": "550e8400-e29b-41d4-a716-446655440000",
   "reference": "ORDER202600001",
   "merchantId": "M10001",
   "paymentStatus": "PAID",
   "orderStatus": "PROCESSING"
}
```

如果指定订单尚未收到任何回调，则返回：

```http
HTTP/1.1 404 Not Found
```

```json
{
   "detail": "Callback not found."
}
```

### 11.1.3 异常响应设计

凡是有处理结果的请求，不统一使用 HTTP 200 响应。当订单无法被正常处理、无法记录到系统中时，返回 HTTP 层错误，并提供如下返回体：

```json
{
   "detail": "string"
}
```

异常响应规则如下：

| HTTP | Detail | 场景 |
| --- | --- | --- |
| 400 | Invalid card number | 请求格式错误或卡号无效 |
| 400 | Invalid currency | 请求格式错误或币种非法 |
| 404 | Order not exist | 订单不存在 |
| 405 | Method Not Allowed | 请求方法不支持 |
| 409 | Duplicate order | 重复订单 |
| 422 | Invalid request | Payload 校验失败 |
| 500 | Internal Server Error | 系统异常 |
