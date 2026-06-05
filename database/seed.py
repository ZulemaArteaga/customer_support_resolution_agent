import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", 3306)),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE", "customer_support")
    )

def init_db():
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    conn = get_connection()
    cursor = conn.cursor()

    # Read and execute schema — run each statement separately
    with open(schema_path, "r") as f:
        schema = f.read()

    for statement in schema.split(";"):
        statement = statement.strip()
        if statement:
            cursor.execute(statement)

    # Customers
    customers = [
        ("CUST-001", "Zulema", "zulema@example.com", "active"),
        ("CUST-002", "Zulema Arteaga", "zulemaarteaga@example.com", "active"),
        ("CUST-003", "Example No1", "exampl3@example.com", "inactive"),
        ("CUST-004", "Example No2", "example2@example.com", "active"),
    ]
    cursor.executemany(
        """INSERT INTO customers (customer_id, name, email, status)
           VALUES (%s, %s, %s, %s)
           ON DUPLICATE KEY UPDATE name=VALUES(name), email=VALUES(email), status=VALUES(status)""",
        customers
    )

    # Orders
    orders = [
        ("ORD-001", "CUST-001", "Wireless Headphones", 89.99, "delivered", "2025-05-01"),
        ("ORD-002", "CUST-001", "Phone Case", 19.99, "delivered", "2025-05-10"),
        ("ORD-003", "CUST-002", "Laptop Stand", 45.00, "delivered", "2025-05-15"),
        ("ORD-004", "CUST-003", "Keyboard", 120.00, "cancelled", "2025-05-18"),
        ("ORD-005", "CUST-004", "Monitor", 1200.00, "delivered", "2025-05-20"),
    ]
    cursor.executemany(
        """INSERT INTO orders (order_id, customer_id, product, amount, status, created_at)
           VALUES (%s, %s, %s, %s, %s, %s)
           ON DUPLICATE KEY UPDATE product=VALUES(product), amount=VALUES(amount),
           status=VALUES(status), created_at=VALUES(created_at)""",
        orders
    )

    # Refunds
    refunds = [
        ("REF-001", "ORD-002", 19.99, "approved", "2025-05-12"),
        ("REF-002", "ORD-004", 120.00, "pending", "2025-05-19"),
        ("REF-003", "ORD-003", 45.00, "rejected", "2025-05-16"),
    ]
    cursor.executemany(
        """INSERT INTO refunds (refund_id, order_id, amount, status, created_at)
           VALUES (%s, %s, %s, %s, %s)
           ON DUPLICATE KEY UPDATE amount=VALUES(amount), status=VALUES(status)""",
        refunds
    )

    # Escalations
    escalations = [
        ("ESC-001", "CUST-003", "Refund rejected, customer disputing", "open", "2025-05-17"),
        ("ESC-002", "CUST-002", "Order not received after 30 days", "resolved", "2025-05-20"),
    ]
    cursor.executemany(
        """INSERT INTO escalations (escalation_id, customer_id, reason, status, created_at)
           VALUES (%s, %s, %s, %s, %s)
           ON DUPLICATE KEY UPDATE reason=VALUES(reason), status=VALUES(status)""",
        escalations
    )

    conn.commit()
    cursor.close()
    conn.close()
    print("Database initialized and seeded successfully.")

if __name__ == "__main__":
    init_db()