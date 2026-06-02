import time
import requests
import os

TG_TOKEN = os.environ.get("TG_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")
CHECK_INTERVAL = 45

# Track only the 8TB plan
TRACKED_PLANS = [
    "Seedbox 8TB R5 10G"
]
URL = "https://pulsedmedia.com/clients/index.php/store/the-eternal-vainamoinen"
headers = {'User-Agent': 'Mozilla/5.0'}

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "Markdown"})
    except:
        pass

if __name__ == "__main__":
    send_telegram("Heroku Bot Active! Tracking the 8TB Pulsed Media package now...")
    while True:
        try:
            res = requests.get(URL, headers=headers, timeout=15)
            text = res.text
            for plan in TRACKED_PLANS:
                if plan in text:
                    status = text.split(plan)[1][:60].lower()
                    if "0 available" not in status and "out of stock" not in status:
                        send_telegram(f"IN STOCK ALERT!\n\nPlan: {plan}\nLink: {URL}")
        except Exception as e:
            pass
        time.sleep(CHECK_INTERVAL)