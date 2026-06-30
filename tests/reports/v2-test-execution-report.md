# V2 Test Execution Report

- Total test cases: 3
- Passed: 3
- Failed: 0
- Skipped: 0

## Case Details
| No. | Test Case | Result | Test Point | Order Keyword |
|---:|---|---|---|---|
| 1 | test_integration_create_paid_order_persists_db | passed | Integration: POST /order persists PAID order | N/A |
| 2 | test_integration_invalid_card_returns_400_no_persist | passed | Integration: card starts with 4 returns 400 and does not persist | N/A |
| 3 | test_integration_transition_to_delivered | passed | Integration: PAID order auto transitions to DELIVERED after scheduler | N/A |