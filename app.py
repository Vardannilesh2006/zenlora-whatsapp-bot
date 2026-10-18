import os
import json
import logging
import requests
from flask import Flask, request, jsonify, render_template
from db import init_db, get_dashboard_data, save_or_update_order, update_order_status, record_message, log_event

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize ZenOS Database
init_db()

# Configurations
VERIFY_TOKEN = os.getenv("META_VERIFY_TOKEN", "zenlora_secret_token_2026")
WHATSAPP_TOKEN = os.getenv("META_ACCESS_TOKEN", "EAAkmfpCGwLUBS9vTp9AcI3eQikEksYUciEhYSZCcfL9HtH3uRttmEVlTVlnOQmteZBGTUsnUxQ86DvMDcuRT8KcbgB1CkkS9DqIYlSwFkaTwxCnukGOMDhUSrUZA59EkMZAtTSnZCdKW1b3lRyJRmHQAzWTI0ZCs17PU0VEE11vibtNn7Jl3LfvuuqmR1uiw0kMAZDZD")
PHONE_NUMBER_ID = os.getenv("META_PHONE_ID", "1385477007982491")
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "rzp_live_TowfcuBZZgrDeg")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "RmTDV14cCIK1YxscAlWCYNvq")

def send_whatsapp_message(to_number, text_message):
    """Sends a text message back to WhatsApp user"""
    url = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {
            "body": text_message
        }
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        logger.info(f"Send status: {response.status_code}, response: {response.text}")
        return response.json()
    except Exception as e:
        logger.error(f"Error sending WhatsApp message: {e}")
        return None

def send_interactive_order_confirmation(to_phone, customer_name, order_id, product_name, cod_amount):
    """Sends the 3-Button Interactive Order Confirmation to customer with 15% discount calculation."""
    url = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    
    clean_phone = str(to_phone).replace("+", "").replace(" ", "").replace("-", "")
    if len(clean_phone) == 10:
        clean_phone = f"91{clean_phone}"

    cod_val = int(cod_amount)
    savings = round(cod_val * 0.15)
    prepaid_val = cod_val - savings

    body_text = (
        f"Hi *{customer_name}!* 👋\n\n"
        f"Your order has been confirmed with Zenlora.\n\n"
        f"*🔖 Order #ZEN-{order_id}*\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"📦 {product_name}\n"
        f"━━━━━━━━━━━━━━━━\n\n"
        f"🟡 *COD:* Pay ₹{cod_val} at doorstep\n"
        f"🟢 *Online:* Pay only ₹{prepaid_val} — Save 15%\n"
        f"   ✅ Free shipping  ✅ Priority dispatch\n"
        f"   ⏱️ Offer valid for 15 mins only\n\n"
        f"─────────────────\n"
        f"✨ Zenlora | zenlora.store"
    )

    payload = {
        "messaging_product": "whatsapp",
        "to": clean_phone,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "header": {
                "type": "text",
                "text": "Zenlora Store — Order Confirmed 🛍️"
            },
            "body": {
                "text": body_text
            },
            "footer": {
                "text": "Thank you for choosing Zenlora!"
            },
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": f"btn_pay_{order_id}_{cod_val}",
                            "title": "⚡ Pay & Save 15%"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": f"btn_cod_{order_id}",
                            "title": "✅ Confirm COD"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": f"btn_cancel_{order_id}",
                            "title": "❌ Cancel Order"
                        }
                    }
                ]
            }
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        logger.info(f"Trigger Order WhatsApp Status: {response.status_code}, Resp: {response.text}")
        return response.json()
    except Exception as e:
        logger.error(f"Error triggering order WhatsApp: {e}")
        return None

def send_interactive_ofd_check(to_phone, customer_name, order_id, product_name, cod_amount, contact_phone="02242567777", pin="159"):
    """Sends Flipkart Saathi-style Out For Delivery (OFD) Availability Check to reduce RTO."""
    url = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    clean_phone = str(to_phone).replace("+", "").replace(" ", "").replace("-", "")
    if len(clean_phone) == 10:
        clean_phone = f"91{clean_phone}"

    cod_val = int(cod_amount)

    body_text = (
        f"Your *zenlora.store* order is out for delivery today. 🚚\n\n"
        f"📦 *Item:* {product_name}\n"
        f"🔖 *Order:* #ZEN-{order_id}\n\n"
        f"💵 Kindly pay *₹{cod_val}* for your cash on delivery order.\n\n"
        f"To help us deliver on time, please confirm you can collect the order today between *9 am - 8 pm*.\n\n"
        f"📞 *Delivery Helpline:* {contact_phone}\n"
        f"🔐 *Security PIN:* {pin}\n\n"
        f"─────────────────\n"
        f"✨ Zenlora | zenlora.store"
    )

    payload = {
        "messaging_product": "whatsapp",
        "to": clean_phone,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "header": {
                "type": "text",
                "text": f"Availability Check: Order #{order_id}"
            },
            "body": {
                "text": body_text
            },
            "footer": {
                "text": "Thank you for choosing Zenlora!"
            },
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": f"btn_collect_{order_id}_{cod_val}",
                            "title": "📦 I can collect"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": f"btn_resched_{order_id}_{cod_val}",
                            "title": "📅 Change the date"
                        }
                    }
                ]
            }
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        logger.info(f"Trigger OFD WhatsApp Status: {response.status_code}, Resp: {response.text}")
        return response.json()
    except Exception as e:
        logger.error(f"Error triggering OFD WhatsApp: {e}")
        return None

def create_razorpay_payment_link(original_amount_inr, customer_name, customer_phone, order_ref="ZEN-1001", discount_pct=15):
    """Creates a 1-tap dynamic payment link via Razorpay API with exact 15% discount applied"""
    try:
        discount_amount = round(original_amount_inr * (discount_pct / 100.0))
        payable_amount = original_amount_inr - discount_amount
        amount_in_paise = int(payable_amount * 100)

        url = "https://api.razorpay.com/v1/payment_links"
        payload = {
            "amount": amount_in_paise,
            "currency": "INR",
            "accept_partial": False,
            "description": f"Zenlora Order #{order_ref} - Flat {discount_pct}% VIP Prepaid Discount",
            "customer": {
                "name": customer_name,
                "contact": customer_phone
            },
            "notify": {
                "sms": False,
                "email": False
            },
            "reminder_enable": False,
            "notes": {
                "policy": f"Flat {discount_pct}% Instant Prepaid Privilege",
                "original_cod_amount": f"Rs {original_amount_inr}",
                "discount_saved": f"Rs {discount_amount}",
                "final_paid": f"Rs {payable_amount}",
                "store": "Zenlora Store"
            }
        }
        auth = (RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET)
        res = requests.post(url, json=payload, auth=auth, timeout=10)
        if res.status_code in [200, 201]:
            data = res.json()
            short_url = data.get("short_url")
            logger.info(f"Generated Razorpay link: {short_url} for Rs {payable_amount}")
            return short_url, payable_amount, discount_amount
        else:
            logger.error(f"Razorpay API Error: {res.text}")
            return "https://zenlora.store", payable_amount, discount_amount
    except Exception as e:
        logger.error(f"Razorpay Exception: {e}")
        return "https://zenlora.store", 297, 52

@app.route("/", methods=["GET"])
@app.route("/dashboard", methods=["GET"])
def render_cockpit():
    """Renders the Hallmark-compliant ZenOS Founder Cockpit"""
    return render_template("dashboard.html")

@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "live",
        "service": "ZenOS Founder Cockpit & Automation Engine",
        "razorpay_connected": bool(RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET)
    }), 200

@app.route("/api/dashboard/data", methods=["GET"])
def fetch_dashboard_metrics():
    """Returns real-time KPIs, orders, and logs from SQLite"""
    try:
        data = get_dashboard_data()
        return jsonify(data), 200
    except Exception as e:
        logger.error(f"Error fetching dashboard data: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/dashboard/action", methods=["POST"])
def execute_dashboard_action():
    """Triggered by 1-click action buttons on the ZenOS Cockpit"""
    try:
        req = request.get_json(force=True)
        action = req.get("action")
        order_ref = req.get("order_ref", "ZEN-1001")
        
        from db import get_db
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM orders WHERE order_ref = ?", (order_ref,))
        order = cursor.fetchone()
        conn.close()

        if not order:
            return jsonify({"status": "error", "message": f"Order {order_ref} not found"}), 404

        order_dict = dict(order)
        phone = order_dict["phone"]
        cust_name = order_dict["customer_name"]
        amt = order_dict["amount"]
        item = order_dict["product_name"]

        if action == "order":
            res = send_interactive_order_confirmation(phone, cust_name, order_ref.replace("ZEN-", ""), item, amt)
            log_event("SUCCESS", "DASHBOARD", f"Manually resent Order Confirmation to {cust_name} ({phone})")
            return jsonify({"status": "success", "message": f"WhatsApp Order Confirmation sent to {cust_name}!"}), 200
        
        elif action == "ofd":
            res = send_interactive_ofd_check(phone, cust_name, order_ref.replace("ZEN-", ""), item, amt)
            update_order_status(order_ref, "OUT_FOR_DELIVERY")
            log_event("SUCCESS", "DASHBOARD", f"Manually triggered Out For Delivery check to {cust_name} ({phone})")
            return jsonify({"status": "success", "message": f"Out For Delivery check sent to {cust_name}!"}), 200

        elif action == "wukusy":
            update_order_status(order_ref, order_dict["status"], {"wukusy_status": "SYNCED_QUEUE"})
            log_event("SUCCESS", "WUKUSY", f"Order {order_ref} staged for 1-Click Wukusy fulfillment.")
            return jsonify({"status": "success", "message": f"Order {order_ref} staged for Wukusy fulfillment!"}), 200

        return jsonify({"status": "error", "message": "Unknown action"}), 400

    except Exception as e:
        logger.error(f"Error executing action: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/dashboard/chat/send", methods=["POST"])
def send_admin_chat_reply():
    """Allows founder/admin to send direct WhatsApp messages from cockpit"""
    try:
        req = request.get_json(force=True)
        phone = req.get("phone")
        msg = req.get("message")
        if not phone or not msg:
            return jsonify({"status": "error", "message": "Phone and message are required"}), 400

        result = send_whatsapp_message(phone, msg)
        record_message(phone, "Customer", "OUTBOUND", "TEXT", msg)
        log_event("INFO", "LIVE_CHAT", f"Admin sent direct message to {phone}: '{msg[:40]}...'")
        return jsonify({"status": "success", "result": result}), 200
    except Exception as e:
        logger.error(f"Error sending admin chat: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/order-webhook", methods=["POST"])
def handle_store_order():
    """Triggered whenever a new order occurs on zenlora.store"""
    try:
        data = request.get_json(force=True)
        logger.info(f"New Order Received: {data}")

        customer_name = data.get("customer_name", "Valued Customer")
        phone = data.get("phone")
        order_id = str(data.get("order_id", "1001"))
        product_name = data.get("product_name", "Zenlora Lifestyle Item")
        amount = data.get("amount", 349)

        if not phone:
            return jsonify({"status": "error", "message": "Phone number is required"}), 400

        # Save to ZenOS Database
        data["status"] = "PENDING_VERIFICATION"
        save_or_update_order(data)

        # Trigger WhatsApp Confirmation
        result = send_interactive_order_confirmation(
            to_phone=phone,
            customer_name=customer_name,
            order_id=order_id,
            product_name=product_name,
            cod_amount=amount
        )

        record_message(phone, customer_name, "OUTBOUND", "INTERACTIVE_ORDER", f"Order #{order_id} confirmation sent with 15% discount option")

        return jsonify({"status": "success", "result": result}), 200

    except Exception as e:
        logger.error(f"Error processing store order: {e}")
        log_event("ERROR", "SMARTBIZ", f"Failed to ingest order: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/ofd-webhook", methods=["POST"])
def handle_ofd_trigger():
    """Triggered when an order is Out For Delivery to check customer availability and reduce RTO"""
    try:
        data = request.get_json(force=True)
        logger.info(f"Out For Delivery Trigger Received: {data}")

        customer_name = data.get("customer_name", "Valued Customer")
        phone = data.get("phone")
        order_id = data.get("order_id", "1001")
        product_name = data.get("product_name", "Zenlora Order")
        amount = data.get("amount", 349)
        pin = data.get("pin", "159")
        helpline = data.get("helpline", "02242567777")

        if not phone:
            return jsonify({"status": "error", "message": "Phone number is required"}), 400

        result = send_interactive_ofd_check(
            to_phone=phone,
            customer_name=customer_name,
            order_id=order_id,
            product_name=product_name,
            cod_amount=amount,
            contact_phone=helpline,
            pin=pin
        )

        update_order_status(phone, "OUT_FOR_DELIVERY")
        record_message(phone, customer_name, "OUTBOUND", "INTERACTIVE_OFD", f"Out For Delivery check sent for Order #{order_id}")
        log_event("SUCCESS", "WHATSAPP", f"Out For Delivery check sent to {customer_name} ({phone})")

        return jsonify({"status": "success", "result": result}), 200

    except Exception as e:
        logger.error(f"Error processing OFD check: {e}")
        log_event("ERROR", "WHATSAPP", f"Error sending OFD check: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/webhook", methods=["GET"])
def verify_webhook():
    """Meta Webhook verification handshake"""
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        logger.info("Meta Webhook successfully verified!")
        return challenge, 200
    else:
        logger.warning("Webhook verification failed. Token mismatch.")
        return "Verification failed", 403

@app.route("/webhook", methods=["POST"])
def handle_incoming_messages():
    """Ultra-resilient webhook handler for Meta events"""
    try:
        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify({"status": "no_data"}), 200

        logger.info(f"Incoming Webhook Raw: {json.dumps(data)}")

        # Meta always wraps notifications in 'entry'
        entries = data.get("entry", [])
        if not entries:
            return jsonify({"status": "empty_entry"}), 200

        for entry in entries:
            changes = entry.get("changes", [])
            for change in changes:
                value = change.get("value", {})
                
                # If it's a delivery status update (sent/delivered/read), acknowledge with 200 OK
                if "statuses" in value and "messages" not in value:
                    continue

                messages = value.get("messages", [])
                if not messages:
                    continue

                for msg in messages:
                    sender_phone = msg.get("from")
                    sender_name = "there"
                    
                    contacts = value.get("contacts", [])
                    if contacts:
                        sender_name = contacts[0].get("profile", {}).get("name", "there")

                    msg_type = msg.get("type", "")
                    logger.info(f"Processing message from {sender_phone}, type: {msg_type}")

                    btn_id = ""
                    button_text = ""
                    text_body = ""

                    if msg_type == "interactive":
                        interactive = msg.get("interactive", {})
                        if interactive.get("type") == "button_reply":
                            btn_id = interactive.get("button_reply", {}).get("id", "")
                            button_text = interactive.get("button_reply", {}).get("title", "")
                    elif msg_type == "button":
                        btn_obj = msg.get("button", {})
                        btn_id = btn_obj.get("payload", "")
                        button_text = btn_obj.get("text", "")
                    elif msg_type == "text":
                        text_body = msg.get("text", {}).get("body", "").strip()

                    action_str = f"{btn_id} {button_text} {text_body}".lower().strip()
                    logger.info(f"Action string resolved: '{action_str}' from {sender_phone}")

                    # Record Inbound Message
                    record_message(sender_phone, sender_name, "INBOUND", msg_type, text_body or button_text or action_str, btn_id)

                    # Option 1: "I can collect" / Availability Confirmed
                    if "collect" in action_str:
                        cod_val = "349"
                        parts = btn_id.split("_")
                        if len(parts) >= 4:
                            cod_val = parts[3]

                        reply = (
                            f"🎉 *Thank you for confirming, {sender_name}!* 🚚\n\n"
                            f"Your delivery partner has been notified that you are available to collect the order today!\n\n"
                            f"💵 Kindly keep *₹{cod_val}* ready in cash or via UPI at doorstep.\n\n"
                            f"📦 We hope you love your Zenlora purchase!\n\n"
                            f"─────────────────\n"
                            f"✨ *Thank you for choosing Zenlora!*\n"
                            f"I hope your day goes amazing and filled with joy! 😊\n"
                            f"— *Team Zenlora* 🛍️"
                        )
                        send_whatsapp_message(sender_phone, reply)
                        update_order_status(sender_phone, "DELIVERY_COLLECT_CONFIRMED")
                        record_message(sender_phone, sender_name, "OUTBOUND", "TEXT", "Delivery collection confirmed reply sent")
                        log_event("SUCCESS", "WHATSAPP", f"Customer {sender_name} confirmed OFD collection today!")

                    # Option 2: "Change the date" / Reschedule
                    elif "resched" in action_str or "change the date" in action_str or "date" in action_str:
                        reply = (
                            f"🗓️ *Delivery Rescheduled Successfully!* ⏱️\n\n"
                            f"No worries at all, {sender_name}! We have updated your preference with our courier delivery partner so you don't face any inconvenience.\n\n"
                            f"Your delivery attempt has been rescheduled for *Tomorrow*. The delivery partner will contact you prior to arrival.\n\n"
                            f"─────────────────\n"
                            f"✨ *Thank you for choosing Zenlora!*\n"
                            f"I hope your day goes amazing and filled with joy! 😊\n"
                            f"— *Team Zenlora* 🛍️"
                        )
                        send_whatsapp_message(sender_phone, reply)
                        update_order_status(sender_phone, "DELIVERY_RESCHEDULED")
                        record_message(sender_phone, sender_name, "OUTBOUND", "TEXT", "Delivery reschedule reply sent")
                        log_event("WARNING", "WHATSAPP", f"Customer {sender_name} rescheduled delivery for tomorrow.")

                    # Option 3: "Pay & Save 15%"
                    elif "btn_pay" in action_str or "pay" in action_str or "save 15" in action_str or "save" in action_str:
                        parts = btn_id.split("_")
                        original_cod = 349
                        order_ref = "ZEN-1001"
                        if len(parts) >= 4:
                            order_ref = f"ZEN-{parts[2]}"
                            try:
                                original_cod = int(parts[3])
                            except:
                                original_cod = 349

                        rzp_link, payable_amt, saved_amt = create_razorpay_payment_link(
                            original_amount_inr=original_cod,
                            customer_name=sender_name,
                            customer_phone=sender_phone,
                            order_ref=order_ref,
                            discount_pct=15
                        )

                        reply = (
                            f"🎉 *Fantastic choice, {sender_name}!* ⚡\n\n"
                            f"You have unlocked *FLAT 15% Instant Savings*!\n"
                            f"• Original COD Price: ~₹{original_cod}~\n"
                            f"• *Discounted Amount:* ₹{payable_amt} *(You save ₹{saved_amt}!)*\n\n"
                            f"👉 *Tap below to pay securely via Google Pay / PhonePe / Paytm / UPI:*\n"
                            f"🔗 {rzp_link}\n\n"
                            f"⏱️ *Offer validity:* 15 minutes only.\n"
                            f"Once payment is completed, your package receives *Priority 24h Express Dispatch*! 🚀\n\n"
                            f"─────────────────\n"
                            f"✨ *Thank you for choosing Zenlora!*\n"
                            f"I hope your day goes amazing and filled with joy! 😊\n"
                            f"— *Team Zenlora* 🛍️"
                        )
                        send_whatsapp_message(sender_phone, reply)
                        update_order_status(sender_phone, "PREPAID_PENDING_LINK", {"razorpay_link": rzp_link, "prepaid_amount": payable_amt, "discount_amount": saved_amt})
                        record_message(sender_phone, sender_name, "OUTBOUND", "TEXT", f"15% Discount Razorpay link {rzp_link} sent")
                        log_event("SUCCESS", "RAZORPAY", f"Prepaid link generated for {sender_name} (₹{payable_amt}). Saved ₹{saved_amt} risk!")

                    # Option 4: "Confirm COD"
                    elif "btn_cod" in action_str or "confirm cod" in action_str or "confirm" in action_str:
                        reply = (
                            f"✅ *Order Successfully Confirmed!* 📦\n\n"
                            f"Thank you, {sender_name}! Your Cash on Delivery order is now confirmed and prioritized.\n\n"
                            f"Our fulfillment team is packaging your item with extreme care. You will receive live tracking updates right here on WhatsApp the moment it leaves our warehouse! 🚚\n\n"
                            f"─────────────────\n"
                            f"✨ *Thank you for choosing Zenlora!*\n"
                            f"We truly appreciate your trust and hope your day goes absolutely amazing! 🌟\n"
                            f"— *Team Zenlora* 🛍️"
                        )
                        send_whatsapp_message(sender_phone, reply)
                        update_order_status(sender_phone, "CONFIRMED_COD")
                        record_message(sender_phone, sender_name, "OUTBOUND", "TEXT", "COD confirmation reply sent")
                        log_event("SUCCESS", "WHATSAPP", f"Order confirmed COD by {sender_name}. Queued for dispatch.")

                    # Option 5: "Cancel Order"
                    elif "btn_cancel" in action_str or "cancel" in action_str:
                        reply = (
                            f"We completely understand, {sender_name}. 💙\n\n"
                            f"Your order has been cancelled immediately as requested. You will NOT be contacted by any delivery executive.\n\n"
                            f"We would love to welcome you back whenever you're ready! Here is an exclusive gift voucher just for you:\n"
                            f"🎁 Code: *VIPZEN10* (Flat 10% OFF on your next purchase at zenlora.store)\n\n"
                            f"─────────────────\n"
                            f"✨ *Thank you for considering Zenlora!*\n"
                            f"I hope your day goes wonderful and smiling! ✨\n"
                            f"— *Team Zenlora* 🛍️"
                        )
                        send_whatsapp_message(sender_phone, reply)
                        update_order_status(sender_phone, "CANCELLED")
                        record_message(sender_phone, sender_name, "OUTBOUND", "TEXT", "Cancellation response and voucher VIPZEN10 sent")
                        log_event("WARNING", "WHATSAPP", f"Order cancelled by {sender_name}. Prevented ₹90 forward/reverse courier loss!")

                    # Option 6: General Text / Store Support
                    else:
                        reply = (
                            f"Hello {sender_name}! 👋\n\n"
                            f"Thank you for contacting *Zenlora Store Support*.\n"
                            f"How can we assist you with your orders or shopping today?\n\n"
                            f"Explore our trending lifestyle collection: https://zenlora.store\n\n"
                            f"✨ *Thank you for choosing Zenlora!*\n"
                            f"I hope your day goes amazing and filled with joy! 🌟\n"
                            f"— *Team Zenlora* 🛍️"
                        )
                        send_whatsapp_message(sender_phone, reply)
                        record_message(sender_phone, sender_name, "OUTBOUND", "TEXT", reply)
                        log_event("INFO", "WHATSAPP", f"Store support auto-reply sent to {sender_phone}.")

        return jsonify({"status": "success"}), 200

    except Exception as e:
        logger.error(f"Fatal error handling webhook: {e}", exc_info=True)
        # Always return 200 to Meta so it does not disable the webhook
        return jsonify({"status": "handled_with_error", "error": str(e)}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
