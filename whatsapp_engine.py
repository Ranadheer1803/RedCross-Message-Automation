import urllib.parse
import re
import datetime
import logging

logging.basicConfig(level=logging.INFO)

def format_clean_phone(phone_str: str) -> str:
    """Ensure phone number has only digits without leading + for API URLs."""
    if not phone_str:
        return ""
    digits = re.sub(r'\D', '', str(phone_str))
    # If 10 digits, add country code 91 by default
    if len(digits) == 10:
        digits = "91" + digits
    return digits

def generate_whatsapp_web_url(phone: str, message: str) -> str:
    """Generate universal WhatsApp Web / App deep link."""
    clean_phone = format_clean_phone(phone)
    encoded_msg = urllib.parse.quote(message)
    return f"https://api.whatsapp.com/send?phone={clean_phone}&text={encoded_msg}"

def generate_wa_me_link(phone: str, message: str) -> str:
    """Generate wa.me short link."""
    clean_phone = format_clean_phone(phone)
    encoded_msg = urllib.parse.quote(message)
    return f"https://wa.me/{clean_phone}?text={encoded_msg}"

def dispatch_pywhatkit_message(phone: str, message: str, wait_time: int = 15) -> dict:
    """
    Attempt to send WhatsApp message instantly via pywhatkit / Web browser automation.
    """
    try:
        import pywhatkit
        clean_phone = format_clean_phone(phone)
        full_phone = f"+{clean_phone}" if not clean_phone.startswith("+") else clean_phone
        
        # pywhatkit sendwhatmsg_instantly
        pywhatkit.sendwhatmsg_instantly(
            phone_no=full_phone,
            message=message,
            wait_time=wait_time,
            tab_close=True,
            close_time=3
        )
        return {"status": "success", "message": f"Dispatched message to {full_phone}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def dispatch_twilio_whatsapp(phone: str, message: str, account_sid: str, auth_token: str, from_number: str) -> dict:
    """
    Send official WhatsApp message using Twilio API (if configured).
    """
    try:
        import requests
        clean_phone = format_clean_phone(phone)
        to_number = f"whatsapp:+{clean_phone}"
        from_num = f"whatsapp:{from_number}" if not from_number.startswith("whatsapp:") else from_number
        
        url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
        data = {
            "From": from_num,
            "To": to_number,
            "Body": message
        }
        response = requests.post(url, data=data, auth=(account_sid, auth_token))
        if response.status_code in [200, 201]:
            return {"status": "success", "response": response.json()}
        else:
            return {"status": "error", "message": response.text}
    except Exception as e:
        return {"status": "error", "message": str(e)}
