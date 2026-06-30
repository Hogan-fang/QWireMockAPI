# QwireMockAPI Blueprint Delivery Roadmap

> **备注：文档定位**
> 本文件用于拆分 `implementation-plan.md` 的执行阶段，所有来源标记统一使用备注方式。

## Phase 1：Schema Freeze

- **输出文件**
  - `../schema/order_service.yaml`
  - `../schema/callback_service.yaml`
- **完成标准**
  - 路径、字段、响应码完成确认
  - `order` / `callback` 的输入输出模型一致

> 备注：来源：schema

## Phase 2：Spec Finalize

- **输出文件**
  - `../spec/order-service.spec.yaml`
  - `../spec/callback-service.spec.yaml`
  - `../spec/shared-contracts.spec.yaml`
- **完成标准**
  - 订单规则、callback 规则和共享约束全部落到 spec
  - 每条核心规则都能追溯到需求或 schema

> 备注：来源：需求

## Phase 3：Python Scaffold

- **输出目录**
  - `../../src/qwire_mock/`
  - `../../tests/`
- **完成标准**
  - `order_server` 与 `callback_server` 的 Python 工程骨架建立完成
  - DB、内存缓存、日志模块均可落位

> 备注：来源：工程化补充

## Phase 4：Test Assets

- **输出文件/目录**
  - `../../tests/test_order_service.py`
  - `../../tests/test_callback_service.py`
  - `../../tests/reports/`
- **完成标准**
  - 正常流、失败流、状态推进和 callback 查询均有测试样例
  - 测试报告包含 `reference`、`orderId`、`status` 等关键字

> 备注：来源：工程化补充
