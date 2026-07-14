import time
import requests
import os

TG_TOKEN = os.environ.get("TG_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")
CHECK_INTERVAL = 45

# Explicit targets tracking 
TARGET_PLANS = [
    "Seedbox 8TB R5 10G",
    "Dragon-R Trophy"
]

URL = "https://pulsedmedia.com/clients/index.php/store/the-eternal-vainamoinen"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "Markdown"})
    except:
        pass

if __name__ == "__main__":
    # Standard static message on startup — never changes on update
    send_telegram("🚀 Heroku Bot Active! Tracking Pulsed Media packages now...")
    
    while True:
        try:
            print("Fetching store page and scanning text matrix...", flush=True)
            res = requests.get(URL, headers=headers, timeout=15)
            
            if res.status_code == 200:
                raw_html = res.text
                
                for plan in TARGET_PLANS:
                    if plan in raw_html:
                        parts = raw_html.split(plan)
                        status_chunk = parts[1][:300].lower()
                        
                        print(f"[{plan}] Evaluating Zone: {status_chunk[:90]}...", flush=True)
                        
                        # Resilient markers matching updated table layouts
                        is_unavailable = "0 available" in status_chunk or "out of stock" in status_chunk or "out stock" in status_chunk
                        is_orderable = "available" in status_chunk or "open" in status_chunk or "order" in status_chunk or "get one" in status_chunk
                        
                        if not is_unavailable and is_orderable:
                            print(f"!!! MATCH FOUND FOR {plan} !!! Sending Alert.", flush=True)
                            send_telegram(f"🚨 *STOCK ALERT:* [{plan}] IS LIVE! 🚨\n\n📦 *Plan:* {plan}\n🔗 [Order Instantly Now]({URL})")
                        else:
                            print(f"Result: {plan} is confirmed out of stock.", flush=True)
                    else:
                        print(f"Notice: {plan} keyword not visible in current batch layout.", flush=True)
            else:
                print(f"Network Warning: HTTP Code {res.status_code}", flush=True)
                
        except Exception as e:
            print(f"Error during runtime matrix loop: {e}", flush=True)
            
        time.sleep(CHECK_INTERVAL)
