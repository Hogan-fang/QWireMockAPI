from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

import pymysql
from pymysql.cursors import DictCursor

from qwire_mock.config import load_config
from qwire_mock.schemas import (
    OrderCreateRequest,
    OrderCreateResponse,
    OrderQueryResponse,
    ProductQueryResponse,
)

ORDERS_TABLE = "orders"
ORDER_PRODUCTS_TABLE = "order_products"


@dataclass
class TransitionTarget:
    order_id: UUID
    reference: str
    merchant_id: str
    payment_status: str
    order_status: str
    finish_time: datetime
    callback_url: str


def _mysql_config() -> dict:
    mysql = load_config()["mysql"]
    return {
        "host": mysql["host"],
        "port": int(mysql["port"]),
        "user": mysql["user"],
        "password": mysql["password"],
        "database": mysql["database"],
        "charset": mysql.get("charset", "utf8mb4"),
        "cursorclass": DictCursor,
    }


def _conn(use_db: bool = True):
    kwargs = {**_mysql_config()}
    if not use_db:
        kwargs.pop("database", None)
    return pymysql.connect(**kwargs)


def mask_card(card_number: str) -> str:
    value = (card_number or "").strip()
    if len(value) >= 10:
        return f"{value[:6]}{'*' * 6}{value[-4:]}"
    if len(value) >= 4:
        return f"{value[:2]}{'*' * (len(value) - 4)}{value[-2:]}"
    return "*" * len(value)


def init_db() -> None:
    db_name = _mysql_config()["database"]
    conn = _conn(use_db=False)
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        conn.commit()
    finally:
        conn.close()

    conn = _conn(use_db=True)
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {ORDERS_TABLE} (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    order_id CHAR(36) NOT NULL UNIQUE,
                    reference VARCHAR(64) NOT NULL,
                    merchant_id VARCHAR(32) NOT NULL,
                    amount DECIMAL(18,2) NOT NULL,
                    currency VARCHAR(8) NOT NULL,
                    payment_status VARCHAR(16) NOT NULL,
                    order_status VARCHAR(16) NOT NULL,
                    card_number_masked VARCHAR(32) NOT NULL,
                    fail_reason VARCHAR(255) DEFAULT NULL,
                    callback_url VARCHAR(512) NOT NULL,
                    create_time DATETIME(3) NOT NULL,
                    finish_time DATETIME(3) DEFAULT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    UNIQUE KEY uq_orders_merchant_reference (merchant_id, reference),
                    KEY idx_orders_reference (reference),
                    KEY idx_orders_created_time (create_time)
                )
                """
            )
            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {ORDER_PRODUCTS_TABLE} (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    order_pk BIGINT NOT NULL,
                    sku VARCHAR(64) NOT NULL,
                    name VARCHAR(128) NOT NULL,
                    quantity INT NOT NULL,
                    unit_price DECIMAL(18,2) NOT NULL,
                    amount DECIMAL(18,2) NOT NULL,
                    CONSTRAINT fk_order_products_order FOREIGN KEY (order_pk) REFERENCES {ORDERS_TABLE}(id) ON DELETE CASCADE,
                    KEY idx_order_products_order_pk (order_pk)
                )
                """
            )
        conn.commit()
    finally:
        conn.close()


def exists(merchant_id: str, reference: str) -> bool:
    conn = _conn()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                f"SELECT 1 FROM {ORDERS_TABLE} WHERE merchant_id = %s AND reference = %s LIMIT 1",
                (merchant_id, reference),
            )
            return cursor.fetchone() is not None
    finally:
        conn.close()


def create_order(
    request: OrderCreateRequest,
    callback_url: str,
    payment_status: str,
    order_status: str,
    fail_reason: str | None = None,
) -> OrderCreateResponse:
    conn = _conn()
    order_id = uuid4()
    create_time = datetime.now(timezone.utc)
    finish_time = create_time
    masked_card = mask_card(request.cardNumber)
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                f"""
                INSERT INTO {ORDERS_TABLE} (
                    order_id, reference, merchant_id, amount, currency, payment_status, order_status,
                    card_number_masked, fail_reason, callback_url, create_time, finish_time
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    str(order_id),
                    request.reference,
                    request.merchantId,
                    Decimal(str(request.amount)),
                    request.currency,
                    payment_status,
                    order_status,
                    masked_card,
                    fail_reason,
                    callback_url,
                    create_time,
                    finish_time,
                ),
            )
            order_pk = cursor.lastrowid
            for item in request.products:
                cursor.execute(
                    f"""
                    INSERT INTO {ORDER_PRODUCTS_TABLE} (order_pk, sku, name, quantity, unit_price, amount)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        order_pk,
                        item.sku,
                        item.sku,
                        int(item.quantity),
                        Decimal(str(item.unitPrice)),
                        Decimal(str(item.amount)),
                    ),
                )
        conn.commit()
    finally:
        conn.close()

    return OrderCreateResponse(
        orderId=order_id,
        reference=request.reference,
        merchantId=request.merchantId,
        amount=float(request.amount),
        currency=request.currency,
        paymentStatus=payment_status,
        createTime=create_time,
        finishTime=finish_time,
        failReason=fail_reason,
    )


def _to_query_response(order_row: dict, product_rows: list[dict]) -> OrderQueryResponse:
    return OrderQueryResponse(
        orderId=UUID(order_row["order_id"]),
        reference=order_row["reference"],
        merchantId=order_row["merchant_id"],
        amount=float(order_row["amount"]),
        currency=order_row["currency"],
        cardNumber=order_row["card_number_masked"],
        paymentStatus=order_row["payment_status"],
        orderStatus=order_row["order_status"],
        products=[
            ProductQueryResponse(
                sku=row["sku"],
                name=row["name"],
                quantity=int(row["quantity"]),
                unitPrice=float(row["unit_price"]),
                amount=float(row["amount"]),
            )
            for row in product_rows
        ],
        failReason=order_row.get("fail_reason") if order_row["payment_status"] == "FAILED" else None,
    )


def get_order(merchant_id: str, reference: str | None = None, order_id: UUID | None = None) -> OrderQueryResponse | None:
    if (reference is None and order_id is None) or (reference is not None and order_id is not None):
        raise ValueError("Exactly one of reference or order_id is required")

    conn = _conn()
    try:
        with conn.cursor() as cursor:
            if reference is not None:
                cursor.execute(
                    f"SELECT * FROM {ORDERS_TABLE} WHERE merchant_id = %s AND reference = %s LIMIT 1",
                    (merchant_id, reference),
                )
            else:
                cursor.execute(
                    f"SELECT * FROM {ORDERS_TABLE} WHERE merchant_id = %s AND order_id = %s LIMIT 1",
                    (merchant_id, str(order_id)),
                )
            order_row = cursor.fetchone()
            if order_row is None:
                return None
            cursor.execute(
                f"SELECT sku, name, quantity, unit_price, amount FROM {ORDER_PRODUCTS_TABLE} WHERE order_pk = %s ORDER BY id",
                (order_row["id"],),
            )
            product_rows = cursor.fetchall()
            return _to_query_response(order_row, product_rows)
    finally:
        conn.close()


def get_callback_target(order_id: UUID) -> tuple[str, str, str, str, str, datetime] | None:
    conn = _conn()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT callback_url, reference, merchant_id, payment_status, order_status, finish_time
                FROM {ORDERS_TABLE}
                WHERE order_id = %s
                """,
                (str(order_id),),
            )
            row = cursor.fetchone()
            if row is None:
                return None
            return (
                row["callback_url"],
                row["reference"],
                row["merchant_id"],
                row["payment_status"],
                row["order_status"],
                row["finish_time"],
            )
    finally:
        conn.close()


def apply_scheduled_transitions(min_create_time: datetime | None = None) -> list[TransitionTarget]:
    transitions: list[TransitionTarget] = []
    conn = _conn()
    try:
        with conn.cursor() as cursor:
            where_extra = ""
            params: list = []
            if min_create_time is not None:
                where_extra = " AND create_time >= %s"
                params.append(min_create_time)

            cursor.execute(
                f"""
                SELECT order_id, reference, merchant_id, callback_url
                FROM {ORDERS_TABLE}
                WHERE payment_status = 'PAID' AND order_status = 'PROCESSING'
                  AND create_time <= NOW() - INTERVAL 30 SECOND
                  {where_extra}
                """,
                tuple(params),
            )
            rows = cursor.fetchall()
            if rows:
                ids = [(row["order_id"],) for row in rows]
                cursor.executemany(
                    f"""
                    UPDATE {ORDERS_TABLE}
                    SET order_status = 'DELIVERED', finish_time = NOW(3)
                    WHERE order_id = %s
                    """,
                    ids,
                )
                for row in rows:
                    transitions.append(
                        TransitionTarget(
                            order_id=UUID(row["order_id"]),
                            reference=row["reference"],
                            merchant_id=row["merchant_id"],
                            payment_status="PAID",
                            order_status="DELIVERED",
                            finish_time=datetime.now(timezone.utc),
                            callback_url=row["callback_url"],
                        )
                    )

        conn.commit()
    finally:
        conn.close()

    return transitions


def db_now() -> datetime:
    conn = _conn()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT NOW() AS now")
            row = cursor.fetchone()
            return row["now"]
    finally:
        conn.close()


def clear_orders(reference: str | None = None, merchant_id: str | None = None) -> int:
    conn = _conn()
    try:
        with conn.cursor() as cursor:
            if reference is None:
                cursor.execute(f"DELETE FROM {ORDERS_TABLE}")
            elif merchant_id is not None:
                cursor.execute(
                    f"DELETE FROM {ORDERS_TABLE} WHERE merchant_id = %s AND reference = %s",
                    (merchant_id, reference),
                )
            else:
                cursor.execute(f"DELETE FROM {ORDERS_TABLE} WHERE reference = %s", (reference,))
            affected = cursor.rowcount
        conn.commit()
        return affected
    finally:
        conn.close()


def count_rows(table_name: str) -> int:
    conn = _conn()
    try:
        with conn.cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) AS c FROM {table_name}")
            row = cursor.fetchone()
            return int(row["c"])
    finally:
        conn.close()
