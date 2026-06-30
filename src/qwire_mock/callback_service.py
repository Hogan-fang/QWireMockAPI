import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from qwire_mock.config import load_config
from qwire_mock.schemas import CallbackAckResponse, OrderCallbackQueryResponse, OrderCallbackRequest

logger = logging.getLogger(__name__)
CONFIG = load_config()
LOGGING_CONFIG = CONFIG["logging"]

_callback_store: dict[str, OrderCallbackQueryResponse] = {}


def _ensure_file_logger() -> None:
    logger.setLevel(logging.INFO)
    callback_log_path = LOGGING_CONFIG["callback_log"]
    existing = [
        handler
        for handler in logger.handlers
        if isinstance(handler, logging.FileHandler)
        and os.path.basename(getattr(handler, "baseFilename", "")) == os.path.basename(callback_log_path)
    ]
    if existing:
        return

    file_handler = logging.FileHandler(callback_log_path, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    logger.addHandler(file_handler)


_ensure_file_logger()


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("callback service startup")
    try:
        yield
    finally:
        logger.info("callback service shutdown")


app = FastAPI(title="QWire Merchant Callback API v3", version="3.0.0", lifespan=lifespan)


def _json(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, default=str)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_: Request, __: RequestValidationError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": "Invalid request"})


@app.post("/callback")
def callback(body: OrderCallbackRequest):
    record = OrderCallbackQueryResponse(
        callbackId=uuid4(),
        callbackTime=datetime.now(timezone.utc),
        orderId=body.orderId,
        reference=body.reference,
        merchantId=body.merchantId,
        paymentStatus=body.paymentStatus,
        orderStatus=body.orderStatus,
    )
    _callback_store[str(body.orderId)] = record
    logger.info("POST /callback request:\n%s", _json(body.model_dump(mode="json")))
    logger.info("POST /callback stored:\n%s", _json(record.model_dump(mode="json")))
    response = CallbackAckResponse(status="SUCCESS")
    return JSONResponse(status_code=200, content=response.model_dump(mode="json"))


@app.get("/callback/latest")
def latest_callback(orderId: str = Query(...)):
    try:
        order_uuid = UUID(orderId)
    except ValueError:
        return JSONResponse(status_code=422, content={"detail": "Invalid request"})

    key = str(order_uuid)
    record = _callback_store.get(key)
    if record is None:
        return JSONResponse(status_code=404, content={"detail": "Callback not found."})

    payload = record.model_dump(mode="json")
    logger.info("GET /callback/latest response:\n%s", _json(payload))
    _callback_store.pop(key, None)
    return JSONResponse(status_code=200, content=payload)