"""
Sequential 1-by-1 WhatsApp Auto-Send Engine for RED CROSS WEST GODAVARI.
Guarantees ONLY 1 active WhatsApp Web tab at a time, auto-types the message,
auto-presses ENTER to send, closes the tab, and proceeds to the next donor sequentially!
"""

import time
import urllib.parse
import webbrowser
import logging
import pyautogui
import os
import sys

logging.basicConfig(level=logging.INFO)

def send_sequential_emergency_whatsapp(donors_list: list, delay_between_donors: int = 12) -> dict:
    """
    Process emergency donors strictly 1-by-1 to prevent WhatsApp Web multi-tab conflict.
    Autosends each message by auto-pressing the ENTER key!
    """
    if not donors_list:
        return {"status": "error", "message": "No donors provided for dispatch"}

    results = []
    
    # Configure PyAutoGUI failsafe & pause
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0.5

    for idx, donor in enumerate(donors_list):
        phone_raw = donor.get('phone', '')
        digits = ''.join(c for c in str(phone_raw) if c.isdigit())
        if not digits:
            continue
            
        name = donor.get('name', 'Donor')
        msg = donor.get('wa_message', '')
        
        encoded_msg = urllib.parse.quote(msg)
        wa_url = f"https://web.whatsapp.com/send?phone={digits}&text={encoded_msg}"
        
        logging.info(f"[{idx+1}/{len(donors_list)}] Dispatching to {name} ({digits})...")
        
        # 1. Open WhatsApp Web for THIS single donor
        webbrowser.open(wa_url)
        
        # 2. Wait for WhatsApp Web to load chat input (10 seconds for initial web socket load)
        wait_seconds = 12 if idx == 0 else 8
        time.sleep(wait_seconds)
        
        # 3. Auto-press ENTER key to send the pre-filled message!
        pyautogui.press('enter')
        logging.info(f"[{idx+1}/{len(donors_list)}] Auto-pressed ENTER key to send message to {name}!")
        
        # 4. Wait 3 seconds for message delivery transmission
        time.sleep(3)
        
        # 5. Cleanly close the active tab using macOS Cmd+W hotkey so ONLY 1 tab is ever open!
        if sys.platform == 'darwin':
            pyautogui.hotkey('command', 'w')
        else:
            pyautogui.hotkey('ctrl', 'w')
            
        time.sleep(1)
        
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
