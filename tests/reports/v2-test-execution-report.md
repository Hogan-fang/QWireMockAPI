# V2 Test Execution Report

- Total test cases: 20
- Passed: 20
- Failed: 0
- Skipped: 0

## Case Details
| No. | Test Case | Result | Test Point | Order Keyword |
|---:|---|---|---|---|
| 1 | test_v2_create_order_success_returns_201_and_masked_card | passed | POST /order creates successfully and returns a masked card | 0df613b9-bb54-445e-9c76-0a8ce96a68ba |
| 2 | test_v2_create_order_conflict_returns_409 | passed | POST /order duplicate reference returns 409 with unified HTTP error payload | 72f93407-339c-4cd7-88a5-78076583bc25 |
| 3 | test_v2_create_order_invalid_card_returns_400 | passed | POST /order card number starting with 4 returns 400 and FAIL | 774087c9-ad6e-44e2-bc05-5d104f1b86a9 |
| 4 | test_v2_create_order_insufficient_balance_returns_400 | passed | POST /order card number starting with 5 returns 400 and FAIL with insufficient balance | 96ea6a71-1e14-4c79-acaa-e6b6b2787f99 |
| 5 | test_v2_create_order_invalid_uuid_returns_422 | passed | POST /order invalid UUID in request body returns 422 from framework validation | 1aba8bca-a65b-4954-b459-6757591 |
| 6 | test_v2_get_order_invalid_uuid_returns_422 | passed | GET /order invalid UUID returns 422 with unified HTTP error payload | not-a-uuid |
| 7 | test_v2_get_order_not_found_returns_404 | passed | GET /order order not found returns 404 with unified HTTP error payload | d8928488-8768-45df-9d08-1126f07a043e |
| 8 | test_v2_get_order_found_returns_200 | passed | GET /order successful query returns 200 | 8e9d4868-5ab9-4d51-9435-aed88fcb004c |
| 9 | test_v2_create_then_get_order_flow | passed | Create then query: returns the same reference and orderId | 443f8096-8640-4bb7-9c68-5a30f2ec46e5 |
| 10 | test_v2_dispatch_callback_skip_by_amount_policy | passed | Amount threshold policy: high amount skips callback, low amount triggers callback | PX1001 |
| 11 | test_v2_callback_receive_returns_ok | passed | POST /callback valid payload returns 200 and callback data is logged only | 160dfc85-d7b8-4ab4-a1b8-9546c8e47b70 |
| 12 | test_v2_check_not_found_returns_404 | passed | GET /check returns 404 because callbacks are log-only | 8ff3add6-0dad-4852-a6ce-f1704b576e7a |
| 13 | test_v2_callback_invalid_payload_returns_400 | passed | POST /callback invalid payload returns 400 with unified HTTP error details | f13ee724-0262-45ea-b081-a2c6002dc81a |
| 14 | test_v2_integration_create_order_persists_db | passed | Integration: POST /order persists successfully into `order` / `order_product` | 755a6295-2d08-4259-8e23-fba7131b16d6 |
| 15 | test_v2_integration_invalid_card_persists_fail_order | passed | Integration: card number starting with 4 returns 400 and persists failed order | e88144e6-d3cc-426a-8f62-9ff587059ae1 |
| 16 | test_v2_integration_insufficient_balance_persists_fail_order | passed | Integration: card number starting with 5 returns 400 and persists insufficient-balance failure | 69758915-d080-4586-97f0-7d4ce2cd0913 |
| 17 | test_v2_integration_get_order_reads_from_db | passed | Integration: GET /order reads and returns data from database | 843654cd-3b28-44ea-ac4f-9c00a862f1a8 |
| 18 | test_v2_integration_duplicate_reference_conflict | passed | Integration: duplicate reference second submit returns 409 and keeps only one record | 6e95e9b1-ff00-4af6-9861-391cbf19e315 |
| 19 | test_v2_integration_product_status_transition_30s_60s | passed | Integration: product status becomes SHIPPED at 30s and DELIVERED at 60s, then order becomes COMPLETED | aa15bf3a-f9ea-433d-a03e-002b9948d4d6 |
| 20 | test_v2_integration_order_completed_only_when_all_products_delivered | passed | Integration: in multi-product orders, order becomes COMPLETED only after all products are DELIVERED | f6433928-43b2-47b9-a08f-4ea139fc5af0 |