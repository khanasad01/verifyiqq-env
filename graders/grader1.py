from nlp.intent import classify_intent
from nlp.tone import detect_tone

CORRECT_ACTIONS = {
    "order_status":   ["track_order", "reply_only"],
    "refund_request": ["initiate_refund", "investigate_first"],
    "complaint":      ["reply_only", "escalate_human"],
    "general_query":  ["reply_only"]
}

def grade(episode_log: list) -> float:
    if not episode_log:
        return 0.0

    correct = 0
    total = len(episode_log)

    for entry in episode_log:
        message = entry.get("message", "")
        action_type = entry.get("action_type", "")
        intent = classify_intent(message)
        if action_type in CORRECT_ACTIONS.get(intent, []):
            correct += 1

    score = correct / total
    return min(max(round(score, 2), 0.01), 0.99)
