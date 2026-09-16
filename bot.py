def parse_campaign_data():
    stats = {"mrr": None, "claims": None, "referrals": None}
    try:
        res = requests.get(CAMPAIGN_URL, headers=headers, timeout=15)
        if res.status_code == 200:
            raw_html = res.text

            # Clean HTML tags and normalize spacing
            text_only = unescape(raw_html)
            text_only = re.sub(r'<[^>]+>', ' ', text_only)
            text_only = re.sub(r'[\xa0\s]+', ' ', text_only)

            # 1. MRR Parser: matches "MRR: € 3080.07"
            mrr_match = re.search(r'MRR[:\s]*€?\s*([0-9\s]+(?:\.[0-9]+)?)', text_only, re.IGNORECASE)
            if mrr_match:
                raw_val = mrr_match.group(1).replace(" ", "").strip()
                if raw_val:
                    try:
                        stats["mrr"] = float(raw_val)
                    except ValueError:
                        pass

            # 2. Claims Parser: matches "Claimed in the campaign: 1 255 / 4 900"
            if "Claimed in the campaign:" in raw_html:
                claim_part = raw_html.split("Claimed in the campaign:")[1]
                raw_claims = claim_part.split("/")[0].strip()
                clean_claims = "".join(c for c in raw_claims if c.isdigit())
                if clean_claims:
                    stats["claims"] = int(clean_claims)

            # 3. Referrals Parser: targets the active "🎯 ... — X so far" tier
            # Priority 1: Match directly after the active target dart emoji
            active_match = re.search(r'🎯[^\n—\-]+[—\-]\s*(\d+)\s+so far', text_only)
            if active_match:
                stats["referrals"] = int(active_match.group(1))
            else:
                # Priority 2: Match the last occurrence of "— X so far" on the page
                all_so_far = re.findall(r'[—\-]\s*(\d+)\s+so far', text_only, re.IGNORECASE)
                if all_so_far:
                    stats["referrals"] = int(all_so_far[-1])

    except Exception as e:
        print(f"Error parsing campaign stats: {e}", flush=True)
    return stats
