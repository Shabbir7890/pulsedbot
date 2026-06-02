import time
import requests
import os
from bs4 import BeautifulSoup

TG_TOKEN = os.environ.get("TG_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")
CHECK_INTERVAL = 45

# Exact package name on the page
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
    send_telegram("Heroku Bot Updated! Now strictly watching the 8TB package layout container...")
    while True:
        try:
            res = requests.get(URL, headers=headers, timeout=15)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, 'html.parser')
                
                # Find all product containers on the WHMCS page
                products = soup.find_all('div', class_='product')
                
                for product in products:
                    product_text = product.get_text()
                    
                    # Ensure we are looking inside the container for the 8TB plan
                    if TARGET_PLAN in product_text:
                        # Force everything to lowercase for accurate evaluation
                        status_text = product_text.lower()
                        
                        # Only trigger if it doesn't mention 0 or out of stock inside this box
                        if "0 available" not in status_text and "out of stock" not in status_text:
                            send_telegram(f"🚨 *8TB IN STOCK ALERT!* 🚨\n\n📦 *Plan:* {TARGET_PLAN}\n🔗 [Order Now]({URL})")
                            
        except Exception as e:
            pass
        time.sleep(CHECK_INTERVAL)