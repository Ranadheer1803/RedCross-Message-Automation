"""
Sequential 1-by-1 WhatsApp Auto-Send Engine for RED CROSS WEST GODAVARI.
Focuses WhatsApp Web chat input box using screen-space targeting,
auto-presses ENTER key to send, closes the tab, and proceeds to the next donor sequentially!
"""

import time
import urllib.parse
import webbrowser
import logging
import pyautogui
import sys

logging.basicConfig(level=logging.INFO)

def send_sequential_emergency_whatsapp(donors_list: list) -> dict:
    """
    Process emergency donors strictly 1-by-1.
    Focuses the WhatsApp Web input box, auto-presses ENTER to send, and closes the tab cleanly.
    """
    if not donors_list:
        return {"status": "error", "message": "No donors provided for dispatch"}

    results = []
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0.3

    screen_w, screen_h = pyautogui.size()

    for idx, donor in enumerate(donors_list):
        phone_raw = donor.get('phone', '')
        digits = ''.join(c for c in str(phone_raw) if c.isdigit())
        if not digits:
            continue
            
        name = donor.get('name', 'Donor')
        msg = donor.get('wa_message', '')
        
        encoded_msg = urllib.parse.quote(msg)
        wa_url = f"https://web.whatsapp.com/send?phone={digits}&text={encoded_msg}"
        
        logging.info(f"[{idx+1}/{len(donors_list)}] Opening WhatsApp Web for {name} ({digits})...")
        
        # 1. Open WhatsApp Web for THIS single donor
        webbrowser.open(wa_url)
        
        # 2. Wait for WhatsApp Web socket and chat input to finish rendering
        wait_seconds = 14 if idx == 0 else 10
        time.sleep(wait_seconds)
        
        # 3. Focus the WhatsApp Web chat input box by clicking at the lower-center of the screen
        input_x = int(screen_w * 0.55)
        input_y = int(screen_h * 0.93)
        pyautogui.click(input_x, input_y)
        time.sleep(0.5)
        
        # 4. Auto-press ENTER and Return key to send the pre-filled message!
        pyautogui.press('enter')
        time.sleep(0.4)
        pyautogui.press('return')
        
        logging.info(f"[{idx+1}/{len(donors_list)}] Focused & Auto-pressed ENTER key to send message to {name}!")
        
        # 5. Wait 3 seconds for WhatsApp Web to transmit message over websocket
        time.sleep(3)
        
        # 6. Cleanly close active browser tab (Cmd+W on macOS, Ctrl+W on Windows/Linux)
        if sys.platform == 'darwin':
            pyautogui.hotkey('command', 'w')
        else:
            pyautogui.hotkey('ctrl', 'w')
            
        time.sleep(1.5)
        
        results.append({
            "name": name,
            "phone": digits,
            "status": "SENT_AUTOMATICALLY",
            "time": time.strftime("%H:%M:%S")
        })

    return {
        "status": "success",
        "message": f"Successfully auto-sent messages to all {len(results)} donors sequentially!",
        "count": len(results),
        "details": results
    }
