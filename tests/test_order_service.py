from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

import qwire_mock.order_service as order_service
from qwire_mock.schemas import OrderCreateResponse, OrderQueryResponse, ProductQueryResponse


@pytest.fixture
def order_client(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(order_service.order_db, "init_db", lambda: None)
    monkeypatch.setattr(order_service, "_status_scheduler", lambda: None)
    order_service._stop_event.clear()
    with TestClient(order_service.app) as client:
        yield client


def _build_create_response(
    order_id: str,
    payment_status: str = "PAID",
    fail_reason: str | None = None,
) -> OrderCreateResponse:
    now = datetime.now(timezone.utc)
    return OrderCreateResponse(
        orderId=order_id,
        reference="ORDER-001",
        merchantId="M10001",
        amount=99.99,
        currency="CAD",
        paymentStatus=payment_status,
        createTime=now,
        finishTime=now,
        failReason=fail_reason,
    )


def _build_query_response(order_id: str, payment_status: str = "PAID") -> OrderQueryResponse:
    return OrderQueryResponse(
        orderId=order_id,
        reference="ORDER-001",
        merchantId="M10001",
        amount=99.99,
        currency="CAD",
        cardNumber="411111******1111",
        paymentStatus=payment_status,
        orderStatus="PROCESSING",
        products=[
            ProductQueryResponse(
                sku="SKU-1",
                name="SKU-1",
                quantity=1,
                unitPrice=99.99,
                amount=99.99,
            )
        ],
        failReason="余额不足" if payment_status == "FAILED" else None,
    )


def _payload(reference: str, card_number: str = "6222222222222222", currency: str = "CAD") -> dict:
    return {
        "reference": reference,
        "merchantId": "M10001",
        "amount": 99.99,
        "currency": currency,
        "cardholderName": "TEST USER",
        "cardNumber": card_number,
        "cvv": "123",
        "expiry": "12/28",
        "products": [
            {
                "sku": "SKU-1",
                "quantity": 1,
                "unitPrice": 99.99,
                "amount": 99.99,
            }
        ],
    }


@pytest.mark.case(point="POST /order PAID returns 200 and excludes failReason")
def test_create_order_paid_returns_200(order_client: TestClient, monkeypatch: pytest.MonkeyPatch):
    oid = str(uuid4())
    monkeypatch.setattr(order_service.order_db, "exists", lambda merchant_id, reference: False)
    monkeypatch.setattr(
        order_service.order_db,
        "create_order",
        lambda request, callback_url, payment_status, order_status, fail_reason=None: _build_create_response(
            oid,
            payment_status,
            fail_reason,
        ),
    )
    events: list[str] = []
    monkeypatch.setattr(order_service, "_dispatch_callback", lambda payload, callback_url: events.append(payload.orderStatus))

    response = order_client.post("/order", json=_payload("ORDER-PAID"))
    assert response.status_code == 200
    body = response.json()
    assert body["paymentStatus"] == "PAID"
    assert "failReason" not in body
    assert events == ["PROCESSING"]


@pytest.mark.case(point="POST /order card starting with 4 returns 400 without persistence")
def test_create_order_invalid_card_returns_400(order_client: TestClient, monkeypatch: pytest.MonkeyPatch):
    called = {"create": 0}

    monkeypatch.setattr(order_service.order_db, "exists", lambda merchant_id, reference: False)

    def _not_called(*args, **kwargs):
        called["create"] += 1
        return _build_create_response(str(uuid4()))

    monkeypatch.setattr(order_service.order_db, "create_order", _not_called)

    response = order_client.post("/order", json=_payload("ORDER-400", card_number="4111111111111111"))
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid card number"}
    assert called["create"] == 0


@pytest.mark.case(point="POST /order card starting with 5 returns 200 with FAILED and failReason")
def test_create_order_balance_failed_returns_200(order_client: TestClient, monkeypatch: pytest.MonkeyPatch):
    oid = str(uuid4())
    monkeypatch.setattr(order_service.order_db, "exists", lambda merchant_id, reference: False)
    monkeypatch.setattr(
        order_service.order_db,
        "create_order",
        lambda request, callback_url, payment_status, order_status, fail_reason=None: _build_create_response(
            oid,
            payment_status,
            fail_reason,
        ),
    )

    response = order_client.post("/order", json=_payload("ORDER-FAILED", card_number="5222222222222222"))
    assert response.status_code == 200
    body = response.json()
    assert body["paymentStatus"] == "FAILED"
    assert body["failReason"] == "余额不足"


@pytest.mark.case(point="POST /order duplicate returns 409")
def test_create_order_duplicate_returns_409(order_client: TestClient, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(order_service.order_db, "exists", lambda merchant_id, reference: True)

    response = order_client.post("/order", json=_payload("ORDER-DUP"))
    assert response.status_code == 409
    assert response.json() == {"detail": "Duplicate order"}


@pytest.mark.case(point="POST /order invalid currency returns 400")
def test_create_order_invalid_currency_returns_400(order_client: TestClient, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(order_service.order_db, "exists", lambda merchant_id, reference: False)

    response = order_client.post("/order", json=_payload("ORDER-CURR", currency="XXX"))
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid currency"}


@pytest.mark.case(point="GET /order by reference returns 200")
def test_get_order_by_reference_returns_200(order_client: TestClient, monkeypatch: pytest.MonkeyPatch):
    oid = str(uuid4())
    monkeypatch.setattr(
        order_service.order_db,
        "get_order",
        lambda merchant_id, reference=None, order_id=None: _build_query_response(oid),
    )

    response = order_client.get("/order", params={"merchantId": "M10001", "reference": "ORDER-001"})
    assert response.status_code == 200
    body = response.json()
    assert body["merchantId"] == "M10001"
    assert body["orderStatus"] == "PROCESSING"


@pytest.mark.case(point="GET /order by orderId returns 200")
def test_get_order_by_order_id_returns_200(order_client: TestClient, monkeypatch: pytest.MonkeyPatch):
    oid = str(uuid4())
    monkeypatch.setattr(
        order_service.order_db,
        "get_order",
        lambda merchant_id, reference=None, order_id=None: _build_query_response(oid),
    )

    response = order_client.get("/order", params={"merchantId": "M10001", "orderId": oid})
    assert response.status_code == 200
    assert response.json()["orderId"] == oid


@pytest.mark.case(point="GET /order invalid query combinations return 422")
def test_get_order_invalid_query_returns_422(order_client: TestClient):
    response_none = order_client.get("/order", params={"merchantId": "M10001"})
    assert response_none.status_code == 422
    assert response_none.json() == {"detail": "Invalid request"}

    oid = str(uuid4())
    response_both = order_client.get(
        "/order",
        params={"merchantId": "M10001", "reference": "ORDER-1", "orderId": oid},
    )
    assert response_both.status_code == 422
    assert response_both.json() == {"detail": "Invalid request"}


@pytest.mark.case(point="GET /order not found returns 404")
def test_get_order_not_found_returns_404(order_client: TestClient, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(order_service.order_db, "get_order", lambda merchant_id, reference=None, order_id=None: None)

    response = order_client.get("/order", params={"merchantId": "M10001", "reference": "ORDER-404"})
    assert response.status_code == 404
    assert response.json() == {"detail": "Order not exist"}
