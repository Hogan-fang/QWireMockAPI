# V2 Test Execution Report

- Total test cases: 16
- Passed: 16
- Failed: 0
- Skipped: 0

## Case Details
| No. | Test Case | Result | Test Point | Order Keyword |
|---:|---|---|---|---|
| 1 | test_v2_create_order_success_returns_201_and_masked_card | passed | POST /order creates successfully and returns a masked card | e901f5ef-41cf-4855-b05b-11a8bdd8d82d |
| 2 | test_v2_create_order_conflict_returns_409 | passed | POST /order duplicate reference returns 409 with unified HTTP error payload | 4a0cd0a2-daad-43b0-9425-d00d395e7a79 |
| 3 | test_v2_create_order_invalid_card_returns_400 | passed | POST /order card number starting with 4 returns 400 and FAIL | 2712988d-ed34-4272-a4ad-eea0ef0ddf4d |
| 4 | test_v2_create_order_insufficient_balance_returns_400 | passed | POST /order card number starting with 5 returns 400 and FAIL with insufficient balance | 8defbd8c-9c7c-40f0-8354-d3af67f38add |
| 5 | test_v2_create_order_invalid_uuid_returns_422 | passed | POST /order invalid UUID in request body returns 422 from framework validation | 1aba8bca-a65b-4954-b459-6757591 |
| 6 | test_v2_get_order_invalid_uuid_returns_422 | passed | GET /order invalid UUID returns 422 with unified HTTP error payload | not-a-uuid |
| 7 | test_v2_get_order_not_found_returns_404 | passed | GET /order order not found returns 404 with unified HTTP error payload | 2c2edac8-4010-4211-8b9c-bff3f479c390 |
| 8 | test_v2_get_order_found_returns_200 | passed | GET /order successful query returns 200 | 7acc59d9-d810-4a32-acb2-febb6195f043 |
| 9 | test_v2_create_then_get_order_flow | passed | Create then query: returns the same reference and orderId | 7f32c42b-53be-445d-9587-eabcb207bea9 |
| 10 | test_v2_dispatch_callback_skip_by_amount_policy | passed | Amount threshold policy: high amount skips callback, low amount triggers callback | PX1001 |
| 11 | test_v2_callback_receive_returns_ok | passed | POST /callback valid payload returns 200 and callback data is logged only | 2574a62f-6d33-4dd9-9a44-93d1f0c1fcfc |
| 12 | test_v2_check_not_found_returns_404 | passed | GET /check returns 404 when reference has no stored callback | cd42e1b5-fb1d-4ac8-97e5-92a72a49277c |
| 13 | test_v2_callback_invalid_payload_returns_400 | passed | POST /callback invalid payload returns 400 with unified HTTP error details | 6181a27d-b5c7-49ff-a292-d17000509304 |
| 14 | test_v2_check_invalid_uuid_returns_422 | passed | GET /check invalid UUID returns 422 with unified HTTP error payload | not-a-uuid |
| 15 | test_v2_check_found_returns_200 | passed | GET /check returns 200 with stored OrderResponse after POST /callback | 926f42d7-a61c-4ff9-8977-86ad3d4ea11b |
| 16 | test_generate_v2_execution_report | passed | Execution trace sample: record reference and orderId keywords | PX9001 |