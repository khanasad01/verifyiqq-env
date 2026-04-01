import re

def extract_claims(message: str, order_id: str = None) -> list:
    claims = []
    message_lower = message.lower()

    date_patterns = [
        r'(\d+)\s*din\s*pehle',
        r'(\d+)\s*days?\s*ago',
        r'(\d+)\s*din\s*se',
        r'(\d+)\s*days?\s*back'
    ]
    for pattern in date_patterns:
        match = re.search(pattern, message_lower)
        if match:
            claims.append({
                "type": "delivery_date",
                "claimed_days_ago": int(match.group(1)),
                "order_id": order_id
            })
            break

    condition_keywords = {
        "damaged": ["toot", "broken", "damaged", "toot hua", "phoot"],
        "not_working": ["kaam nahi", "not working", "band hai", "chalu nahi"],
        "wrong_item": ["wrong item", "galat item", "alag item", "wrong product"]
    }
    for condition, keywords in condition_keywords.items():
        if any(kw in message_lower for kw in keywords):
            claims.append({
                "type": "item_condition",
                "claimed_condition": condition,
                "order_id": order_id
            })
            break

    missing_keywords = [
        "nahi aaya", "not delivered", "missing",
        "nahi mila", "deliver nahi", "nahi pahuncha"
    ]
    if any(kw in message_lower for kw in missing_keywords):
        claims.append({
            "type": "non_delivery",
            "order_id": order_id
        })

    return claims
