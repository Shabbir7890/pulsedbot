import time
import requests
import os
from bs4 import BeautifulSoup

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
    send_telegram("Heroku Bot Active! Live log printing enabled.")
    while True:
        try:
            # This line will print to your Heroku Logs view every 45 seconds
            print(f"Checking store page... Target: {TARGET_PLAN}", flush=True)
            
            res = requests.get(URL, headers=headers, timeout=15)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, 'html.parser')
                products = soup.find_all('div', class_='product')
                
                for product in products:
                    product_text = product.get_text()
                    
                    if TARGET_PLAN in product_text:
                        status_text = product_text.lower()
                        
                        if "0 available" not in status_text and "out of stock" not in status_text:
                            print(f"!!! MATCH FOUND !!! Sending Telegram Alert.", flush=True)
                            send_telegram(f"🚨 *8TB IN STOCK ALERT!* 🚨\n\n📦 *Plan:* {TARGET_PLAN}\n🔗 [Order Now]({URL})")
                        else:
                            # This prints quietly in your Heroku dashboard logs
                            print(f"Result: {TARGET_PLAN} is currently Out of Stock.", flush=True)
                            
        except Exception as e:
            print(f"Error during check: {e}", flush=True)
            
        time.sleep(CHECK_INTERVAL)
