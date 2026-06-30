import time
import requests
import os

TG_TOKEN = os.environ.get("TG_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")
CHECK_INTERVAL = 45

TARGET_PLAN = "Seedbox 8TB R5 10G"
URL = "https://pulsedmedia.com/clients/index.php/store/the-eternal-vainamoinen"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "Markdown"})
    except:
        pass

if __name__ == "__main__":
    send_telegram("🚀 Heroku Bot Re-Aligned! Tracking updated layout precisely...")
    
    while True:
        try:
            print(f"Checking updated page text... Target: {TARGET_PLAN}", flush=True)
            res = requests.get(URL, headers=headers, timeout=15)
            
            if res.status_code == 200:
                raw_html = res.text
                
                if TARGET_PLAN in raw_html:
                    parts = raw_html.split(TARGET_PLAN)
                    status_chunk = parts[1][:300].lower()
                    
                    print(f"Inspecting Text Block: {status_chunk[:120]}...", flush=True)
                    
                    # 1. Look for definitive unavailable text strings
                    is_unavailable = "0 available" in status_chunk or "out of stock" in status_chunk or "out stock" in status_chunk
                    
                    # 2. Look for explicit indicators that it IS available (like "open", "available", or "get one")
                    is_available_keywords = "available" in status_chunk or "open" in status_chunk or "get one" in status_chunk or "order" in status_chunk
                    
                    # ONLY send a Telegram alert if it is not unavailable AND we actually see active order/stock phrasing
                    if not is_unavailable and is_available_keywords:
                        print("!!! 8TB SEEDBOX DETECTED IN STOCK !!! Sending Telegram Alert.", flush=True)
                        send_telegram(f"🚨 *8TB IN STOCK ALERT!* 🚨\n\n📦 *Plan:* {TARGET_PLAN}\n🔗 [Order Now]({URL})")
                    else:
                        print(f"Result: {TARGET_PLAN} is explicitly out of stock or reading layout noise.", flush=True)
                else:
                    print(f"Warning: '{TARGET_PLAN}' text not found on page.", flush=True)
            else:
                print(f"Connection Warning: HTTP Status {res.status_code}", flush=True)
                
        except Exception as e:
            print(f"Error during execution loop: {e}", flush=True)
            
        time.sleep(CHECK_INTERVAL)
