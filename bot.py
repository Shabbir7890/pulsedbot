import time
import requests
import re
import os

TG_TOKEN = os.environ.get("TG_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")
CHECK_INTERVAL = 30

TARGET_PLANS = [
    "Seedbox 8TB R5 10G",
    "Dragon-R Trophy",
    "Mini",
    "Trophy"
]

STORE_URL = "https://pulsedmedia.com/clients/index.php/store/the-eternal-vainamoinen"
CAMPAIGN_URL = "https://pulsedmedia.com/eternal-vainamoinen.php"
BASE_CART_URL = "https://pulsedmedia.com/clients/cart.php?a=add&pid="
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "Markdown"})
    except Exception:
        pass

if __name__ == "__main__":
    send_telegram("🚀 Heroku Bot Active! Tracking Pulsed Media packages and milestones...")

    # State tracking flags
    revenue_alerts_sent = 0
    notified_mrr_3985 = False
    notified_claims_1490 = False
    notified_ref_143 = False
    notified_ref_145 = False

    while True:
        # --- TASK 1: CHECK CAMPAIGN MILESTONES (MRR, CLAIMS, REFERRALS) ---
        try:
            needs_camp_check = (
                (revenue_alerts_sent < 2)
                or (not notified_mrr_3985)
                or (not notified_claims_1490)
                or (not notified_ref_143)
                or (not notified_ref_145)
            )

            if needs_camp_check:
                print("Checking campaign metrics...", flush=True)
                camp_res = requests.get(CAMPAIGN_URL, headers=headers, timeout=15)

                if camp_res.status_code == 200:
                    camp_html = camp_res.text

                    # 1. Revenue / MRR Checks
                    if "MRR: €" in camp_html:
                        mrr_part = camp_html.split("MRR: €")[1]
                        raw_mrr = mrr_part.split("<")[0].split("·")[0].strip()
                        clean_mrr = "".join(c for c in raw_mrr if c.isdigit() or c == '.')
                        clean_mrr = clean_mrr.rstrip('.')

                        if clean_mrr:
                            total_mrr = float(clean_mrr)
                            print(f"Current campaign MRR: €{total_mrr}", flush=True)

                            # 1950+ Euro Tier (Max 2 alerts)
                            if total_mrr >= 1950.0 and revenue_alerts_sent < 2:
                                send_telegram(f"💰 *REVENUE MILESTONE REACHED!* 💰\n\nThe campaign MRR has hit *€{total_mrr}* (Target: €1950+).\n🔗 [View Campaign]({CAMPAIGN_URL})")
                                revenue_alerts_sent += 1

                            # 3985+ Euro Tier (Once)
                            if total_mrr >= 3985.0 and not notified_mrr_3985:
                                send_telegram(f"💰 *REVENUE MILESTONE REACHED!* 💰\n\nThe campaign MRR has reached *€{total_mrr}* (Target: €3985+).\n🔗 [View Campaign]({CAMPAIGN_URL})")
                                notified_mrr_3985 = True

                    # 2. Campaign Claims Check (1490 Claims)
                    if not notified_claims_1490 and "Claimed in the campaign:" in camp_html:
                        claim_part = camp_html.split("Claimed in the campaign:")[1]
                        raw_claims = claim_part.split("/")[0].strip()
                        clean_claims = "".join(c for c in raw_claims if c.isdigit())

                        if clean_claims:
                            total_claims = int(clean_claims)
                            print(f"Current total claims: {total_claims}", flush=True)

                            if total_claims >= 1490:
                                send_telegram(f"🏆 *CLAIM MILESTONE REACHED!* 🏆\n\nTotal claims have reached *{total_claims}* (Target: 1490).\n🔗 [View Campaign]({CAMPAIGN_URL})")
                                notified_claims_1490 = True

                    # 3. Referral Milestones Check (143 & 145)
                    if "REFERRAL MILESTONES" in camp_html.upper():
                        ref_chunk = camp_html[camp_html.upper().find("REFERRAL MILESTONES"):][:1200]
                        ref_match = re.search(r'(\d+)\s+so far', ref_chunk, re.IGNORECASE)

                        if ref_match:
                            current_refs = int(ref_match.group(1))
                            print(f"Current global referrals: {current_refs}", flush=True)

                            if current_refs >= 143 and not notified_ref_143:
                                send_telegram(f"🤝 *REFERRAL MILESTONE!* 🤝\n\nGlobal referrals reached *{current_refs}* (Target: 143)!\n🔗 [View Campaign]({CAMPAIGN_URL})")
                                notified_ref_143 = True

                            if current_refs >= 145 and not notified_ref_145:
                                send_telegram(f"🤝 *REFERRAL MILESTONE!* 🤝\n\nGlobal referrals reached *{current_refs}* (Target: 145)!\n🔗 [View Campaign]({CAMPAIGN_URL})")
                                notified_ref_145 = True

        except Exception as e:
            print(f"Error reading campaign metrics: {e}", flush=True)

        # --- TASK 2: CHECK SEEDBOX STOCK & EXTRACT PID ---
        try:
            print("Checking store page text for stock...", flush=True)
            res = requests.get(STORE_URL, headers=headers, timeout=15)

            if res.status_code == 200:
                raw_html = res.text

                for plan in TARGET_PLANS:
                    if plan in raw_html:
                        parts = raw_html.split(plan)
                        status_chunk = parts[1][:500].lower()

                        print(f"[{plan}] Evaluating Zone: {status_chunk[:90]}...", flush=True)

                        is_unavailable = "0 available" in status_chunk or "out of stock" in status_chunk or "out stock" in status_chunk
                        is_orderable = "available" in status_chunk or "open" in status_chunk or "order" in status_chunk or "get one" in status_chunk

                        if not is_unavailable and is_orderable:
                            print(f"!!! MATCH FOUND FOR {plan} !!! Sending Alert.", flush=True)

                            pid_match = re.search(r'pid=(\d+)', parts[1][:600])
                            if pid_match:
                                found_pid = pid_match.group(1)
                                order_link = f"{BASE_CART_URL}{found_pid}"
                                pid_text = f"\n🔑 *Product ID (PID):* `{found_pid}`\n⚡ [Instant Checkout Link]({order_link})"
                            else:
                                pid_text = f"\n🔗 [Store Page Link]({STORE_URL})"

                            send_telegram(f"🚨 *STOCK ALERT:* [{plan}] IS LIVE! 🚨\n\n📦 *Plan Match:* {plan}{pid_text}")
                        else:
                            print(f"Result: {plan} is confirmed out of stock.", flush=True)
                    else:
                        print(f"Notice: {plan} keyword not visible in current batch layout.", flush=True)
            else:
                print(f"Network Warning: HTTP Code {res.status_code}", flush=True)

        except Exception as e:
            print(f"Error during stock check execution loop: {e}", flush=True)

        time.sleep(CHECK_INTERVAL)
