# QWireMockAPI Requirement

## 1. Order Server Requirement

Simulate order payment processing, order query, and trigger merchant callbacks when order status changes.

---

## 2. Order Interface Requirement

### 2.1 Request Content
Merchant provides the following information:
- Merchant ID
- Order reference number (unique per merchant)
- Amount and currency
- Simple product list

### 2.2 Processing and Persistence Rules
- Orders entering business processing are recorded to database regardless of success or failure.
- Interface returns main order request information, server-generated order ID, and processing result.
- Order reference number must be unique per merchant; reject if duplicate.
- Orders that cannot be processed by the system are not recorded to database; instead, return HTTP error code and message.

---

## 3. Query Interface Requirement

### 3.1 Query Criteria
- Query by merchant's order reference number.

### 3.2 Business Behavior
1. Card Number Rules:
   - Starting with `4`: Return `400`, error is "Card invalid".
   - Starting with `5`: Return `400`, error is "Insufficient balance" (business error).
2. Result Mapping Rules:
   - Success: Order status is `SUCCESS`, product status is `PROCESSING`.
   - Failure: Order status is `FAIL`, and return `failReason`.
   - In success scenario, must not return empty error field.
3. Status Progression Rules:
   - After ~30 seconds: `SHIPPED`
   - After ~60 seconds: `DELIVERED`
   - When all products are `DELIVERED`: Order status becomes `COMPLETED`
4. Trigger callback when status changes.
5. Database Persistence Requirements:
   - Card number must be masked in storage.
   - Must not store `CVV` / `expiry`.
6. Data Masking Scope:
   - Card numbers in query results, callback data, and API return data must all be masked.
   - All returns and callbacks must not contain `CVV` / `expiry`.

---

## 4. Callback Server Requirement

Simulate merchant system to receive callbacks from Order Server. Return responses using HTTP Code.

### 4.1 Callback Receipt Interface
- `POST`:
  - Validation passed: Write to memory and return `200`.
  - Validation failed: Return `400`.
- `GET`:
  - Invalid UUID format: Return `422`.
  - Record does not exist: Return `404`.
  - Record exists: Return `200`, data structure must conform to `OrderResponse`.

### 4.2 Storage and Logging
- Use in-memory storage only and output logs.
