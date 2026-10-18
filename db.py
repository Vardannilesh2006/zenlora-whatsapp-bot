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
    seed_realistic_zenos_data(conn)
    conn.close()
    logger.info("ZenOS SQLite Database initialized and seeded successfully.")

def seed_realistic_zenos_data(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM orders")
    row = cursor.fetchone()
    if row and row["count"] >= 8:
        return # Already seeded

    # Seed realistic customer orders representing live Indian D2C fulfillment
    seed_orders = [
        (
            "ZEN-1005", "Nilesh Vardan", "919608837916",
            "Handcrafted Red Decorative Matki Kalash with Lid for Pooja and Home Decor Gift Set",
            349, 297, 52,
            "House No. 21, Green Park Colony, Near AIIMS Road, Phulwari Sharif",
            "800001", "Patna", "Bihar",
            "DELIVERY_COLLECT_CONFIRMED", 98,
            "https://rzp.io/rzp/gZgDGKoW", "SYNCED_DISPATCHED", "WUK-78912",
            "DEL982145019", "Delhivery Express",
            "2026-10-18 10:30:15"
        ),
        (
            "ZEN-1006", "Rohan Sharma", "919876543210",
            "2-in-1 Premium Glass Oil Dispenser & Vinegar Sprayer Bottle (500ml)",
            299, 254, 45,
            "Flat 402, Sai Residency, 12th Main, 4th Cross, Indiranagar",
            "560038", "Bengaluru", "Karnataka",
            "PREPAID_PAID", 99,
            "https://rzp.io/rzp/28twKzR", "SYNCED_DISPATCHED", "WUK-78913",
            "BLU481923012", "BlueDart Air",
            "2026-10-18 11:15:22"
        ),
        (
            "ZEN-1007", "Pooja Verma", "919811234567",
            "Handcrafted Red Decorative Matki Kalash with Glowing Diya Set",
            499, 424, 75,
            "B-142, Sector 62, Near Fortis Hospital, Noida",
            "201301", "Noida", "Uttar Pradesh",
            "CONFIRMED_COD", 94,
            "", "READY_TO_SYNC", "WUK-78914",
            "EKT719284102", "Ekart Logistics",
            "2026-10-18 11:42:10"
        ),
        (
            "ZEN-1008", "Amit Patel", "919920187654",
            "Multi-function 12-in-1 Vegetable & Fruit Chopper with Storage Container",
            399, 339, 60,
            "Row House 8, Shivalik Villa, Near Iscon Cross Road, Satellite",
            "380015", "Ahmedabad", "Gujarat",
            "PREPAID_PAID", 96,
            "https://rzp.io/rzp/Q4D13em", "SYNCED_DISPATCHED", "WUK-78915",
            "DEL339182471", "Delhivery Surface",
            "2026-10-18 12:05:44"
        ),
        (
            "ZEN-1009", "Sneha Reddy", "919740123456",
            "Floating Water Sensor LED Diyas for Festive Home Decor (Pack of 12)",
            249, 212, 37,
            "Plot 18, Road No. 10, Near City Center Mall, Banjara Hills",
            "500034", "Hyderabad", "Telangana",
            "OUT_FOR_DELIVERY", 95,
            "", "IN_TRANSIT", "WUK-78916",
            "SHD992140182", "Shadowfax Express",
            "2026-10-18 12:18:30"
        ),
        (
            "ZEN-1010", "Vikramaditya Chauhan", "919123456789",
            "Handcrafted Red Decorative Matki Kalash with Lid for Pooja",
            349, 297, 52,
            "4/128, Vibhuti Khand, Near Wave Mall, Gomti Nagar",
            "226010", "Lucknow", "Uttar Pradesh",
            "DELIVERY_RESCHEDULED", 89,
            "", "RESCHEDULED_TRANSIT", "WUK-78917",
            "DEL881920314", "Delhivery Express",
            "2026-10-18 12:35:12"
        ),
        (
            "ZEN-1011", "Kavita Sundaram", "919445123456",
            "Crystal Rose Diamond Touch Sensor LED Bedside Table Lamp (16 Colors)",
            599, 509, 90,
            "Door No. 15, North Usman Road, Opp. Panagal Park, T. Nagar",
            "600017", "Chennai", "Tamil Nadu",
            "PREPAID_PAID", 97,
            "https://rzp.io/rzp/HaI8ok1D", "SYNCED_DISPATCHED", "WUK-78918",
            "BLU552190342", "BlueDart Air",
            "2026-10-18 12:45:00"
        ),
        (
            "ZEN-1012", "Sunil Meena", "919312098765",
            "Wireless Portable USB Rechargeable Smoothie Blender Bottle (380ml)",
            449, 382, 67,
            "Village Rampur, Near Purana Kuan, Tehsil Lalsot",
            "303303", "Dausa", "Rajasthan",
            "RTO_RISK_HIGH", 38,
            "", "ON_HOLD_VERIFICATION", "",
            "", "Verification Required",
            "2026-10-18 12:48:19"
        ),
        (
            "ZEN-1013", "Deepak Mehta", "919820012345",
            "Automatic Rechargeable Drinking Water Bottle Dispenser Pump",
            299, 254, 45,
            "12B, Sea Face Enclave, B.G. Kher Marg, Malabar Hill",
            "400006", "Mumbai", "Maharashtra",
            "CANCELLED", 86,
            "", "CANCELLED_ABORTED", "",
            "", "Order Cancelled by Customer",
            "2026-10-18 12:50:55"
        ),
        (
            "ZEN-1014", "Ananya Sen", "919830167890",
            "Smart Motion Sensor Wireless Night LED Strip Light (Warm White)",
            349, 297, 52,
            "Tower 3, Flat 9A, Greenwood Heights, Action Area 1, New Town",
            "700156", "Kolkata", "West Bengal",
            "CONFIRMED_COD", 93,
            "", "READY_TO_SYNC", "WUK-78919",
            "DTD662910481", "DTDC Express",
            "2026-10-18 12:55:04"
        )
    ]

    for o in seed_orders:
        cursor.execute("""
        INSERT OR REPLACE INTO orders (
            order_ref, customer_name, phone, product_name, amount, prepaid_amount, discount_amount,
            address, pincode, city, state, status, rto_risk_score, razorpay_link, wukusy_status,
            wukusy_order_id, tracking_awb, courier_name, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, o)

    # Seed Customer-Centric Chat Messages
    seed_messages = [
        # Nilesh Vardan (+91 96088 37916)
        ("919608837916", "Nilesh Vardan", "OUTBOUND", "INTERACTIVE_ORDER", "Order #ZEN-1005 placed. 3-Button confirmation sent with 15% VIP discount.", "btn_pay_1005_349", "2026-10-18 10:30:16"),
        ("919608837916", "Nilesh Vardan", "INBOUND", "BUTTON_REPLY", "Clicked: ⚡ Pay & Save 15%", "btn_pay_1005_349", "2026-10-18 10:31:02"),
        ("919608837916", "Nilesh Vardan", "OUTBOUND", "TEXT", "Prepaid Privilege Unlocked! Tap below to pay ₹297 directly via PhonePe/GPay: https://rzp.io/rzp/gZgDGKoW", "", "2026-10-18 10:31:03"),
        ("919608837916", "Nilesh Vardan", "OUTBOUND", "INTERACTIVE_OFD", "Availability Check: Your zenlora.store order is out for delivery today. Security PIN: 159", "btn_collect_1005_349", "2026-10-18 12:00:15"),
        ("919608837916", "Nilesh Vardan", "INBOUND", "BUTTON_REPLY", "Clicked: 📦 I can collect", "btn_collect_1005_349", "2026-10-18 12:05:42"),
        ("919608837916", "Nilesh Vardan", "OUTBOUND", "TEXT", "🎉 Delivery Confirmed, Nilesh! Delivery executive notified that you are available today. Thank you for choosing Zenlora! 😊 — Team Zenlora 🛍️", "", "2026-10-18 12:05:43"),

        # Rohan Sharma (+91 98765 43210)
        ("919876543210", "Rohan Sharma", "OUTBOUND", "INTERACTIVE_ORDER", "Order #ZEN-1006 placed. Confirmation sent with 15% VIP discount.", "", "2026-10-18 11:15:23"),
        ("919876543210", "Rohan Sharma", "INBOUND", "BUTTON_REPLY", "Clicked: ⚡ Pay & Save 15%", "btn_pay_1006_299", "2026-10-18 11:16:05"),
        ("919876543210", "Rohan Sharma", "OUTBOUND", "TEXT", "Prepaid Privilege Unlocked! Tap link to pay ₹254 via UPI: https://rzp.io/rzp/28twKzR", "", "2026-10-18 11:16:06"),
        ("919876543210", "Rohan Sharma", "INBOUND", "TEXT", "Done! Paid via Google Pay. Please dispatch quickly.", "", "2026-10-18 11:17:40"),
        ("919876543210", "Rohan Sharma", "OUTBOUND", "TEXT", "Payment of ₹254 verified! Your order has been upgraded to Priority 24h Express Dispatch via BlueDart Air (AWB: BLU481923012). 😊 — Team Zenlora 🛍️", "", "2026-10-18 11:18:10"),

        # Pooja Verma (+91 98112 34567)
        ("919811234567", "Pooja Verma", "OUTBOUND", "INTERACTIVE_ORDER", "Order #ZEN-1007 placed. Confirmation sent.", "", "2026-10-18 11:42:11"),
        ("919811234567", "Pooja Verma", "INBOUND", "BUTTON_REPLY", "Clicked: ✅ Confirm COD", "btn_cod_1007", "2026-10-18 11:43:50"),
        ("919811234567", "Pooja Verma", "OUTBOUND", "TEXT", "✅ Order Confirmed for COD Delivery! Thank you, Pooja! Amount to collect: ₹499. Live tracking updates will follow shortly. 😊 — Team Zenlora 🛍️", "", "2026-10-18 11:43:51"),

        # Vikramaditya Chauhan (+91 91234 56789)
        ("919123456789", "Vikramaditya Chauhan", "OUTBOUND", "INTERACTIVE_OFD", "Availability Check: Your order is out for delivery today. Security PIN: 482", "", "2026-10-18 12:35:15"),
        ("919123456789", "Vikramaditya Chauhan", "INBOUND", "BUTTON_REPLY", "Clicked: 📅 Change the date", "btn_resched_1010_349", "2026-10-18 12:36:20"),
        ("919123456789", "Vikramaditya Chauhan", "OUTBOUND", "TEXT", "🗓️ Delivery Rescheduled! No worries, Vikramaditya! Delivery partner has rescheduled your delivery for Tomorrow. 😊 — Team Zenlora 🛍️", "", "2026-10-18 12:36:21"),

        # Deepak Mehta (+91 98200 12345)
        ("919820012345", "Deepak Mehta", "OUTBOUND", "INTERACTIVE_ORDER", "Order #ZEN-1013 confirmation sent.", "", "2026-10-18 12:50:56"),
        ("919820012345", "Deepak Mehta", "INBOUND", "BUTTON_REPLY", "Clicked: ❌ Cancel Order", "btn_cancel_1013", "2026-10-18 12:52:10"),
        ("919820012345", "Deepak Mehta", "OUTBOUND", "TEXT", "❌ Order Cancellation Confirmed. As a courtesy, here is 10% voucher VIPZEN10 for your next visit. 😊 — Team Zenlora 🛍️", "", "2026-10-18 12:52:11")
    ]

    for m in seed_messages:
        cursor.execute("""
        INSERT INTO messages (phone, customer_name, direction, message_type, body, button_id, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, m)

    # Seed realistic live system audit logs
    seed_logs = [
        ("SUCCESS", "RAZORPAY", "Payment captured ₹297 via PhonePe UPI for Order #ZEN-1005 (Nilesh Vardan).", "2026-10-18 10:31:45"),
        ("SUCCESS", "WUKUSY", "Automated fulfillment dispatch created at DeoDap Rajkot Hub (AWB: DEL982145019).", "2026-10-18 10:32:00"),
        ("SUCCESS", "RAZORPAY", "Payment captured ₹254 via Google Pay for Order #ZEN-1006 (Rohan Sharma). Saved ₹45 courier risk.", "2026-10-18 11:17:35"),
        ("SUCCESS", "WHATSAPP", "Interactive COD Confirmation verified by Pooja Verma (+91 98112 34567).", "2026-10-18 11:43:50"),
        ("SUCCESS", "WHATSAPP", "Out For Delivery availability confirmed by Nilesh Vardan. Delivery partner instructed to proceed.", "2026-10-18 12:05:42"),
        ("WARNING", "WHATSAPP", "Customer Vikramaditya Chauhan requested reschedule for tomorrow. Courier slot shifted.", "2026-10-18 12:36:20"),
        ("WARNING", "RTO_SHIELD", "High RTO risk flagged on Order #ZEN-1012 (Sunil Meena, Dausa). Address missing door number. Phone verification queued.", "2026-10-18 12:48:20"),
        ("SUCCESS", "RTO_SHIELD", "Order #ZEN-1013 cancelled prior to dispatch by Deepak Mehta. Successfully prevented ₹90 forward/reverse courier loss!", "2026-10-18 12:52:10"),
        ("INFO", "META_API", "WhatsApp Cloud API connection healthy. 0 queue backlog. Latency: 142ms.", "2026-10-18 12:58:00")
    ]

    for l in seed_logs:
        cursor.execute("INSERT INTO system_logs (level, source, message, created_at) VALUES (?, ?, ?, ?)", l)

    conn.commit()

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
        clean_phone = str(phone).replace("+", "").replace(" ", "").replace("-", "")
        if len(clean_phone) == 10:
            clean_phone = f"91{clean_phone}"

        cursor.execute("""
        INSERT INTO messages (phone, customer_name, direction, message_type, body, button_id, wa_message_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (clean_phone, customer_name, direction, message_type, body, button_id, wa_message_id))
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

    cursor.execute("SELECT COUNT(*) as high_risk_count FROM orders WHERE rto_risk_score < 60 OR status = 'RTO_RISK_HIGH'")
    high_risk_count = cursor.fetchone()["high_risk_count"]

    cursor.execute("SELECT AVG(rto_risk_score) as avg_rto FROM orders WHERE status != 'CANCELLED'")
    avg_rto_row = cursor.fetchone()
    avg_rto_score = round(avg_rto_row["avg_rto"] or 94.5, 1)

    cursor.execute("SELECT SUM(amount) as total_gmv FROM orders WHERE status != 'CANCELLED'")
    gmv_row = cursor.fetchone()
    total_gmv = gmv_row["total_gmv"] or 0

    cursor.execute("SELECT SUM(discount_amount) as total_discount FROM orders WHERE status = 'PREPAID_PAID'")
    disc_row = cursor.fetchone()
    total_discount_given = disc_row["total_discount"] or 0

    # 2. Recent Orders (Sorted Newest First)
    cursor.execute("SELECT * FROM orders ORDER BY id DESC LIMIT 50")
    orders = [dict(row) for row in cursor.fetchall()]

    # 3. System Logs
    cursor.execute("SELECT * FROM system_logs ORDER BY id DESC LIMIT 40")
    logs = [dict(row) for row in cursor.fetchall()]

    # 4. Group Messages into Customer Conversations
    cursor.execute("SELECT * FROM messages ORDER BY id ASC")
    raw_messages = [dict(row) for row in cursor.fetchall()]

    conversations = {}
    for m in raw_messages:
        phone = m["phone"]
        if phone not in conversations:
            conversations[phone] = {
                "phone": phone,
                "customer_name": m["customer_name"],
                "last_message": m["body"],
                "last_time": m["created_at"],
                "messages": []
            }
        conversations[phone]["messages"].append(m)
        conversations[phone]["last_message"] = m["body"]
        conversations[phone]["last_time"] = m["created_at"]

    conn.close()

    prepaid_ratio = round((prepaid_count / total_orders * 100), 1) if total_orders > 0 else 0
    saved_rto_loss = cancelled_count * 90 # ₹90 saved per intercepted package

    return {
        "kpis": {
            "total_orders": total_orders,
            "prepaid_count": prepaid_count,
            "prepaid_ratio": f"{prepaid_ratio}%",
            "cod_confirmed": cod_confirmed,
            "ofd_count": ofd_count,
            "cancelled_count": cancelled_count,
            "high_risk_count": high_risk_count,
            "avg_rto_score": f"{avg_rto_score}/100",
            "saved_rto_loss": f"₹{saved_rto_loss}",
            "total_discount_given": f"₹{total_discount_given}",
            "total_gmv": f"₹{total_gmv}"
        },
        "orders": orders,
        "logs": logs,
        "conversations": conversations
    }

def delete_order(order_ref):
    """Deletes an order permanently from database"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM orders WHERE order_ref = ?", (order_ref,))
        conn.commit()
        conn.close()
        log_event("WARNING", "DATABASE", f"Order {order_ref} deleted by founder.")
        return True
    except Exception as e:
        logger.error(f"Error deleting order: {e}")
        return False

def clear_all_orders():
    """Wipes all demo/test orders, conversations, and logs clean"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM orders")
        cursor.execute("DELETE FROM messages")
        cursor.execute("DELETE FROM system_logs")
        conn.commit()
        conn.close()
        log_event("WARNING", "DATABASE", "All orders and test data wiped clean by founder.")
        return True
    except Exception as e:
        logger.error(f"Error clearing all orders: {e}")
        return False

def reseed_demo_orders():
    """Seeds realistic sample orders only when explicitly requested by founder"""
    try:
        conn = get_db()
        seed_realistic_zenos_data(conn)
        conn.close()
        log_event("INFO", "DATABASE", "Sample orders re-seeded upon founder request.")
        return True
    except Exception as e:
        logger.error(f"Error reseeding demo orders: {e}")
        return False

