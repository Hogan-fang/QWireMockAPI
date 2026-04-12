# QWireMockAPI Implementation Plan

## 1. Document Positioning and Mode

- Current document is in requirement mode, used to transform requirement into executable implementation plan and perform schema consistency checks.
- This document does not involve modifications to production code or test code; it only constrains subsequent spec, implementation, and verification paths.

## 2. Input Baseline

- Requirement baseline: `blueprint/requirement/requirement.md` / `requirement.en.md`
- Guideline baseline:
	- `QWireGuideline/guideline/project-guideline.md`
	- `QWireGuideline/guideline/methodology.md`
	- `QWireGuideline/guideline/AI-guideline.md`
- Schema baseline:
	- `blueprint/schema/order_server.yaml` / `order_server.en.yaml`
	- `blueprint/schema/callback_server.yaml` / `callback_server.en.yaml`

## 3. Objectives and Scope

### 3.1 Objectives
- Establish a traceable implementation plan covering Order Server and Callback Server.
- Clarify interface behavior, data security requirements, status flow, and callback rules.
- Complete schema satisfaction check before implementation and record gaps.

### 3.2 In Scope
- Order creation and query capability.
- Business failure branches caused by card number rules.
- Order status progression (PROCESSING -> SHIPPED -> DELIVERED -> COMPLETED).
- Status changes trigger callbacks.
- Callback receiving and query capability.
- Data security and masking constraints (card masking, no CVV/expiry).

### 3.3 Out of Scope
- Real payment gateway, authentication, risk control.
- Distributed and high-availability architecture.

## 4. Requirement Mapping

### 4.1 Order Interface
- Input: Merchant ID, order reference, amount and currency, product list.
- Orders (successful or business failures) require persistence and return main request info + server-generated order ID + processing result.
- Reference must be unique per merchant; reject if not satisfied.
- Requests that cannot be processed are not persisted; return HTTP error structure (code + detail).

### 4.2 Query Interface
- Query via merchant's order reference number.
- Business rules:
	- Card starting with 4 -> 400, card invalid.
	- Card starting with 5 -> 400, insufficient balance.
	- Success: Order SUCCESS, product PROCESSING.
	- Failure: Order FAIL + failReason.
	- Success does not return empty error field.
- Status progression: 30s -> SHIPPED, 60s -> DELIVERED, all DELIVERED -> COMPLETED.
- Status changes trigger callbacks.
- Both DB storage and external returns must mask card number; must not include CVV/expiry.

### 4.3 Callback Server
- POST: Validation passed, write to memory and return 200; otherwise 400.
- GET: UUID error 422, does not exist 404, exists 200 with data conforming to OrderResponse.
- In-memory storage + logging only.

## 5. Technical Constraints (from Guideline)

- API field naming uses camelCase; status enums use uppercase.
- HTTP/framework errors unified return structure:
	- `{ "code": "error_code", "detail": "error description" }`
- Business failures prioritize business structure expression (status=FAIL + failReason), strictly separated from HTTP error structure.
- All interface data must conform to OpenAPI Schema.
- Time fields use ISO 8601 + UTC.

## 6. Phased Implementation Plan

### Phase A: Contract Fixation
- Output: Revised order/callback schema and gap closure record.
- Completion: Key gap items all closed, field naming and error structure consistent with guideline.

### Phase B: Behavior Specification (Spec)
- Output:
	- `blueprint/spec/order-server.spec.yaml`
	- `blueprint/spec/callback-server.spec.yaml`
	- `blueprint/spec/shared-contracts.spec.yaml`
- Completion: State machine, callback timing, error layering (business failure vs HTTP error) all verifiable.
- Status: ✓ Completed

### Phase C: Implementation Deployment
- Output:
	- order/callback service implementation
	- Persistence model and transformation layer (camelCase <-> snake_case)
- Completion: Interface, persistence, masking, callback logic all achieve spec.
- Status: ✓ Completed

### Phase D: Verification and Regression
- Output: Test cases, sample data, verification report.
- Completion:
	- Critical and exception paths pass.
	- Callback and query 200/400/404/422 behavior meets expectation.
- Status: ✓ Completed
- Verification Summary:
	- Fixed outdated `failReason="Unsupported card type"` → `"Card invalid"` in `test_v2_create_order_invalid_card_returns_400` (mock and assertion synchronized).
	- Added `test_v2_check_invalid_uuid_returns_422`: GET /check with invalid UUID returns 422 + HttpErrorResponse.
	- Added `test_v2_check_found_returns_200`: After POST /callback write, GET /check returns 200 + OrderResponse.
	- All 16 tests passing (order service 11 + callback service 5).

## 7. Schema Satisfaction Check Results

Conclusion: All gap items closed, schema contract fixed, ready for Phase B (Spec generation).

### 7.1 Satisfied Items
- Order POST/GET and Callback POST/GET basic interfaces defined.
- Callback query status codes 422/404/200 covered.
- Unified HTTP error structure (code + detail) defined.
- Both OrderResponse and Callback OrderResponse do not include CVV/expiry fields.
- Status enums use uppercase; field naming conforms to camelCase.

### 7.2 Gap Items (All Closed)

1. ~~Masking format constraint missing~~ ✓ Closed
- Closure: In `order_server.yaml` `OrderResponse.cardNumber`, `OrderBusinessFailureResponse.cardNumber`, and `callback_server.yaml` `OrderResponse.cardNumber`, unified addition of `pattern: '^\d{6}\*{6}\d{4}$'`.

2. ~~failReason constraint not strict enough~~ ✓ Closed
- Closure: Both schema `OrderResponse` add `oneOf` conditional constraint—when `SUCCESS/COMPLETED`, `failReason` not allowed; when `FAIL`, `failReason` required and `minLength: 1`.

3. ~~Business failure message terminology difference~~ ✓ Closed
- Closure: Unified as `Card invalid` / `Insufficient balance`, semantically aligned with requirement; specific trigger conditions moved from schema to spec.

4. ~~Mock simulation logic mixed into interface definition~~ ✓ Closed
- Closure: Removed all mock simulation rules (card prefix judgment, status progression timing, implementation details) from interface and field descriptions; schema retains only pure contract semantics, business rules unified in spec.

## 8. Acceptance Criteria

- Plan, Spec, Schema are mutually traceable and conflict-free.
- All interface responses satisfy requirement + guideline in structure and status code.
- Success responses do not show empty error fields; failure responses contain failReason; HTTP errors use code/detail.
- Card numbers in both DB (storage layer) and external (query/callback/response) are masked per requirement, and do not include CVV/expiry.

## 9. Next Step Recommendations

1. ~~Complete schema revision and submit gap closure records.~~ ✓ Completed
2. ~~Generate spec based on fixed schema, finalize state machine, card trigger rules, and callback trigger points.~~ ✓ Completed
3. ~~Enter code implementation and testing deployment in development mode.~~ ✓ Completed
4. ~~Verification and regression: All spec validationChecklist items have corresponding tests, 16/16 passing.~~ ✓ Completed
