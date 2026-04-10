from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

import pymysql
from pymysql.cursors import DictCursor

from qwire_mock.config import load_config
from qwire_mock.schemas import OrderRequest, OrderResponse, ProductResponse

ORDER_TABLE = "`order`"
ORDER_PRODUCT_TABLE = "order_product"


@dataclass
class TransitionTarget:
    reference: UUID
    callback_url: str
    target_status: str


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
        return f"{value[:6]}{'*' * (len(value) - 10)}{value[-4:]}"
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
                CREATE TABLE IF NOT EXISTS {ORDER_TABLE} (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    mid VARCHAR(10) NOT NULL,
                    reference VARCHAR(36) NOT NULL UNIQUE,
                    order_id VARCHAR(64) UNIQUE,
                    name VARCHAR(255) NOT NULL,
                    amount DOUBLE NOT NULL,
                    currency VARCHAR(16) NOT NULL,
                    status VARCHAR(32) NOT NULL,
                    card_number VARCHAR(64) NOT NULL,
                    fail_reason VARCHAR(255) DEFAULT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    callback_url VARCHAR(512) NOT NULL,
                    )
                """
            )
            cursor.execute(f"SHOW COLUMNS FROM {ORDER_TABLE} LIKE 'mid'")
            has_mid = cursor.fetchone() is not None
            if not has_mid:
                cursor.execute(f"ALTER TABLE {ORDER_TABLE} ADD COLUMN mid VARCHAR(10) NOT NULL DEFAULT 'UNKNOWN'")
            cursor.execute(f"SHOW COLUMNS FROM {ORDER_TABLE} LIKE 'fail_reason'")
            has_fail_reason_snake = cursor.fetchone() is not None
            if not has_fail_reason_snake:
                cursor.execute(f"SHOW COLUMNS FROM {ORDER_TABLE} LIKE 'failReason'")
                has_fail_reason_camel = cursor.fetchone() is not None
                if has_fail_reason_camel:
                    cursor.execute(
                        f"ALTER TABLE {ORDER_TABLE} CHANGE failReason fail_reason VARCHAR(255) DEFAULT NULL"
                    )
                else:
                    cursor.execute(
                        f"ALTER TABLE {ORDER_TABLE} ADD COLUMN fail_reason VARCHAR(255) DEFAULT NULL"
                    )
            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {ORDER_PRODUCT_TABLE} (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    order_id INT NOT NULL,
                    product_id VARCHAR(64) NOT NULL,
                    count INT NOT NULL,
                    spec VARCHAR(128) NOT NULL,
                    status VARCHAR(32) NOT NULL,
                    FOREIGN KEY (order_id) REFERENCES {ORDER_TABLE}(id) ON DELETE CASCADE,
                    INDEX idx_v2_order_id (order_id)
                )
                """
            )
        conn.commit()
    finally:
        conn.close()


def exists(reference: UUID) -> bool:
    conn = _conn()
    try:
        with conn.cursor() as cursor:
            cursor.execute(f"SELECT 1 FROM {ORDER_TABLE} WHERE reference = %s LIMIT 1", (str(reference),))
            return cursor.fetchone() is not None
    finally:
        conn.close()

def create_order(request: OrderRequest, status: str, failReason: str | None = None) -> OrderResponse:
    conn = _conn()
    now = datetime.now(timezone.utc)
    masked_card = mask_card(request.cardNumber)
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                f"""
                INSERT INTO {ORDER_TABLE} (
                    reference, name, callback_url, mid, card_number, amount, currency, status, fail_reason
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    str(request.reference),
                    request.name,
                    request.callback,
                    request.mid,
                    masked_card,
                    float(request.amount),
                    request.currency,
                    status,
                    failReason,
                ),
            )
            row_id = cursor.lastrowid
            order_id = f"PX{row_id}"
            cursor.execute(f"UPDATE {ORDER_TABLE} SET order_id = %s WHERE id = %s", (order_id, row_id))

            product_status = "FAIL" if status == "FAIL" else "PROCESSING"
            for product in request.products:
                cursor.execute(
                    f"""
                    INSERT INTO {ORDER_PRODUCT_TABLE} (order_id, product_id, count, spec, status)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (row_id, product.productId, product.count, product.spec, product_status),
                )

        conn.commit()
    finally:
        conn.close()

    return OrderResponse(
        reference=request.reference,
        orderId=order_id,
        name=request.name,
        mid=request.mid,
        orderDate=now,
        amount=float(request.amount),
        currency=request.currency,
        status=status,
        cardNumber=masked_card,
        products=[
            ProductResponse(
                productId=product.productId,
                count=product.count,
                spec=product.spec,
                status="FAIL" if status == "FAIL" else "PROCESSING",
            )
            for product in request.products
        ],
        failReason=failReason if status == "FAIL" else None,
    )


def _map_row_to_order(order_row: dict, product_rows: list[dict]) -> OrderResponse:
    return OrderResponse(
        reference=UUID(order_row["reference"]),
        orderId=order_row["order_id"],
        name=order_row["name"],
        mid=order_row["mid"],
        orderDate=order_row["created_at"],
        amount=float(order_row["amount"]),
        currency=order_row["currency"],
        status=order_row["status"],
        cardNumber=order_row["card_number"],
        products=[
            ProductResponse(
                productId=row["product_id"],
                count=int(row["count"]),
                spec=row["spec"],
                status=row["status"],
            )
            for row in product_rows
        ],
        failReason=(order_row.get("failReason") or order_row.get("fail_reason")) if order_row["status"] == "FAIL" else None,
    )


def get_order(reference: UUID) -> OrderResponse | None:
    conn = _conn()
    try:
        with conn.cursor() as cursor:
            cursor.execute(f"SELECT * FROM {ORDER_TABLE} WHERE reference = %s", (str(reference),))
            order_row = cursor.fetchone()
            if not order_row:
                return None
            cursor.execute(
                f"SELECT product_id, count, spec, status FROM {ORDER_PRODUCT_TABLE} WHERE order_id = %s ORDER BY id",
                (order_row["id"],),
            )
            product_rows = cursor.fetchall()
            return _map_row_to_order(order_row, product_rows)
    finally:
        conn.close()


def get_callback_info(reference: UUID) -> tuple[str, float] | None:
    conn = _conn()
    try:
        with conn.cursor() as cursor:
            cursor.execute(f"SELECT callback_url, amount FROM {ORDER_TABLE} WHERE reference = %s", (str(reference),))
            row = cursor.fetchone()
            if row is None:
                return None
            return row["callback_url"], float(row["amount"])
    finally:
        conn.close()


def db_now() -> datetime:
    conn = _conn()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT NOW() AS now")
            row = cursor.fetchone()
            return row["now"]
    finally:
        conn.close()


def apply_scheduled_transitions(min_created_at: datetime | None = None) -> list[TransitionTarget]:
    transitions: list[TransitionTarget] = []
    conn = _conn()
    try:
        with conn.cursor() as cursor:
            min_created_clause = ""
            min_created_params: tuple = ()
            if min_created_at is not None:
                min_created_clause = " AND created_at >= %s"
                min_created_params = (min_created_at,)

            cursor.execute(
                f"""
                SELECT reference, callback_url
                FROM {ORDER_TABLE}
                WHERE status = 'SUCCESS' AND created_at <= NOW() - INTERVAL 30 SECOND
                {min_created_clause}
                """,
                min_created_params,
            )
            to_shipped = cursor.fetchall()
            if to_shipped:
                refs = [row["reference"] for row in to_shipped]
                cursor.executemany(
                    f"""
                    UPDATE {ORDER_PRODUCT_TABLE} p
                    JOIN {ORDER_TABLE} o ON p.order_id = o.id
                    SET p.status = 'SHIPPED'
                    WHERE o.reference = %s AND p.status = 'PROCESSING'
                    """,
                    [(ref,) for ref in refs],
                )
                transitions.extend(
                    [
                        TransitionTarget(reference=UUID(row["reference"]), callback_url=row["callback_url"], target_status="SHIPPED")
                        for row in to_shipped
                    ]
                )

            cursor.execute(
                f"""
                SELECT reference, callback_url
                FROM {ORDER_TABLE}
                WHERE status = 'SUCCESS' AND created_at <= NOW() - INTERVAL 60 SECOND
                {min_created_clause}
                """,
                min_created_params,
            )
            to_delivered = cursor.fetchall()
            if to_delivered:
                refs = [row["reference"] for row in to_delivered]
                cursor.executemany(
                    f"""
                    UPDATE {ORDER_PRODUCT_TABLE} p
                    JOIN {ORDER_TABLE} o ON p.order_id = o.id
                    SET p.status = 'DELIVERED'
                    WHERE o.reference = %s AND p.status IN ('PROCESSING', 'SHIPPED')
                    """,
                    [(ref,) for ref in refs],
                )
                transitions.extend(
                    [
                        TransitionTarget(reference=UUID(row["reference"]), callback_url=row["callback_url"], target_status="DELIVERED")
                        for row in to_delivered
                    ]
                )

            cursor.execute(
                f"""
                SELECT o.reference, o.callback_url
                FROM {ORDER_TABLE} o
                WHERE o.status = 'SUCCESS'
                {"AND o.created_at >= %s" if min_created_at is not None else ""}
                  AND EXISTS (
                    SELECT 1 FROM {ORDER_PRODUCT_TABLE} p WHERE p.order_id = o.id
                  )
                  AND NOT EXISTS (
                    SELECT 1 FROM {ORDER_PRODUCT_TABLE} p WHERE p.order_id = o.id AND p.status != 'DELIVERED'
                  )
                """,
                min_created_params,
            )
            to_completed = cursor.fetchall()
            if to_completed:
                refs = [row["reference"] for row in to_completed]
                cursor.executemany(f"UPDATE {ORDER_TABLE} SET status = 'COMPLETED' WHERE reference = %s", [(ref,) for ref in refs])
                transitions.extend(
                    [
                        TransitionTarget(reference=UUID(row["reference"]), callback_url=row["callback_url"], target_status="COMPLETED")
                        for row in to_completed
                    ]
                )

        conn.commit()
    finally:
        conn.close()
    return transitions


def clear_orders(reference: UUID | None = None) -> int:
    conn = _conn()
    try:
        with conn.cursor() as cursor:
            if reference is None:
                cursor.execute(f"DELETE FROM {ORDER_TABLE}")
            else:
                cursor.execute(f"DELETE FROM {ORDER_TABLE} WHERE reference = %s", (str(reference),))
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
