import json
import os

def load_orders() -> dict:
    path = os.path.join("data", "orders.json")
    with open(path, "r") as f:
        orders = json.load(f)
    return {o["order_id"]: o for o in orders}

def validate_claims(claims: list, order_id: str) -> dict:
    if not claims or not order_id:
        return {
            "truth_score": 1.0,
            "truth_label": "verified",
            "details": "No claims to verify"
        }

    orders = load_orders()
    order = orders.get(order_id)

    if not order:
        return {
            "truth_score": 0.5,
            "truth_label": "suspicious",
            "details": "Order not found in database"
        }

    scores = []
    details = []

    for claim in claims:

        if claim["type"] == "delivery_date":
            claimed = claim["claimed_days_ago"]
            actual = order["delivered_days_ago"]
            diff = abs(claimed - actual)
            if diff == 0:
                scores.append(1.0)
                details.append(f"Delivery date correct: {actual} days ago")
            elif diff <= 1:
                scores.append(0.7)
                details.append(f"Delivery date close: claimed {claimed}, actual {actual}")
            elif diff <= 3:
                scores.append(0.4)
                details.append(f"Delivery date off: claimed {claimed}, actual {actual}")
            else:
                scores.append(0.1)
                details.append(f"Delivery date FALSE: claimed {claimed}, actual {actual}")

        if claim["type"] == "item_condition":
            claimed = claim["claimed_condition"]
            actual = order["actual_condition"]
            has_report = order["damage_report"]
            if actual == claimed and has_report:
                scores.append(1.0)
                details.append(f"Condition verified: {claimed} with damage report")
            elif actual == claimed and not has_report:
                scores.append(0.6)
                details.append(f"Condition matches but no damage report filed")
            else:
                scores.append(0.1)
                details.append(f"Condition FALSE: claimed {claimed}, actual {actual}")

        if claim["type"] == "non_delivery":
            actual = order["delivered_days_ago"]
            if actual is None:
                scores.append(1.0)
                details.append("Non-delivery verified")
            else:
                scores.append(0.0)
                details.append(f"Non-delivery FALSE: order delivered {actual} days ago")

    final_score = sum(scores) / len(scores) if scores else 1.0

    if final_score >= 0.7:
        label = "verified"
    elif final_score >= 0.4:
        label = "suspicious"
    else:
        label = "false"

    return {
        "truth_score": round(final_score, 2),
        "truth_label": label,
        "details": " | ".join(details)
    }
