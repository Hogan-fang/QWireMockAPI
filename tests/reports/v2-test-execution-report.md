# V2 Test Execution Report

- Total test cases: 19
- Passed: 19
- Failed: 0
- Skipped: 0

## Case Details
| No. | Test Case | Result | Test Point | Order Keyword |
|---:|---|---|---|---|
| 1 | test_v2_create_order_success_returns_201_and_masked_card | passed | POST /order creates successfully and returns a masked card | 008a13cd-1116-4628-85df-d602f7bb3c4c |
| 2 | test_v2_create_order_conflict_returns_400 | passed | POST /order duplicate reference returns 400 with Order already exists | c57e710f-eae7-4580-aa2c-d51188cf54cd |
| 3 | test_v2_create_order_invalid_card_returns_400 | passed | POST /order card number starting with 4 returns 400 and FAIL | efbf25e3-b743-4640-a0fa-32388b2b6de1 |
| 4 | test_v2_create_order_invalid_uuid_returns_422 | passed | POST /order invalid UUID in request body returns 422 from framework validation | 1aba8bca-a65b-4954-b459-6757591 |
| 5 | test_v2_get_order_invalid_uuid_returns_400 | passed | GET /order invalid UUID returns 400 | not-a-uuid |
| 6 | test_v2_get_order_not_found_returns_404 | passed | GET /order order not found returns 404 | 502f3716-5570-41cc-a612-7cfe446191af |
| 7 | test_v2_get_order_found_returns_200 | passed | GET /order successful query returns 200 | 68fb556b-b7ad-4ff7-b313-4c6d0dd5bced |
| 8 | test_v2_create_then_get_order_flow | passed | Create then query: returns the same reference and orderId | 29a23eea-0eea-4544-8df3-c95c294da218 |
| 9 | test_v2_dispatch_callback_skip_by_amount_policy | passed | Amount threshold policy: high amount skips callback, low amount triggers callback | PX1001 |
| 10 | test_v2_integration_create_order_persists_db | passed | Integration: POST /order persists successfully into v2_orders/v2_order_products | bf2b3356-0a6f-47eb-b833-7576fb3ff19a |
| 11 | test_v2_integration_invalid_card_persists_fail_order | passed | Integration: card number starting with 4 returns 400 and persists failed order | 8fcf561f-1d8d-4a51-924b-a9b7fea58677 |
| 12 | test_v2_integration_get_order_reads_from_db | passed | Integration: GET /order reads and returns data from database | 97ebadc5-dc0b-42c9-8fe8-08fb0ccd0f3c |
| 13 | test_v2_integration_duplicate_reference_conflict | passed | Integration: duplicate reference second submit returns 400 and keeps only one record | e9997476-5401-4ef7-92b9-178d5c1190cd |
| 14 | test_v2_integration_product_status_transition_30s_60s | passed | Integration: product status becomes SHIPPED at 30s and DELIVERED at 60s, then order becomes COMPLETED | 7da3736a-793f-4bbe-80ae-8189125cce80 |
| 15 | test_v2_integration_order_completed_only_when_all_products_delivered | passed | Integration: in multi-product orders, order becomes COMPLETED only after all products are DELIVERED | 01b2bb53-46e9-4373-b84d-3a9826c6ca0f |
| 16 | test_v2_callback_receive_returns_ok | passed | POST /callback valid payload returns 200 and callback data is logged only | 56ea339e-a46e-4dae-84a6-399186d48fa2 |
| 17 | test_v2_check_not_found_returns_404 | passed | GET /check returns 404 because callbacks are log-only | 95245b49-0732-49cb-a006-d9acbbab9079 |
| 18 | test_v2_callback_invalid_payload_returns_400 | passed | POST /callback invalid payload returns 400 with error details | db505382-23e0-4299-a5ad-5cd96a3a94fe |
| 19 | test_generate_v2_execution_report | passed | Execution trace sample: record reference and orderId keywords | PX9001 |