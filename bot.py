import time
import requests
import os

TG_TOKEN = os.environ.get("TG_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")
CHECK_INTERVAL = 45

# Stock Tracking Settings
TARGET_PLANS = [
    "Seedbox 8TB R5 10G",
    "Dragon-R Trophy"
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
    # Your standard, static welcome message
    send_telegram("🚀 Heroku Bot Active! Tracking Pulsed Media packages now...")
    
    # State flags to ensure you only get notified EXACTLY ONCE per milestone tier
    notified_490 = False
    notified_495 = False
    notified_499 = False
    
    while True:
        # --- TASK 1: CHECK CAMPAIGN MILESTONES ---
        try:
            # Only request the campaign URL if at least one milestone has not fired yet
            if not notified_490 or not notified_495 or not notified_499:
                print("Checking campaign milestone metrics...", flush=True)
                camp_res = requests.get(CAMPAIGN_URL, headers=headers, timeout=15)
                if camp_res.status_code == 200:
                    camp_html = camp_res.text
                    
                    if "Claimed in the campaign:" in camp_html:
                        milestone_part = camp_html.split("Claimed in the campaign:")[1]
                        raw_count = milestone_part.split("/")[0].strip()
                        clean_count = "".join(c for c in raw_count if c.isdigit())
                        
                        if clean_count:
                            total_claims = int(clean_count)
                            print(f"Current campaign total claims: {total_claims}", flush=True)
                            
                            # Check 490 Tier
                            if total_claims >= 490 and not notified_490:
                                send_telegram(f"🏆 *MILESTONE REACHED!* 🏆\n\nThe total campaign claims have reached *{total_claims}* (Target: 490).\n🔗 [View Campaign]({CAMPAIGN_URL})")
                                notified_490 = True
                                
                            # Check 495 Tier
                            if total_claims >= 495 and not notified_495:
                                send_telegram(f"🏆 *MILESTONE REACHED!* 🏆\n\nThe total campaign claims have reached *{total_claims}* (Target: 495).\n🔗 [View Campaign]({CAMPAIGN_URL})")
                                notified_495 = True
                                
                            # Check 499 Tier
                            if total_claims >= 499 and not notified_499:
                                send_telegram(f"🏆 *MILESTONE REACHED!* 🏆\n\nThe total campaign claims have reached *{total_claims}* (Target: 499).\n🔗 [View Campaign]({CAMPAIGN_URL})")
                                notified_499 = True
                                
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
                            send_telegram(f"🚨 *STOCK ALERT:* [{plan}] IS LIVE! 🚨\n\n📦 *Plan:* {plan}\n🔗 [Order Instantly Now]({STORE_URL})")
                        else:
                            print(f"Result: {plan} is confirmed out of stock.", flush=True)
                    else:
                        print(f"Notice: {plan} keyword not visible in current batch layout.", flush=True)
            else:
                print(f"Network Warning: HTTP Code {res.status_code}", flush=True)
                
        except Exception as e:
            print(f"Error during runtime matrix loop: {e}", flush=True)
            
        time.sleep(CHECK_INTERVAL)
