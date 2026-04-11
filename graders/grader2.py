def grade(episode_log: list) -> float:
    if not episode_log:
        return 0.01

    total = len(episode_log)
    fraud_caught = 0
    fraud_missed = 0
    correct_actions = 0

    CORRECT_ACTIONS = {
        "order_status":   ["track_order", "reply_only"],
        "refund_request": ["initiate_refund", "investigate_first"],
        "complaint":      ["reply_only", "escalate_human"],
        "general_query":  ["reply_only"]
    }

    for entry in episode_log:
        intent = entry.get("intent", "general_query")
        action = entry.get("action_type", "")
        truth = entry.get("claim_truth_label", "verified")

        if action in CORRECT_ACTIONS.get(intent, []):
            correct_actions += 1

        if truth == "false":
            if action == "investigate_first":
                fraud_caught += 1
            elif action == "initiate_refund":
                fraud_missed += 1

    total_fraud = fraud_caught + fraud_missed
    fraud_score = fraud_caught / total_fraud if total_fraud > 0 else 1.0
    action_score = correct_actions / total

    final = (fraud_score * 0.60) + (action_score * 0.40)
    return min(max(round(final, 2), 0.01), 0.99)
