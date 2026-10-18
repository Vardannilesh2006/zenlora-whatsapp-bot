import sqlite3
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), "zenos.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # 1. Orders Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_ref TEXT UNIQUE,
        customer_name TEXT,
        phone TEXT,
        product_name TEXT,
        amount INTEGER DEFAULT 349,
        prepaid_amount INTEGER DEFAULT 297,
        discount_amount INTEGER DEFAULT 52,
        address TEXT DEFAULT '',
        pincode TEXT DEFAULT '',
        city TEXT DEFAULT '',
        state TEXT DEFAULT '',
        status TEXT DEFAULT 'PENDING_VERIFICATION',
        rto_risk_score INTEGER DEFAULT 95,
        razorpay_link TEXT DEFAULT '',
        wukusy_status TEXT DEFAULT 'READY_TO_SYNC',
        wukusy_order_id TEXT DEFAULT '',
        tracking_awb TEXT DEFAULT '',
        courier_name TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 2. Messages & Chat History
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone TEXT,
        customer_name TEXT,
        direction TEXT, -- INBOUND or OUTBOUND
        message_type TEXT, -- TEXT, INTERACTIVE, BUTTON_REPLY
        body TEXT,
        button_id TEXT DEFAULT '',
        wa_message_id TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 3. System & Error Logs Stream
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS system_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        level TEXT, -- INFO, SUCCESS, WARNING, ERROR
        source TEXT, -- SMARTBIZ, WHATSAPP, RAZORPAY, WUKUSY, SYSTEM
        message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()
    logger.info("ZenOS SQLite Database initialized successfully.")

def log_event(level, source, message):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO system_logs (level, source, message) VALUES (?, ?, ?)", (level, source, message))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error logging event: {e}")

def save_or_update_order(order_data):
    try:
        conn = get_db()
        cursor = conn.cursor()
        order_ref = order_data.get("order_ref", f"ZEN-{order_data.get('order_id', '1001')}")
        
        # Calculate address risk score
        address = order_data.get("address", "")
        pincode = str(order_data.get("pincode", ""))
        score = 95
        if len(address) < 15:
            score -= 25
        if not any(c.isdigit() for c in address):
            score -= 15
        if len(pincode) != 6:
            score -= 20
        if score < 20:
            score = 20

        amount = int(order_data.get("amount", 349))
        savings = round(amount * 0.15)
        prepaid = amount - savings

        cursor.execute("""
        INSERT INTO orders (
            order_ref, customer_name, phone, product_name, amount, prepaid_amount, discount_amount,
            address, pincode, city, state, status, rto_risk_score, razorpay_link, wukusy_status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(order_ref) DO UPDATE SET
            customer_name = excluded.customer_name,
            phone = excluded.phone,
            product_name = excluded.product_name,
            amount = excluded.amount,
            address = CASE WHEN excluded.address != '' THEN excluded.address ELSE orders.address END,
            pincode = CASE WHEN excluded.pincode != '' THEN excluded.pincode ELSE orders.pincode END,
            status = CASE WHEN excluded.status != '' THEN excluded.status ELSE orders.status END,
            updated_at = CURRENT_TIMESTAMP
        """, (
            order_ref,
            order_data.get("customer_name", "Valued Customer"),
            order_data.get("phone", ""),
            order_data.get("product_name", "Zenlora Lifestyle Item"),
            amount,
            prepaid,
            savings,
            address,
            pincode,
            order_data.get("city", ""),
            order_data.get("state", ""),
            order_data.get("status", "PENDING_VERIFICATION"),
            score,
            order_data.get("razorpay_link", ""),
            order_data.get("wukusy_status", "READY_TO_SYNC")
        ))
        conn.commit()
        conn.close()
        log_event("SUCCESS", "SMARTBIZ", f"Order {order_ref} ({order_data.get('customer_name')}, ₹{amount}) synced to ZenOS.")
        return True
    except Exception as e:
        logger.error(f"Error saving order: {e}")
        log_event("ERROR", "DATABASE", f"Failed to save order {order_data.get('order_ref')}: {str(e)}")
        return False

def update_order_status(phone_or_ref, new_status, extra_fields=None):
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        clean_phone = str(phone_or_ref).replace("+", "").replace(" ", "").replace("-", "")
        if len(clean_phone) == 10:
            clean_phone = f"91{clean_phone}"

        set_clause = "status = ?, updated_at = CURRENT_TIMESTAMP"
        params = [new_status]

        if extra_fields:
            for k, v in extra_fields.items():
                set_clause += f", {k} = ?"
                params.append(v)

        params.extend([phone_or_ref, clean_phone, f"%{clean_phone[-10:]}%"])
        cursor.execute(f"""
        UPDATE orders 
        SET {set_clause}
        WHERE order_ref = ? OR phone = ? OR phone LIKE ?
        """, params)

        conn.commit()
        conn.close()
        log_event("INFO", "ORDER_STATUS", f"Order for {phone_or_ref} updated to status: {new_status}")
        return True
    except Exception as e:
        logger.error(f"Error updating order status: {e}")
        return False

def record_message(phone, customer_name, direction, message_type, body, button_id="", wa_message_id=""):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO messages (phone, customer_name, direction, message_type, body, button_id, wa_message_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (phone, customer_name, direction, message_type, body, button_id, wa_message_id))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error recording message: {e}")

def get_dashboard_data():
    conn = get_db()
    cursor = conn.cursor()

    # 1. KPIs
    cursor.execute("SELECT COUNT(*) as total_orders FROM orders")
    total_orders = cursor.fetchone()["total_orders"]

    cursor.execute("SELECT COUNT(*) as prepaid_count FROM orders WHERE status = 'PREPAID_PAID'")
    prepaid_count = cursor.fetchone()["prepaid_count"]

    cursor.execute("SELECT COUNT(*) as cod_confirmed FROM orders WHERE status = 'CONFIRMED_COD'")
    cod_confirmed = cursor.fetchone()["cod_confirmed"]

    cursor.execute("SELECT COUNT(*) as ofd_count FROM orders WHERE status IN ('OUT_FOR_DELIVERY', 'DELIVERY_COLLECT_CONFIRMED')")
    ofd_count = cursor.fetchone()["ofd_count"]

    cursor.execute("SELECT COUNT(*) as cancelled_count FROM orders WHERE status = 'CANCELLED'")
    cancelled_count = cursor.fetchone()["cancelled_count"]

    cursor.execute("SELECT SUM(amount) as total_gmv FROM orders WHERE status != 'CANCELLED'")
    gmv_row = cursor.fetchone()
    total_gmv = gmv_row["total_gmv"] or 0

    # 2. Recent Orders
    cursor.execute("SELECT * FROM orders ORDER BY id DESC LIMIT 50")
    orders = [dict(row) for row in cursor.fetchall()]

    # 3. System Logs
    cursor.execute("SELECT * FROM system_logs ORDER BY id DESC LIMIT 30")
    logs = [dict(row) for row in cursor.fetchall()]

    conn.close()

    prepaid_ratio = round((prepaid_count / total_orders * 100), 1) if total_orders > 0 else 0
    saved_rto_loss = cancelled_count * 90 # Approx Rs 90 forward/reverse courier loss saved per cancelled package

    return {
        "kpis": {
            "total_orders": total_orders,
            "prepaid_count": prepaid_count,
            "prepaid_ratio": f"{prepaid_ratio}%",
            "cod_confirmed": cod_confirmed,
            "ofd_count": ofd_count,
            "cancelled_count": cancelled_count,
            "saved_rto_loss": f"₹{saved_rto_loss}",
            "total_gmv": f"₹{total_gmv}"
        },
        "orders": orders,
        "logs": logs
    }
