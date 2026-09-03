import urllib.parse
import webbrowser
import requests

def clean_phone_for_whatsapp(phone_raw: str) -> str:
    digits = ''.join(c for c in str(phone_raw) if c.isdigit())
    if len(digits) == 10:
        return f"91{digits}"
    return digits

def generate_whatsapp_web_url(phone_raw: str, message: str) -> str:
    """Generate official WhatsApp Web API URL with pre-filled message text."""
    phone_clean = clean_phone_for_whatsapp(phone_raw)
    encoded_msg = urllib.parse.quote(message)
    return f"https://api.whatsapp.com/send?phone={phone_clean}&text={encoded_msg}"

def generate_wa_me_link(phone_raw: str, message: str) -> str:
    """Generate short wa.me URL for quick mobile opening."""
    phone_clean = clean_phone_for_whatsapp(phone_raw)
    encoded_msg = urllib.parse.quote(message)
    return f"https://wa.me/{phone_clean}?text={encoded_msg}"

def dispatch_whatsapp_web_js(phone_raw: str, message: str) -> dict:
    """Send message via background Node.js whatsapp-web.js microservice on port 3000 (0-click API dispatch)."""
    try:
        url = "http://localhost:3000/send-message"
        res = requests.post(url, json={"phone": phone_raw, "message": message}, timeout=10)
        return res.json()
    except Exception as e:
        return {"status": "error", "message": f"whatsapp-web.js Node service offline: {e}"}

def dispatch_pywhatkit_message(phone_raw: str, message: str) -> dict:
    """Send message via PyWhatKit instant browser automation."""
    try:
        import pywhatkit
        phone_clean = clean_phone_for_whatsapp(phone_raw)
        formatted_phone = f"+{phone_clean}"
        pywhatkit.sendwhatmsg_instantly(formatted_phone, message, wait_time=8, tab_close=True, close_time=3)
        return {"status": "success", "message": f"PyWhatKit message dispatched to {formatted_phone}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def dispatch_twilio_whatsapp(phone_raw: str, message: str, account_sid: str, auth_token: str, from_number: str) -> dict:
    """Send WhatsApp message using Twilio WhatsApp API."""
    try:
        phone_clean = clean_phone_for_whatsapp(phone_raw)
        to_number = f"whatsapp:+{phone_clean}"
        if not from_number.startswith("whatsapp:"):
            from_number = f"whatsapp:{from_number}"
            
        url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
        payload = {
            'From': from_number,
            'To': to_number,
            'Body': message
        }
        response = requests.post(url, data=payload, auth=(account_sid, auth_token))
        if response.status_code in [200, 201]:
            return {"status": "success", "data": response.json()}
        else:
            return {"status": "error", "message": response.text}
    except Exception as e:
        return {"status": "error", "message": str(e)}
