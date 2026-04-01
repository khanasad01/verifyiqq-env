import re

REFUND_WORDS = [
    "refund", "wapas", "return", "money back", "paise wapas",
    "vapas karo", "refund chahiye", "refund do", "cancel"
]

ORDER_WORDS = [
    "order", "kahan hai", "where is", "track", "delivery",
    "status", "shipped", "dispatch", "kab aayega", "when"
]

COMPLAINT_WORDS = [
    "kharab", "broken", "damaged", "worst", "bakwaas",
    "bekar", "problem", "issue", "complaint", "wrong",
    "galat", "toot", "missing", "not working"
]

def classify_intent(text: str) -> str:
    text_lower = text.lower()

    refund_score = sum(
        1 for word in REFUND_WORDS
        if word in text_lower
    )
    order_score = sum(
        1 for word in ORDER_WORDS
        if word in text_lower
    )
    complaint_score = sum(
        1 for word in COMPLAINT_WORDS
        if word in text_lower
    )

    max_score = max(refund_score, order_score, complaint_score)

    if max_score == 0:
        return "general_query"
    if refund_score == max_score:
        return "refund_request"
    if order_score == max_score:
        return "order_status"
    return "complaint"
