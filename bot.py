import time
import requests
import os

TG_TOKEN = os.environ.get("TG_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")
CHECK_INTERVAL = 30

# Stock Tracking Settings
TARGET_PLANS = [
    "Seedbox 8TB R5 10G",
    "Dragon-R Trophy",
    "Mini",
    "Trophy"
]

STORE_URL = "https://pulsedmedia.com/clients/index.php/store/the-eternal-vainamoinen"
CAMPAIGN_URL = "https://pulsedmedia.com/eternal-vainamoinen.php"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "Markdown"})
    except:
        pass

if __name__ == "__main__":
    send_telegram("🚀 Heroku Bot Active! Tracking Pulsed Media packages now...")
    
    # Limits the bot to a maximum of 2 alerts for the Revenue milestone
    revenue_alerts_sent = 0
    
    while True:
        # --- TASK 1: CHECK REVENUE (MRR) MILESTONES ---
        try:
            if revenue_alerts_sent < 2:
                print("Checking campaign MRR (Revenue) metrics...", flush=True)
                camp_res = requests.get(CAMPAIGN_URL, headers=headers, timeout=15)
                
                if camp_res.status_code == 200:
                    camp_html = camp_res.text
                    
                    if "MRR: €" in camp_html:
                        mrr_part = camp_html.split("MRR: €")[1]
                        raw_mrr = mrr_part.split("<")[0].split("·")[0].strip()
                        
                        clean_mrr = "".join(c for c in raw_mrr if c.isdigit() or c == '.')
                        clean_mrr = clean_mrr.rstrip('.')
                        
                        if clean_mrr:
                            total_mrr = float(clean_mrr)
                            print(f"Current campaign MRR: €{total_mrr}", flush=True)
                            
                            if total_mrr >= 1950.0 and revenue_alerts_sent < 2:
                                send_telegram(f"💰 *REVENUE MILESTONE REACHED!* 💰\n\nThe campaign MRR has hit *€{total_mrr}* (Target: €1950+).\n🔗 [View Campaign]({CAMPAIGN_URL})")
                                revenue_alerts_sent += 1
                                
        except Exception as e:
            print(f"Error reading milestone metrics: {e}", flush=True)

        # --- TASK 2: CHECK SEEDBOX STOCK ---
        try:
            print("Checking updated page text for stock...", flush=True)
            res = requests.get(STORE_URL, headers=headers, timeout=15)
            
            if res.status_code == 200:
                raw_html = res.text
                
                for plan in TARGET_PLANS:
                    if plan in raw_html:
                        parts = raw_html.split(plan)
                        status_chunk = parts[1][:300].lower()
                        
                        print(f"[{plan}] Evaluating Zone: {status_chunk[:90]}...", flush=True)
                        
                        is_unavailable = "0 available" in status_chunk or "out of stock" in status_chunk or "out stock" in status_chunk
                        is_orderable = "available" in status_chunk or "open" in status_chunk or "order" in status_chunk or "get one" in status_chunk
                        
                        if not is_unavailable and is_orderable:
                            print(f"!!! MATCH FOUND FOR {plan} !!! Sending Alert.", flush=True)
                            send_telegram(f"🚨 *STOCK ALERT:* [{plan}] IS LIVE! 🚨\n\n📦 *Plan Match:* {plan}\n🔗 [Order Instantly Now]({STORE_URL})")
                        else:
                            print(f"Result: {plan} is confirmed out of stock.", flush=True)
                    else:
                        print(f"Notice: {plan} keyword not visible in current batch layout.", flush=True)
            else:
                print(f"Network Warning: HTTP Code {res.status_code}", flush=True)
                
        except Exception as e:
            print(f"Error during stock check execution loop: {e}", flush=True)
            
        time.sleep(CHECK_INTERVAL)
