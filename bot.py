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
    if not TG_TOKEN or not TG_CHAT_ID:
        print("Missing TG_TOKEN or TG_CHAT_ID config vars!", flush=True)
        return
    try:
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        payload = {
            "chat_id": str(TG_CHAT_ID),
            "text": msg,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        res = requests.post(url, json=payload, timeout=10)
        if res.status_code != 200:
            print(f"Telegram Delivery Failed ({res.status_code}): {res.text}", flush=True)
    except Exception as e:
        print(f"Network error sending telegram: {e}", flush=True)

def parse_campaign_data():
    stats = {"mrr": None, "claims": None, "referrals": None}
    try:
        res = requests.get(CAMPAIGN_URL, headers=headers, timeout=15)
        if res.status_code == 200:
            html = res.text
            
            # Flexible MRR regex: handles "MRR:", optional tags/entities, and European spaces
            mrr_match = re.search(r'MRR:[^0-9€&]*[€&euro;]?\s*([0-9\s]+(?:\.[0-9]+)?)', html, re.IGNORECASE)
            if mrr_match:
                clean_mrr = mrr_match.group(1).replace(" ", "").strip()
                if clean_mrr:
                    stats["mrr"] = float(clean_mrr)

            # Claims parse
            if "Claimed in the campaign:" in html:
                claim_part = html.split("Claimed in the campaign:")[1]
                raw_claims = claim_part.split("/")[0].strip()
                clean_claims = "".join(c for c in raw_claims if c.isdigit())
                if clean_claims:
                    stats["claims"] = int(clean_claims)

            # Flexible Referrals regex: searches referral section for current tally
            if "REFERRAL" in html.upper():
                ref_chunk = html[html.upper().find("REFERRAL"):html.upper().find("REFERRAL") + 2500]
                
                # Check for "X so far", "X referrals", or progress "X /"
                ref_match = re.search(r'(\d+)\s*(?:so far|referrals?|confirmed|\/)', ref_chunk, re.IGNORECASE)
                if not ref_match:
                    # Fallback: check percentage and progress bar markers
                    ref_match = re.search(r'—\s*(\d+)', ref_chunk)

                if ref_match:
                    stats["referrals"] = int(ref_match.group(1))
    except Exception as e:
        print(f"Error parsing campaign stats: {e}", flush=True)
    return stats

def handle_stats_command(state):
    stats = parse_campaign_data()
    mrr_val = f"€{stats['mrr']}" if stats["mrr"] is not None else "Pending..."
    claims_val = f"{stats['claims']}" if stats["claims"] is not None else "Pending..."
    refs_val = f"{stats['referrals']}" if stats["referrals"] is not None else "Pending..."

    t2_status = "✅ Reached" if state.get("notified_mrr_3985") else "⏳ Pending"
    claims_status = "✅ Reached" if state.get("notified_claims_1490") else "⏳ Pending"
    ref1_status = "✅ Reached" if state.get("notified_ref_143") else "⏳ Pending"
    ref2_status = "✅ Reached" if state.get("notified_ref_145") else "⏳ Pending"

    msg = (
        "📊 <b>ETERNAL VÄINÄMÖINEN STATS</b>\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
        "💰 <b>MRR Progress</b>\n"
        f"• Current: <b>{mrr_val}</b>\n"
        f"• Target (€3985): {t2_status}\n\n"
        "🏆 <b>Claims Progress</b>\n"
        f"• Current Claims: <b>{claims_val}</b>\n"
        f"• Target (1490): {claims_status}\n\n"
        "🤝 <b>Referral Milestones</b>\n"
        f"• Current Referrals: <b>{refs_val}</b>\n"
        f"• Target 1 (143): {ref1_status}\n"
        f"• Target 2 (145): {ref2_status}\n\n"
        "📦 <b>Active Stock Watches:</b>\n"
        f"<code>{', '.join(TARGET_PLANS)}</code>"
    )
    send_telegram(msg)

def check_telegram_commands(last_update_id, state):
    if not TG_TOKEN:
        return last_update_id
    url = f"https://api.telegram.org/bot{TG_TOKEN}/getUpdates"
    params = {"offset": last_update_id + 1, "timeout": 0}
    try:
        res = requests.get(url, params=params, timeout=5)
        if res.status_code == 200:
            data = res.json()
            for update in data.get("result", []):
                update_id = update["update_id"]
                last_update_id = max(last_update_id, update_id)
                
                message = update.get("message", {})
                chat_id = str(message.get("chat", {}).get("id"))
                text = message.get("text", "").strip().lower()

                if chat_id == str(TG_CHAT_ID).strip():
                    if text.startswith("/stats"):
                        handle_stats_command(state)
                    elif text.startswith("/help") or text.startswith("/start"):
                        send_telegram("💡 <b>Available Commands:</b>\n\n<code>/stats</code> — View current campaign progress\n<code>/help</code> — Show guide")
    except Exception as e:
        print(f"Error checking Telegram commands: {e}", flush=True)
    return last_update_id

if __name__ == "__main__":
    print("Bot initializing...", flush=True)
    send_telegram("🚀 Heroku Bot Active! Tracking packages & commands ready.\nUse /stats to view milestones.")

    state = {
        "notified_mrr_3985": False,
        "notified_claims_1490": False,
        "notified_ref_143": False,
        "notified_ref_145": False
    }

    last_update_id = 0
    try:
        flush_res = requests.get(f"https://api.telegram.org/bot{TG_TOKEN}/getUpdates", params={"offset": -1}, timeout=5)
        if flush_res.status_code == 200 and flush_res.json().get("result"):
            last_update_id = flush_res.json()["result"][-1]["update_id"]
    except Exception as e:
        print(f"Initial update flush failed: {e}", flush=True)

    while True:
        last_update_id = check_telegram_commands(last_update_id, state)

        # --- TASK 1: CHECK CAMPAIGN MILESTONES ---
        try:
            needs_camp_check = (
                (not state["notified_mrr_3985"])
                or (not state["notified_claims_1490"])
                or (not state["notified_ref_143"])
                or (not state["notified_ref_145"])
            )

            if needs_camp_check:
                camp_data = parse_campaign_data()

                # MRR €3985 Milestone Check
                if camp_data["mrr"] is not None:
                    curr_mrr = camp_data["mrr"]
                    if curr_mrr >= 3985.0 and not state["notified_mrr_3985"]:
                        send_telegram(f"💰 <b>REVENUE MILESTONE REACHED!</b> 💰\n\nThe campaign MRR has reached <b>€{curr_mrr}</b> (Target: €3985+).\n🔗 <a href='{CAMPAIGN_URL}'>View Campaign</a>")
                        state["notified_mrr_3985"] = True

                # Claims 1490 Milestone Check
                if camp_data["claims"] is not None and not state["notified_claims_1490"]:
                    curr_claims = camp_data["claims"]
                    if curr_claims >= 1490:
                        send_telegram(f"🏆 <b>CLAIM MILESTONE REACHED!</b> 🏆\n\nTotal claims have reached <b>{curr_claims}</b> (Target: 1490).\n🔗 <a href='{CAMPAIGN_URL}'>View Campaign</a>")
                        state["notified_claims_1490"] = True

                # Referrals 143 & 145 Milestones Check
                if camp_data["referrals"] is not None:
                    curr_refs = camp_data["referrals"]
                    if curr_refs >= 143 and not state["notified_ref_143"]:
                        send_telegram(f"🤝 <b>REFERRAL MILESTONE!</b> 🤝\n\nGlobal referrals reached <b>{curr_refs}</b> (Target: 143)!\n🔗 <a href='{CAMPAIGN_URL}'>View Campaign</a>")
                        state["notified_ref_143"] = True

                    if curr_refs >= 145 and not state["notified_ref_145"]:
                        send_telegram(f"🤝 <b>REFERRAL MILESTONE!</b> 🤝\n\nGlobal referrals reached <b>{curr_refs}</b> (Target: 145)!\n🔗 <a href='{CAMPAIGN_URL}'>View Campaign</a>")
                        state["notified_ref_145"] = True

        except Exception as e:
            print(f"Error in milestone loop: {e}", flush=True)

        # --- TASK 2: CHECK STORE STOCK ---
        try:
            res = requests.get(STORE_URL, headers=headers, timeout=15)
            if res.status_code == 200:
                raw_html = res.text
                for plan in TARGET_PLANS:
                    if plan in raw_html:
                        parts = raw_html.split(plan)
                        status_chunk = parts[1][:500].lower()

                        is_unavailable = "0 available" in status_chunk or "out of stock" in status_chunk or "out stock" in status_chunk
                        is_orderable = "available" in status_chunk or "open" in status_chunk or "order" in status_chunk or "get one" in status_chunk

                        if not is_unavailable and is_orderable:
                            pid_match = re.search(r'pid=(\d+)', parts[1][:600])
                            if pid_match:
                                found_pid = pid_match.group(1)
                                pid_text = f"\n🔑 <b>Product ID (PID):</b> <code>{found_pid}</code>\n⚡ <a href='{BASE_CART_URL}{found_pid}'>Instant Checkout Link</a>"
                            else:
                                pid_text = f"\n🔗 <a href='{STORE_URL}'>Store Page Link</a>"

                            send_telegram(f"🚨 <b>STOCK ALERT:</b> [{plan}] IS LIVE! 🚨\n\n📦 <b>Plan Match:</b> {plan}{pid_text}")
        except Exception as e:
            print(f"Error in stock loop: {e}", flush=True)

        for _ in range(CHECK_INTERVAL):
            last_update_id = check_telegram_commands(last_update_id, state)
            time.sleep(1)
