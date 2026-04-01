import re

HINGLISH_WORDS = [
    "hai", "hain", "kya", "nahi", "kar", "mera", "tera",
    "bhai", "yaar", "aur", "se", "ko", "ka", "ki", "ke",
    "ho", "tha", "main", "tum", "aap", "karo", "chahiye",
    "bohot", "bahut", "accha", "theek", "haan", "bilkul",
    "zaroor", "abhi", "jaldi", "please", "help", "dedo",
    "kahan", "kyun", "kaise", "kitna", "wala", "wali"
]

def detect_language(text: str) -> str:
    if not text:
        return "en"

    if re.search(r'[\u0900-\u097F]', text):
        return "hi"

    text_lower = text.lower()
    words = text_lower.split()
    hinglish_count = sum(
        1 for word in words
        if word in HINGLISH_WORDS
    )

    if hinglish_count >= 1:
        return "hinglish"

    return "en"
