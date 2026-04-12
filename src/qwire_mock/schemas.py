from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

OrderStatus = Literal["SUCCESS", "COMPLETED", "FAIL"]
ProductStatus = Literal["PROCESSING", "SHIPPED", "DELIVERED", "FAIL"]


class ProductRequest(BaseModel):
    productId: str
    count: int = Field(..., ge=0, le=100)
    spec: str


class ProductResponse(BaseModel):
    productId: str
    count: int = Field(..., ge=0, le=100)
    spec: str
    status: ProductStatus


class OrderRequest(BaseModel):
    reference: UUID
    name: str
    callback: str
    mid: str = Field(..., max_length=10)
    signature: str
    cardNumber: str
    cvv: str
    expiry: str
    amount: float
    currency: str
    products: list[ProductRequest]


class OrderResponse(BaseModel):
    reference: UUID
    orderId: str
    name: str
    mid: str = Field(..., max_length=10)
    orderDate: datetime
    amount: float
    currency: str
    status: OrderStatus
    cardNumber: str
    products: list[ProductResponse]
    failReason: str | None = None


class Received(BaseModel):
    message: str = "OK"
