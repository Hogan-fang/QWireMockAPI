import json
import logging
import os
from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from qwire_mock.config import load_config
from qwire_mock.schemas import OrderResponse, Received

logger = logging.getLogger(__name__)
CONFIG = load_config()
LOGGING_CONFIG = CONFIG["logging"]

# In-memory callback store: reference (str) -> latest OrderResponse
_callback_store: dict[str, OrderResponse] = {}


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


app = FastAPI(title="QWire Callback API v2", version="2.0.0", lifespan=lifespan)


def _json(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, default=str)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    logger.warning("Invalid callback payload: path=%s errors=%s", request.url.path, exc.errors())
    return JSONResponse(
        status_code=400,
        content={
            "code": "invalid_request",
            "detail": "Invalid order payload",
        },
    )


@app.post("/callback", response_model=Received)
def callback(body: OrderResponse) -> Received:
    payload = body.model_dump(mode="json")
    logger.info("POST /callback request:\n%s", _json(payload))

    _callback_store[str(body.reference)] = body
    logger.info("POST /callback stored reference=%s", body.reference)

    response = Received(message="OK")
    logger.info("POST /callback response:\n%s", _json(response.model_dump(mode="json")))
    return response


@app.get("/check")
def check(reference: str = Query(..., description="Order reference (UUID)")):
    try:
        reference_uuid = UUID(reference)
    except ValueError:
        logger.warning("GET /check invalid UUID: reference=%s", reference)
        return JSONResponse(
            status_code=422,
            content={"code": "invalid_reference", "detail": "Invalid UUID format"},
        )

    key = str(reference_uuid)
    record = _callback_store.get(key)
    if record is None:
        logger.info("GET /check not found: reference=%s", reference_uuid)
        return JSONResponse(
            status_code=404,
            content={"code": "callback_not_found", "detail": "Callback record not found"},
        )

    payload = record.model_dump(mode="json")
    if record.failReason is None:
        payload.pop("failReason", None)
    logger.info("GET /check response:\n%s", _json(payload))
    return JSONResponse(status_code=200, content=payload)
