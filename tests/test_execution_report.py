from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

import qwire_mock.callback_service as callback_service


client = TestClient(callback_service.app)


@pytest.mark.case(point="Execution trace sample: record reference and orderId keywords")
def test_generate_v2_execution_report(record_order_keyword):
    order_id = str(uuid4())
    record_order_keyword(order_id)
    payload = {
        "orderId": order_id,
        "reference": "ORDER-REPORT-01",
        "merchantId": "M10001",
        "paymentStatus": "PAID",
        "orderStatus": "PROCESSING",
        "finishTime": "2026-02-28T10:00:00Z",
    }

    post_resp = client.post("/callback", json=payload)
    record_order_keyword("ORDER-REPORT-01")

    check_resp = client.get("/callback/latest", params={"orderId": order_id})

    assert post_resp.status_code == 200
    assert check_resp.status_code == 200
    body = check_resp.json()
    assert body["orderId"] == order_id
    assert body["reference"] == "ORDER-REPORT-01"
    assert body["paymentStatus"] == "PAID"
