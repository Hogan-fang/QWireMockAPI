import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

import qwire_mock.order_service as order_service
from qwire_mock import order_db


def _maybe_clear_orders() -> None:
    if os.environ.get("QWIRE_V2_CLEAR_DB_BEFORE_TEST", "0") == "1":
        order_db.clear_orders()


@pytest.fixture
def integration_order_client():
    order_db.init_db()
    with TestClient(order_service.app) as client:
        yield client


def _payload(reference: str, card_number: str = "6222222222222222") -> dict:
    return {
        "reference": reference,
        "merchantId": "M10001",
        "amount": 120.0,
        "currency": "CAD",
        "cardholderName": "TEST USER",
        "cardNumber": card_number,
        "cvv": "123",
        "expiry": "12/28",
        "products": [
            {
                "sku": "SKU-IT-01",
                "quantity": 1,
                "unitPrice": 120.0,
                "amount": 120.0,
            }
        ],
    }


@pytest.mark.v2_integration
@pytest.mark.case(point="Integration: POST /order persists PAID order")
def test_integration_create_paid_order_persists_db(integration_order_client: TestClient):
    _maybe_clear_orders()
    ref = f"ORDER-{uuid4()}"

    response = integration_order_client.post("/order", json=_payload(ref))
    assert response.status_code == 200
    body = response.json()
    assert body["paymentStatus"] == "PAID"

    query = integration_order_client.get("/order", params={"merchantId": "M10001", "reference": ref})
    assert query.status_code == 200
    assert query.json()["reference"] == ref


@pytest.mark.v2_integration
@pytest.mark.case(point="Integration: card starts with 4 returns 400 and does not persist")
def test_integration_invalid_card_returns_400_no_persist(integration_order_client: TestClient):
    _maybe_clear_orders()
    ref = f"ORDER-{uuid4()}"

    response = integration_order_client.post("/order", json=_payload(ref, card_number="4111111111111111"))
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid card number"}

    query = integration_order_client.get("/order", params={"merchantId": "M10001", "reference": ref})
    assert query.status_code == 404


@pytest.mark.v2_integration
@pytest.mark.case(point="Integration: PAID order auto transitions to DELIVERED after scheduler")
def test_integration_transition_to_delivered(integration_order_client: TestClient):
    _maybe_clear_orders()
    ref = f"ORDER-{uuid4()}"

    created = integration_order_client.post("/order", json=_payload(ref))
    assert created.status_code == 200

    conn = order_db._conn()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE orders SET create_time = NOW() - INTERVAL 31 SECOND WHERE merchant_id = %s AND reference = %s",
                ("M10001", ref),
            )
        conn.commit()
    finally:
        conn.close()

    order_db.apply_scheduled_transitions()

    query = integration_order_client.get("/order", params={"merchantId": "M10001", "reference": ref})
    assert query.status_code == 200
    assert query.json()["orderStatus"] == "DELIVERED"
