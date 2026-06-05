import mysql.connector
import os
import datetime
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    conn = mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", 3306)),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE", "customer_support")
    )
    return conn

def get_customer(customer_id: str) -> dict:
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM customers WHERE customer_id = %s", (customer_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if row:
        return row
    return {"error": f"Customer {customer_id} not found"}

def lookup_order(order_id: str) -> dict:
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM orders WHERE order_id = %s", (order_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if row:
        # Convert date object to string for JSON serialization
        if row.get("created_at"):
            row["created_at"] = str(row["created_at"])
        return row
    return {"error": f"Order {order_id} not found"}

def process_refund(order_id: str, amount: float) -> dict:
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Check order exists
    cursor.execute("SELECT * FROM orders WHERE order_id = %s", (order_id,))
    order = cursor.fetchone()
    if not order:
        cursor.close()
        conn.close()
        return {"error": f"Order {order_id} not found"}

    refund_id = f"REF-{order_id[-3:]}-NEW"
    created_at = datetime.datetime.now().strftime("%Y-%m-%d")

    cursor.execute(
        """INSERT INTO refunds (refund_id, order_id, amount, status, created_at)
           VALUES (%s, %s, %s, %s, %s)
           ON DUPLICATE KEY UPDATE amount=VALUES(amount), status=VALUES(status)""",
        (refund_id, order_id, amount, "approved", created_at)
    )
    conn.commit()
    cursor.close()
    conn.close()

    return {
        "refund_id": refund_id,
        "order_id": order_id,
        "amount": amount,
        "status": "approved",
        "created_at": created_at
    }

def escalate_to_human(customer_id: str, reason: str) -> dict:
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    escalation_id = f"ESC-NEW-{customer_id[-3:]}"
    created_at = datetime.datetime.now().strftime("%Y-%m-%d")

    cursor.execute(
        """INSERT INTO escalations (escalation_id, customer_id, reason, status, created_at)
           VALUES (%s, %s, %s, %s, %s)
           ON DUPLICATE KEY UPDATE reason=VALUES(reason), status=VALUES(status)""",
        (escalation_id, customer_id, reason, "open", created_at)
    )
    conn.commit()
    cursor.close()
    conn.close()

    return {
        "escalation_id": escalation_id,
        "customer_id": customer_id,
        "reason": reason,
        "status": "open",
        "created_at": created_at
    }