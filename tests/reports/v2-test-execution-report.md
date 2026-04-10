# V2 Test Execution Report

- Total test cases: 12
- Passed: 12
- Failed: 0
- Skipped: 0

## Case Details
| No. | Test Case | Result | Test Point | Order Keyword |
|---:|---|---|---|---|
| 1 | test_v2_create_order_success_returns_201_and_masked_card | passed | POST /order creates successfully and returns a masked card | 9a8c2ac9-6e64-4d83-8bde-08d300342c40 |
| 2 | test_v2_create_order_conflict_returns_400 | passed | POST /order duplicate reference returns 400 with Order already exists | c3277b79-6781-48d7-82cc-6c90e572814c |
| 3 | test_v2_create_order_invalid_card_returns_400 | passed | POST /order card number starting with 4 returns 400 and FAIL | 2bec6f62-be3e-495e-9ce5-3e2621ae28c7 |
| 4 | test_v2_create_order_invalid_uuid_returns_422 | passed | POST /order invalid UUID in request body returns 422 from framework validation | 1aba8bca-a65b-4954-b459-6757591 |
| 5 | test_v2_get_order_invalid_uuid_returns_422 | passed | GET /order invalid UUID returns 422 with unified HTTP error payload | not-a-uuid |
| 6 | test_v2_get_order_not_found_returns_404 | passed | GET /order order not found returns 404 with unified HTTP error payload | 5f520f68-0260-4f0d-886c-6913b8ca96aa |
| 7 | test_v2_get_order_found_returns_200 | passed | GET /order successful query returns 200 | 0df03736-60ec-4ddd-975f-6b88fc42fcef |
| 8 | test_v2_create_then_get_order_flow | passed | Create then query: returns the same reference and orderId | cc6964fc-970b-45b6-8fac-ab018a3bd8b3 |
| 9 | test_v2_dispatch_callback_skip_by_amount_policy | passed | Amount threshold policy: high amount skips callback, low amount triggers callback | PX1001 |
| 10 | test_v2_callback_receive_returns_ok | passed | POST /callback valid payload returns 200 and callback data is logged only | 50b6da73-79c1-4cb4-b042-4fec378dd44c |
| 11 | test_v2_check_not_found_returns_404 | passed | GET /check returns 404 because callbacks are log-only | 48c13b57-f84c-4e58-b130-d327dc60cf60 |
| 12 | test_v2_callback_invalid_payload_returns_400 | passed | POST /callback invalid payload returns 400 with unified HTTP error details | 1e2ae38e-2289-4e0a-8fe9-b6164b31d72e |