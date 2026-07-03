import json
import logging
import os
import threading
import urllib.error
import urllib.request
from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import FastAPI, Header, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from qwire_mock import order_db
from qwire_mock.config import load_config
from qwire_mock.schemas import OrderCallbackRequest, OrderCreateRequest

logger = logging.getLogger(__name__)
CONFIG = load_config()
ORDER_CONFIG = CONFIG["order"]
LOGGING_CONFIG = CONFIG["logging"]

ALLOWED_CURRENCIES = {"CAD", "USD"}
POLL_INTERVAL_SECONDS = int(ORDER_CONFIG["poll_interval_seconds"])
PROCESS_HISTORICAL_ON_STARTUP = bool(ORDER_CONFIG.get("process_historical_on_startup", False))
_stop_event = threading.Event()
_scheduler_cutoff_time = None


def _ensure_file_logger() -> None:
    logger.setLevel(logging.INFO)
    order_log_path = LOGGING_CONFIG["order_log"]
    existing = [
        handler
        for handler in logger.handlers
        if isinstance(handler, logging.FileHandler)
        and os.path.basename(getattr(handler, "baseFilename", "")) == os.path.basename(order_log_path)
    ]
    if existing:
        return

    file_handler = logging.FileHandler(order_log_path, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    logger.addHandler(file_handler)


_ensure_file_logger()


def _json(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, default=str)


def _sanitize_create_request(payload: dict) -> dict:
    sanitized = dict(payload)
    if "cvv" in sanitized:
        sanitized["cvv"] = "***REDACTED***"
    if "expiry" in sanitized:
        sanitized["expiry"] = "***REDACTED***"
    if "cardholderName" in sanitized:
        sanitized["cardholderName"] = "***REDACTED***"
    if "cardNumber" in sanitized:
        sanitized["cardNumber"] = order_db.mask_card(str(sanitized["cardNumber"]))
    return sanitized


def _dispatch_callback(payload: OrderCallbackRequest, callback_url: str) -> None:
    body = payload.model_dump(mode="json")
    logger.info("dispatch callback -> %s\n%s", callback_url, _json(body))

    request_body = json.dumps(body, ensure_ascii=False, default=str).encode("utf-8")
    request = urllib.request.Request(
        callback_url,
        data=request_body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            logger.info("callback response status=%s", response.status)
    except urllib.error.HTTPError as exc:
        logger.warning("callback http error: %s", exc)
    except Exception as exc:
        logger.warning("callback request failed: %s", exc)


def _status_scheduler() -> None:
    while not _stop_event.is_set():
        transitions = order_db.apply_scheduled_transitions(min_create_time=_scheduler_cutoff_time)
        for target in transitions:
            callback = OrderCallbackRequest(
                orderId=target.order_id,
                reference=target.reference,
                merchantId=target.merchant_id,
                paymentStatus=target.payment_status,
                orderStatus=target.order_status,
                finishTime=target.finish_time,
            )
            _dispatch_callback(callback, target.callback_url)
        _stop_event.wait(POLL_INTERVAL_SECONDS)


@asynccontextmanager
async def lifespan(_: FastAPI):
    global _scheduler_cutoff_time
    order_db.init_db()
    if PROCESS_HISTORICAL_ON_STARTUP:
        _scheduler_cutoff_time = None
        logger.info("order scheduler startup mode: process historical orders enabled")
    else:
        _scheduler_cutoff_time = order_db.db_now()
        logger.info("order scheduler startup mode: skip historical orders before %s", _scheduler_cutoff_time)
    logger.info("order service startup: scheduler poll_interval=%ss", POLL_INTERVAL_SECONDS)
    scheduler = threading.Thread(target=_status_scheduler, daemon=True)
    scheduler.start()
    try:
        yield
    finally:
        _stop_event.set()
        logger.info("order service shutdown")


app = FastAPI(title="QWire Order API v3", version="3.0.0", lifespan=lifespan)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_: Request, __: RequestValidationError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": "Invalid request"})


@app.post("/order")
def create_order(body: OrderCreateRequest, _: str | None = Header(default=None, alias="X-Mock-Signature")):
    logger.info(
        "POST /order request:\n%s",
        _json(body.model_dump(mode="json", exclude_unset=True)),
    )

    if body.currency not in ALLOWED_CURRENCIES:
        return JSONResponse(status_code=400, content={"detail": "Invalid currency"})

    if order_db.exists(body.merchantId, body.reference):
        return JSONResponse(status_code=409, content={"detail": "Duplicate order"})

    if body.cardNumber.strip().startswith("4"):
        return JSONResponse(status_code=400, content={"detail": "Invalid card number"})

    callback_url = f"http://127.0.0.1:{CONFIG['server']['callback_port']}/callback"

    if body.cardNumber.strip().startswith("5"):
        created = order_db.create_order(
            request=body,
            callback_url=callback_url,
            payment_status="FAILED",
            order_status="PROCESSING",
            fail_reason="余额不足",
        )
        payload = created.model_dump(mode="json")
        logger.info("POST /order response(200):\n%s", _json(payload))
        return JSONResponse(status_code=200, content=payload)

    created = order_db.create_order(
        request=body,
        callback_url=callback_url,
        payment_status="PAID",
        order_status="PROCESSING",
    )

    callback_payload = OrderCallbackRequest(
        orderId=created.orderId,
        reference=created.reference,
        merchantId=created.merchantId,
        paymentStatus="PAID",
        orderStatus="PROCESSING",
        finishTime=created.finishTime or created.createTime,
    )
    _dispatch_callback(callback_payload, callback_url)

    payload = created.model_dump(mode="json")
    payload.pop("failReason", None)
    logger.info("POST /order response(200):\n%s", _json(payload))
    return JSONResponse(status_code=200, content=payload)


@app.get("/order")
def get_order(
    merchantId: str = Query(...),
    reference: str | None = Query(default=None),
    orderId: str | None = Query(default=None),
):
    if (reference is None and orderId is None) or (reference is not None and orderId is not None):
        return JSONResponse(status_code=422, content={"detail": "Invalid request"})

    order_uuid: UUID | None = None
    if orderId is not None:
        try:
            order_uuid = UUID(orderId)
        except ValueError:
            return JSONResponse(status_code=422, content={"detail": "Invalid request"})

    order = order_db.get_order(merchant_id=merchantId, reference=reference, order_id=order_uuid)
    if order is None:
        return JSONResponse(status_code=404, content={"detail": "Order not exist"})

    payload = order.model_dump(mode="json")
    if order.paymentStatus != "FAILED":
        payload.pop("failReason", None)
    logger.info("GET /order response:\n%s", _json(payload))
    return JSONResponse(status_code=200, content=payload)