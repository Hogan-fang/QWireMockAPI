# QWireMockAPI

A comprehensive, well-tested order payment and callback simulation system built with FastAPI + MySQL, compliant with OpenAPI 3.0 specification and the three-layer "Requirement-Schema-Spec" engineering methodology.

## 🎯 Project Overview

QWireMockAPI consists of two main services:

- **Order Server** (`order_service.py`) — Order creation and query service, simulating payment processing, card number rule validation, order status flow, and callbacks.
- **Callback Server** (`callback_service.py`) — Merchant webhook receiver, simulating receiving order status notifications and supporting query of received callback data.

### Key Features

✅ **Complete Order Lifecycle** — From creation, business validation, to status progression (SUCCESS → SHIPPED → DELIVERED → COMPLETED)  
✅ **Card Number Rule Validation** — Support business failure scenarios for 4* and 5* card numbers (Card invalid / Insufficient balance)  
✅ **Data Security** — Card number masking (first 6 + last 4), sensitive field scrubbing, no CVV/expiry in returns  
✅ **Event-Driven Callbacks** — Order status changes automatically trigger ORDER_SUCCESS / ORDER_SHIPPED / ORDER_DELIVERED / ORDER_COMPLETED  
✅ **Memory & Log Storage** — Callback Server uses in-memory + log-based storage with query capability  
✅ **Standardized Error Handling** — Unified HTTP error structure (code + detail) distinct from business failures  
✅ **Comprehensive Test Coverage** — 16 unit/functional tests + integration tests, 1:1 source-to-test code ratio  

## 📋 Quick Start

### Requirements

- Python 3.10+
- MySQL 5.7+ or 8.0+
- FastAPI, Pydantic v2

### Installation and Running

```bash
# Clone or enter project directory
cd /Users/hao/vs-workspace/QWireMockAPI

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure database (edit config.yaml or config.properties)
# Default: MySQL localhost:3306, database=qwire_test

# Initialize database
python -m qwire_mock.order_db  # Auto-creates tables

# Start two services (in two terminals)
# Terminal 1 - Order Server (port 9100)
PYTHONPATH=src python -m qwire_mock.order_service

# Terminal 2 - Callback Server (port 8100)
PYTHONPATH=src python -m qwire_mock.callback_service
```

### Testing

```bash
# Run all unit tests (non-integration)
PYTHONPATH=src .venv/bin/python -m pytest tests/ -m "not integration" -v

# Run integration tests
PYTHONPATH=src .venv/bin/python -m pytest tests/ -m "integration" -v

# Generate test execution report
pytest tests/ -m "v2_" --html=tests/reports/report.html
```

## 📁 Project Structure

```
QWireMockAPI/
├── blueprint/                           # Design documentation
│   ├── requirement/
│   │   ├── requirement.md              # Business requirement (Chinese)
│   │   └── requirement.en.md           # Business requirement (English)
│   ├── schema/
│   │   ├── order_service.yaml          # Order API contract (Chinese)
│   │   ├── order_server.en.yaml        # Order API contract (English)
│   │   ├── callback_service.yaml       # Callback API contract (Chinese)
│   │   └── callback_server.en.yaml     # Callback API contract (English)
│   ├── spec/
│   │   ├── order-service.spec.yaml     # Order behavior spec (Chinese)
│   │   ├── order-service.spec.en.yaml  # Order behavior spec (English)
│   │   ├── callback-service.spec.yaml  # Callback behavior spec (Chinese)
│   │   ├── callback-service.spec.en.yaml # Callback behavior spec (English)
│   │   ├── shared-contracts.spec.yaml  # Shared contracts (Chinese)
│   │   └── shared-contracts.spec.en.yaml # Shared contracts (English)
│   ├── implementation-plan.md           # Implementation plan (Chinese)
│   ├── implementation-plan.en.md        # Implementation plan (English)
│   ├── example/                         # API request/response examples
│   │   ├── order/                       # Order Server examples
│   │   └── callback/                    # Callback Server examples
│   └── README.md                        # Design documentation guide
├── src/qwire_mock/
│   ├── __main__.py                      # Startup entry point
│   ├── config.py                        # Configuration management (yaml / properties)
│   ├── schemas.py                       # Pydantic data models (shared)
│   ├── order_service.py                 # Order Server (FastAPI)
│   ├── order_db.py                      # Order Server DB layer (MySQL)
│   └── callback_service.py              # Callback Server (FastAPI)
├── tests/
│   ├── conftest.py                      # pytest configuration and report generation
│   ├── test_order_service.py            # Order Server unit tests (11 tests)
│   ├── test_callback_service.py         # Callback Server unit tests (5 tests)
│   ├── test_execution_report.py         # Report generation test
│   ├── test_order_service_integration.py # Integration tests (optional)
│   └── reports/                         # Test execution reports
├── config.yaml / config.properties      # Application configuration
├── requirements.txt                     # Python dependencies
├── pom.xml                              # Maven configuration (legacy)
└── README.md / README.en.md             # Project documentation (this file)
```

## 🔌 API Documentation

### Order Server (Port 9100)

#### POST /order — Create Order

```bash
curl -X POST http://127.0.0.1:9100/order \
  -H "Content-Type: application/json" \
  -d '{
    "reference": "d290f1ee-6c54-4b01-90e6-d701748f0851",
    "name": "Widget Order",
    "mid": "M123456789",
    "callback": "http://localhost:8100/callback",
    "cardNumber": "6222222222222222",
    "cvv": "123",
    "expiry": "12/28",
    "amount": 99.99,
    "currency": "USD",
    "products": [{"productId": "P1", "count": 2, "spec": "M"}],
    "signature": "8f14e45fceea167a5a36dedd4bea2543"
  }'
```

**Success Response (201)**
```json
{
  "reference": "d290f1ee-6c54-4b01-90e6-d701748f0851",
  "orderId": "PX39280930012",
  "name": "Widget Order",
  "status": "SUCCESS",
  "cardNumber": "622222******2222",
  "products": [...],
  "amount": 99.99,
  "currency": "USD",
  "orderDate": "2024-01-10T10:15:30Z"
}
```

**Card Number Rules (400)**
- Starts with 4 → failReason: "Card invalid"
- Starts with 5 → failReason: "Insufficient balance"

#### GET /order — Query Order

```bash
curl http://127.0.0.1:9100/order?reference=d290f1ee-6c54-4b01-90e6-d701748f0851
```

### Callback Server (Port 8100)

#### POST /callback — Receive Callback

```bash
curl -X POST http://127.0.0.1:8100/callback \
  -H "Content-Type: application/json" \
  -d '{ "reference": "...", "status": "SUCCESS", ... }'
```

#### GET /callback/latest — Query Latest Callback

```bash
curl http://127.0.0.1:8100/callback/latest?orderId=550e8400-e29b-41d4-a716-446655440000
```

Complete API documentation available in `blueprint/schema/order_service.yaml` and `blueprint/schema/callback_service.yaml` (OpenAPI 3.0 format).

## 📊 Code Statistics

| Category | Files | Lines |
|----------|-------|-------|
| **Source Code** | 7 | 894 |
| 　- schemas.py | 1 | 53 |
| 　- config.py | 1 | 104 |
| 　- order_service.py | 1 | 189 |
| 　- order_db.py | 1 | 382 |
| 　- callback_service.py | 1 | 108 |
| **Tests** | 5 | 878 |
| 　- Functional tests | 3 | 459 |
| 　- Integration tests | 1 | 332 |
| **Documentation** | 14 | 1,172 |
| 　- Schema + Spec | 6 | 616 |
| 　- Requirement + Plan | 4 | 210 |
| **Total** | **26** | **2,944** |

## 🎓 Engineering Methodology

This project follows the core **Plan → Spec → Implementation → Verification** four-layer design process:

1. **Plan Layer** (`blueprint/requirement/` + `blueprint/implementation-plan.md`) — Requirement collection and design planning
2. **Spec Layer** (`blueprint/schema/` + `blueprint/spec/`) — Interface contracts and behavior specifications
   - Schema ensures strict interface structure
   - Spec defines business rules and state machine
3. **Implementation Layer** (`src/`) — Code implementation
4. **Verification Layer** (`tests/`) — Unit and integration test verification

All design documents are provided in both **Chinese** and **English** versions (`.en` suffix) for team collaboration. See [implementation-plan.en.md](blueprint/implementation-plan.en.md) for details.

## ✅ Test Coverage

- **Order Service** — 11 unit tests
  - POST /order success, conflict, card validation, UUID validation
  - GET /order success, 404, 422, status progression
- **Callback Service** — 5 unit tests
  - POST /callback success, failure
  - GET /check success, 404, 422
- **Integration Tests** — Complete lifecycle, callback flow (optional)

```bash
# View test execution report
pytest tests/ --co -q  # List all tests
pytest tests/ -v       # Run with detailed output
```

## 📝 Configuration

### config.yaml (Recommended)

```yaml
database:
  host: localhost
  port: 3306
  user: root
  password: root
  db_name: qwire_test

server:
  order_port: 9100
  callback_port: 8100

logging:
  order_log: logs/order.log
  callback_log: logs/callback.log
```

### config.properties (Alternative)

```properties
db.host=localhost
db.port=3306
db.user=root
db.password=root
db.name=qwire_test
```

## 🔧 Development Guide

### Local Development Flow

1. Edit code or tests
2. `pytest tests/ -m "not integration"` Run unit tests
3. Fix failing tests
4. Run full test suite before commit

### FAQ

**Q: How to modify card number rules?**  
A: Edit `_check_card_rules()` function in `src/qwire_mock/order_service.py`. Rules also documented in `blueprint/spec/order-service.spec.yaml`.

**Q: How to change status progression timing?**  
A: Edit `PROCESSING_TO_SHIPPED_DELAY` and `SHIPPED_TO_DELIVERED_DELAY` constants in `src/qwire_mock/order_service.py`.

**Q: Database connection failed?**  
A: Check `config.yaml` or `config.properties`, ensure MySQL is running and credentials are correct.

## 📜 License

Apache License 2.0

## 📧 Contact

QWire Project Team  
Email: you@your-company.com
