import os
import json
import logging
import requests
from flask import Flask, request, jsonify

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)

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

def create_razorpay_payment_link(original_amount_inr, customer_name, customer_phone, order_ref="ZEN-1001", discount_pct=15):
    """Creates a 1-tap dynamic payment link via Razorpay API with exact 15% discount applied"""
    try:
        # Calculate exactly 15% OFF
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
def health_check():
    return jsonify({
        "status": "live",
        "service": "Zenlora WhatsApp RTO Killer Engine",
        "razorpay_connected": bool(RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET)
    }), 200

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
    """Receives user interactive button clicks & replies with tailored Thank You messages and Razorpay links"""
    data = request.get_json()
    logger.info(f"Incoming Webhook Payload: {json.dumps(data)}")

    try:
        entry = data.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})
        
        messages = value.get("messages", [])
        if not messages:
            return jsonify({"status": "no_messages"}), 200

        msg = messages[0]
        sender_phone = msg.get("from")
        sender_name = value.get("contacts", [{}])[0].get("profile", {}).get("name", "there")

        # 1. Interactive Button Reply
        if msg.get("type") == "interactive":
            interactive = msg.get("interactive", {})
            btn_id = interactive.get("button_reply", {}).get("id")

            # Option A: User clicked "Pay Online Save 15%"
            if btn_id == "btn_pay_online":
                original_cod = 349
                rzp_link, payable_amt, saved_amt = create_razorpay_payment_link(
                    original_amount_inr=original_cod,
                    customer_name=sender_name,
                    customer_phone=sender_phone,
                    order_ref="ZEN-1001",
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

            # Option B: User clicked "Confirm COD Order"
            elif btn_id == "btn_confirm_cod":
                reply = (
                    f"✅ *Order Successfully Confirmed!* 📦\n\n"
                    f"Thank you, {sender_name}! Your Cash on Delivery order *#ZEN-1001* is now confirmed and prioritized.\n\n"
                    f"Our fulfillment team is packaging your item with extreme care. You will receive live tracking updates right here on WhatsApp the moment it leaves our warehouse! 🚚\n\n"
                    f"─────────────────\n"
                    f"✨ *Thank you for choosing Zenlora!*\n"
                    f"We truly appreciate your trust and hope your day goes absolutely amazing! 🌟\n"
                    f"— *Team Zenlora* 🛍️"
                )
                send_whatsapp_message(sender_phone, reply)

            # Option C: User clicked "Cancel Order"
            elif btn_id == "btn_cancel":
                reply = (
                    f"We completely understand, {sender_name}. 💙\n\n"
                    f"Your order *#ZEN-1001* has been cancelled immediately as requested. You will NOT be contacted by any delivery executive.\n\n"
                    f"We would love to welcome you back whenever you're ready! Here is an exclusive gift voucher just for you:\n"
                    f"🎁 Code: *VIPZEN10* (Flat 10% OFF on your next purchase at zenlora.store)\n\n"
                    f"─────────────────\n"
                    f"✨ *Thank you for considering Zenlora!*\n"
                    f"I hope your day goes wonderful and smiling! ✨\n"
                    f"— *Team Zenlora* 🛍️"
                )
                send_whatsapp_message(sender_phone, reply)

        # 2. Plain Text Fallback Message
        elif msg.get("type") == "text":
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

        return jsonify({"status": "success"}), 200

    except Exception as e:
        logger.error(f"Error handling webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
