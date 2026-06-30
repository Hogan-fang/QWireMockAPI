from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

PaymentStatus = Literal["PROCESSING", "PAID", "FAILED", "TIMEOUT"]
OrderStatus = Literal["PROCESSING", "DELIVERED"]


class ProductRequest(BaseModel):
    sku: str
    quantity: int = Field(..., ge=1)
    unitPrice: float = Field(..., ge=0)
    amount: float = Field(..., ge=0)


class ProductQueryResponse(BaseModel):
    sku: str
    name: str
    quantity: int = Field(..., ge=1)
    unitPrice: float = Field(..., ge=0)
    amount: float = Field(..., ge=0)


class OrderCreateRequest(BaseModel):
    reference: str
    merchantId: str
    amount: float = Field(..., ge=0)
    currency: str
    status: str | None = None
    paymentStatus: str | None = None
    cardholderName: str
    cardNumber: str
    cvv: str
    expiry: str
    products: list[ProductRequest] = Field(..., min_length=1)


class OrderCreateResponse(BaseModel):
    orderId: UUID
    reference: str
    merchantId: str
    amount: float
    currency: str
    paymentStatus: PaymentStatus
    createTime: datetime
    finishTime: datetime | None = None
    failReason: str | None = None


class OrderQueryResponse(BaseModel):
    orderId: UUID
    reference: str
    merchantId: str
    amount: float
    currency: str
    cardNumber: str
    paymentStatus: PaymentStatus
    orderStatus: OrderStatus
    products: list[ProductQueryResponse]
    failReason: str | None = None


class CallbackAckResponse(BaseModel):
    status: Literal["SUCCESS"] = "SUCCESS"


class OrderCallbackRequest(BaseModel):
    orderId: UUID
    reference: str
    merchantId: str
    paymentStatus: PaymentStatus
    orderStatus: OrderStatus
    finishTime: datetime


class OrderCallbackQueryResponse(BaseModel):
    callbackId: UUID
    callbackTime: datetime
    orderId: UUID
    reference: str
    merchantId: str
    paymentStatus: PaymentStatus
    orderStatus: OrderStatus
