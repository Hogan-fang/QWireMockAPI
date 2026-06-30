from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

import qwire_mock.callback_service as callback_service

client = TestClient(callback_service.app)


def _callback_payload(order_id: str) -> dict:
    return {
        "orderId": order_id,
        "reference": "ORDER-001",
        "merchantId": "M10001",
        "paymentStatus": "PAID",
        "orderStatus": "PROCESSING",
        "finishTime": "2026-02-28T10:00:00Z",
    }


@pytest.mark.case(point="POST /callback valid payload returns 200")
def test_callback_receive_returns_success():
    response = client.post("/callback", json=_callback_payload(str(uuid4())))
    assert response.status_code == 200
    assert response.json() == {"status": "SUCCESS"}


@pytest.mark.case(point="POST /callback invalid payload returns 400 with detail only")
def test_callback_invalid_payload_returns_400():
    payload = _callback_payload(str(uuid4()))
    payload.pop("paymentStatus")

    response = client.post("/callback", json=payload)
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid request"}


@pytest.mark.case(point="GET /callback/latest returns 422 for invalid UUID")
def test_latest_callback_invalid_uuid_returns_422():
    response = client.get("/callback/latest", params={"orderId": "bad-uuid"})
    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid request"}


@pytest.mark.case(point="GET /callback/latest returns 404 when not found")
def test_latest_callback_not_found_returns_404():
    response = client.get("/callback/latest", params={"orderId": str(uuid4())})
    assert response.status_code == 404
    assert response.json() == {"detail": "Callback not found."}


@pytest.mark.case(point="GET /callback/latest returns record and clears it")
def test_latest_callback_found_then_cleared():
    order_id = str(uuid4())
    post_response = client.post("/callback", json=_callback_payload(order_id))
    assert post_response.status_code == 200

    first = client.get("/callback/latest", params={"orderId": order_id})
    assert first.status_code == 200
    body = first.json()
    assert body["orderId"] == order_id
    assert body["paymentStatus"] == "PAID"

    second = client.get("/callback/latest", params={"orderId": order_id})
    assert second.status_code == 404
    assert second.json() == {"detail": "Callback not found."}
