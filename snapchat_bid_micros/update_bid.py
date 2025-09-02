import requests
from decimal import Decimal

ADS_API = "https://adsapi.snapchat.com/v1"

def usd_to_micro(usd: str | float) -> int:
    # Use Decimal to avoid float rounding issues
    return int((Decimal(str(usd)) * Decimal(1_000_000)).to_integral_value())

def update_adsquad_bid(adsquad_id: str, new_bid_usd: float, strategy="LOWEST_COST_WITH_MAX_BID"):
    token = get_access_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # 1) Get current ad squad
    r = requests.get(f"{ADS_API}/adsquads/{adsquad_id}", headers=headers, timeout=30)
    r.raise_for_status()
    adsquad = r.json()["adsquads"][0]["adsquad"]

    # 2) Modify bid fields (and anything else you need)
    adsquad["bid_micro"] = usd_to_micro(new_bid_usd)
    adsquad["bid_strategy"] = strategy  # e.g., LOWEST_COST_WITH_MAX_BID or TARGET_COST

    # 3) PUT full object back through the campaign endpoint
    campaign_id = adsquad["campaign_id"]
    payload = {"adsquads": [adsquad]}
    r2 = requests.put(f"{ADS_API}/campaigns/{campaign_id}/adsquads", json=payload, headers=headers, timeout=30)
    r2.raise_for_status()
    return r2.json()
