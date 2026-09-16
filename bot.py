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

def parse_campaign_data():
    """Scrapes the campaign page and returns current numbers for MRR, claims, and referrals."""
    stats = {"mrr": None, "claims": None, "referrals": None}
    try:
        res = requests.get(CAMPAIGN_URL, headers=headers, timeout=15)
        if res.status_code == 200:
            html = res.text
            
            # MRR parse
            if "MRR: €" in html:
                mrr_part = html.split("MRR: €")[1]
                raw_mrr = mrr_part.split("<")[0].split("·")[0].strip()
                clean_mrr = "".join(c for c in raw_mrr if c.isdigit() or c == '.').rstrip('.')
                if clean_mrr:
                    stats["mrr"] = float(clean_mrr)

            # Claims parse
            if "Claimed in the campaign:" in html:
                claim_part = html.split("Claimed in the campaign:")[1]
                raw_claims = claim_part.split("/")[0].strip()
                clean_claims = "".join(c for c in raw_claims if c.isdigit())
                if clean_claims:
                    stats["claims"] = int(clean_claims)

            # Referrals parse
            if "REFERRAL MILESTONES" in html.upper():
                chunk = html[html.upper().find("REFERRAL MILESTONES"):][:1200]
                ref_match = re.search(r'(\d+)\s+so far', chunk, re.IGNORECASE)
                if ref_match:
                    stats["referrals"] = int(ref_match.group(1))
    except Exception as e:
        print(f"Error parsing campaign stats: {e}", flush=True)
    return stats

def check_telegram_commands(last_update_id, state):
    """Listens for inbound slash commands like /stats."""
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
                text = message.get("text", "").strip()

                # Authorize incoming command
                if chat_id == str(TG_CHAT_ID):
                    if text.startswith("/stats"):
                        handle_stats_command(state)
                    elif text.startswith("/help") or text.startswith("/start"):
                        send_telegram("💡 *Available Commands:*\n\n`/stats` — View current campaign progress & active thresholds\n`/help` — Show this guide")
    except Exception:
        pass
    return last_update_id

def handle_stats_command(state):
    stats = parse_campaign_data()
    mrr_val = f"€{stats['mrr']}" if stats["mrr"] is not None else "Pending..."
    claims_val = f"{stats['claims']}" if stats["claims"] is not None else "Pending..."
    refs_val = f"{stats['referrals']}" if stats["referrals"] is not None else "Pending..."

    msg = (
        f"📊 *ETERNAL VÄINÄMÖINEN STATS*\n"
        f"━━━━━━━━━━━━━━━━━━━\n\n"
        f"💰 *MRR Progress*\n"
        f"• Current: *{mrr_val}*\n"
        f"• Target 1 (€1950): {'✅ Alert Sent' if state['revenue_alerts_sent'] >= 2 else f'{state[\"revenue_alerts_sent\"]}/2 Alerts'}\n"
        f"• Target 2 (€3985): {'✅ Reached' if state['notified_mrr_3985'] else '⏳ Pending'}\n\n"
        f"🏆 *Claims Progress*\n"
        f"• Current Claims: *{claims_val}*\n"
        f"• Target (1490): {'✅ Reached' if state['notified_claims_1490'] else '⏳ Pending'}\n\n"
        f"🤝 *Referral Milestones*\n"
        f"• Current Referrals: *{refs_val}*\n"
        f"• Target 1 (143): {'✅ Reached' if state['notified_ref_143'] else '⏳ Pending'}\n"
        f"• Target 2 (145): {'✅ Reached' if state['notified_ref_145'] else '⏳ Pending'}\n\n"
        f"📦 *Active Stock Watches:*\n"
        f"`{', '.join(TARGET_PLANS)}`"
    )
    send_telegram(msg)

if __name__ == "__main__":
    send_telegram("🚀 Heroku Bot Active! Tracking packages & commands ready.\nUse `/stats` to view milestones.")

    state = {
        "revenue_alerts_sent": 0,
        "notified_mrr_3985": False,
        "notified_claims_1490": False,
        "notified_ref_143": False,
        "notified_ref_145": False
    }

    last_update_id = 0
    # Clear out any stale pending commands before startup
    try:
        flush_res = requests.get(f"https://api.telegram.org/bot{TG_TOKEN}/getUpdates", params={"offset": -1}, timeout=5)
        if flush_res.status_code == 200 and flush_res.json().get("result"):
            last_update_id = flush_res.json()["result"][-1]["update_id"]
    except Exception:
        pass

    while True:
        # Check for incoming /stats requests immediately
        last_update_id = check_telegram_commands(last_update_id, state)

        # --- TASK 1: CHECK CAMPAIGN MILESTONES ---
        try:
            needs_camp_check = (
                (state["revenue_alerts_sent"] < 2)
                or (not state["notified_mrr_3985"])
                or (not state["notified_claims_1490"])
                or (not state["notified_ref_143"])
                or (not state["notified_ref_145"])
            )

            if needs_camp_check:
                camp_data = parse_campaign_data()

                # MRR milestones
                if camp_data["mrr"] is not None:
                    curr_mrr = camp_data["mrr"]
                    if curr_mrr >= 1950.0 and state["revenue_alerts_sent"] < 2:
                        send_telegram(f"💰 *REVENUE MILESTONE REACHED!* 💰\n\nThe campaign MRR has hit *€{curr_mrr}* (Target: €1950+).\n🔗 [View Campaign]({CAMPAIGN_URL})")
                        state["revenue_alerts_sent"] += 1

                    if curr_mrr >= 3985.0 and not state["notified_mrr_3985"]:
                        send_telegram(f"💰 *REVENUE MILESTONE REACHED!* 💰\n\nThe campaign MRR has reached *€{curr_mrr}* (Target: €3985+).\n🔗 [View Campaign]({CAMPAIGN_URL})")
                        state["notified_mrr_3985"] = True

                # Claims milestone
                if camp_data["claims"] is not None and not state["notified_claims_1490"]:
                    curr_claims = camp_data["claims"]
                    if curr_claims >= 1490:
                        send_telegram(f"🏆 *CLAIM MILESTONE REACHED!* 🏆\n\nTotal claims have reached *{curr_claims}* (Target: 1490).\n🔗 [View Campaign]({CAMPAIGN_URL})")
                        state["notified_claims_1490"] = True

                # Referral milestones
                if camp_data["referrals"] is not None:
                    curr_refs = camp_data["referrals"]
                    if curr_refs >= 143 and not state["notified_ref_143"]:
                        send_telegram(f"🤝 *REFERRAL MILESTONE!* 🤝\n\nGlobal referrals reached *{curr_refs}* (Target: 143)!\n🔗 [View Campaign]({CAMPAIGN_URL})")
                        state["notified_ref_143"] = True

                    if curr_refs >= 145 and not state["notified_ref_145"]:
                        send_telegram(f"🤝 *REFERRAL MILESTONE!* 🤝\n\nGlobal referrals reached *{curr_refs}* (Target: 145)!\n🔗 [View Campaign]({CAMPAIGN_URL})")
                        state["notified_ref_145"] = True

        except Exception as e:
            print(f"Error in milestone loop: {e}", flush=True)

        # --- TASK 2: CHECK STORE STOCK & EXTRACT PID ---
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
                                pid_text = f"\n🔑 *Product ID (PID):* `{found_pid}`\n⚡ [Instant Checkout Link]({BASE_CART_URL}{found_pid})"
                            else:
                                pid_text = f"\n🔗 [Store Page Link]({STORE_URL})"

                            send_telegram(f"🚨 *STOCK ALERT:* [{plan}] IS LIVE! 🚨\n\n📦 *Plan Match:* {plan}{pid_text}")
        except Exception as e:
            print(f"Error in stock loop: {e}", flush=True)

        # Sleep in short increments so incoming /stats replies are near-instant
        for _ in range(CHECK_INTERVAL):
            last_update_id = check_telegram_commands(last_update_id, state)
            time.sleep(1)
