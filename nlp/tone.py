FRUSTRATED_WORDS = [
    "worst", "bakwaas", "bekar", "terrible", "pathetic",
    "horrible", "disgusting", "useless", "fraud", "cheater",
    "gussa", "angry", "fed up", "ridiculous", "nonsense",
    "kharab", "jhooth", "dhoka"
]

URGENT_WORDS = [
    "urgent", "jaldi", "abhi", "turant", "asap",
    "emergency", "immediately", "right now", "help",
    "please please", "bahut zaroor"
]

CASUAL_WORDS = [
    "bhai", "yaar", "bro", "buddy", "dost",
    "arre", "oye", "yaar suno"
]

def detect_tone(text: str) -> str:
    text_lower = text.lower()

    frustrated_score = sum(
        1 for word in FRUSTRATED_WORDS
        if word in text_lower
    )
    urgent_score = sum(
        1 for word in URGENT_WORDS
        if word in text_lower
    )
    casual_score = sum(
        1 for word in CASUAL_WORDS
        if word in text_lower
    )

    if frustrated_score > 0:
        return "frustrated"
    if urgent_score > 0:
        return "urgent"
    if casual_score > 0:
        return "casual"
    return "neutral"
