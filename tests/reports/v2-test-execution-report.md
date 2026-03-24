# V2 Test Execution Report

- Total test cases: 19
- Passed: 19
- Failed: 0
- Skipped: 0

## Case Details
| No. | Test Case | Result | Test Point | Order Keyword |
|---:|---|---|---|---|
| 1 | test_v2_callback_receive_returns_ok | passed | POST /callback valid payload returns 200 and callback data is logged only | e45e7ba8-f6f7-4beb-a0ce-67692a6be622 |
| 2 | test_v2_check_not_found_returns_404 | passed | GET /check returns 404 because callbacks are log-only | eb651915-a2bc-4e2c-87a6-3df8b9377889 |
| 3 | test_v2_callback_invalid_payload_returns_400 | passed | POST /callback invalid payload returns 400 with error details | 7f4cc033-6191-4ede-be29-81443d21a831 |
| 4 | test_generate_v2_execution_report | passed | Execution trace sample: record reference and orderId keywords | PX9001 |
| 5 | test_v2_create_order_success_returns_201_and_masked_card | passed | POST /order creates successfully and returns a masked card | 3ff9bdc3-085f-481c-a3be-a6c19beed902 |
| 6 | test_v2_create_order_conflict_returns_400 | passed | POST /order duplicate reference returns 400 with Order already exists | 24774cfb-fede-42cf-8469-60b68ecf0344 |
| 7 | test_v2_create_order_invalid_card_returns_400 | passed | POST /order card number starting with 4 returns 400 and FAIL | 46206042-5908-49d6-aac5-3d3d59c14ae2 |
| 8 | test_v2_create_order_invalid_uuid_returns_422 | passed | POST /order invalid UUID in request body returns 422 from framework validation | 1aba8bca-a65b-4954-b459-6757591 |
| 9 | test_v2_get_order_invalid_uuid_returns_400 | passed | GET /order invalid UUID returns 400 | not-a-uuid |
| 10 | test_v2_get_order_not_found_returns_404 | passed | GET /order order not found returns 404 | a13b0931-d293-4780-bd1e-bb19182a71d7 |
| 11 | test_v2_get_order_found_returns_200 | passed | GET /order successful query returns 200 | 04f01225-6584-4c18-bb24-8ef43d6b3678 |
| 12 | test_v2_create_then_get_order_flow | passed | Create then query: returns the same reference and orderId | efef51a1-697a-442d-a4aa-38fedd8b6f0e |
| 13 | test_v2_dispatch_callback_skip_by_amount_policy | passed | Amount threshold policy: high amount skips callback, low amount triggers callback | PX1001 |
| 14 | test_v2_integration_create_order_persists_db | passed | Integration: POST /order persists successfully into orders/order_products | 706896f7-70d7-458e-90da-43e287e55a0b |
| 15 | test_v2_integration_invalid_card_persists_fail_order | passed | Integration: card number starting with 4 returns 400 and persists failed order | f4d50118-5b7e-42cb-9815-dc228c783a51 |
| 16 | test_v2_integration_get_order_reads_from_db | passed | Integration: GET /order reads and returns data from database | ecfaafce-0003-4242-9e3a-db6405625a02 |
| 17 | test_v2_integration_duplicate_reference_conflict | passed | Integration: duplicate reference second submit returns 400 and keeps only one record | 587d5db9-1a22-4252-915d-0cefc350fcf6 |
| 18 | test_v2_integration_product_status_transition_30s_60s | passed | Integration: product status becomes SHIPPED at 30s and DELIVERED at 60s, then order becomes COMPLETED | ae53271b-2645-469c-9075-1d07eb2ae8f1 |
| 19 | test_v2_integration_order_completed_only_when_all_products_delivered | passed | Integration: in multi-product orders, order becomes COMPLETED only after all products are DELIVERED | 1df7b19a-5b64-4b07-bb38-e14d2b2af447 |