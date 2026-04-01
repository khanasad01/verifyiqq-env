from environment.models import Action, Reward, Observation
from verifier.claim_extractor import extract_claims
from verifier.claim_validator import validate_claims

CORRECT_ACTIONS = {
    "order_status":   ["track_order", "reply_only"],
    "refund_request": ["initiate_refund", "investigate_first"],
    "complaint":      ["reply_only", "escalate_human"],
    "general_query":  ["reply_only"]
}

EMPATHY_WORDS = [
    "samajh sakta hoon", "bilkul theek hai",
    "i understand", "sorry", "zaroor help",
    "main dekh raha hoon", "haan ji", "of course"
]

def calculate_reward(action: Action, obs: Observation) -> Reward:
    reward = 0.0
    breakdown = {}

    # Intent match
    if action.action_type in CORRECT_ACTIONS.get(obs.intent, []):
        reward += 0.40
        breakdown["intent_match"] = 0.40
    else:
        reward -= 0.20
        breakdown["intent_mismatch"] = -0.20

    # Fraud detection
    if obs.claim_truth_label == "false":
        if action.action_type == "initiate_refund":
            reward -= 0.50
            breakdown["fraud_enabled"] = -0.50
        elif action.action_type == "investigate_first":
            reward += 0.30
            breakdown["fraud_caught"] = 0.30

    if obs.claim_truth_label == "suspicious":
        if action.action_type == "investigate_first":
            reward += 0.20
            breakdown["suspicious_handled"] = 0.20
        elif action.action_type == "initiate_refund":
            reward -= 0.20
            breakdown["suspicious_refunded"] = -0.20

    # Empathy check
    if obs.tone == "frustrated":
        has_empathy = any(
            w in action.reply_message.lower()
            for w in EMPATHY_WORDS
        )
        if has_empathy:
            reward += 0.20
            breakdown["empathy_shown"] = 0.20
        else:
            reward -= 0.15
            breakdown["empathy_missing"] = -0.15

    # Language match
    if obs.language == "hinglish" or obs.language == "hi":
        hinglish_words = ["hoon", "karta", "main", "aap", "bhai", "ji"]
        has_hinglish = any(
            w in action.reply_message.lower()
            for w in hinglish_words
        )
        if has_hinglish:
            reward += 0.10
            breakdown["language_match"] = 0.10

    # Unnecessary escalation penalty
    if action.action_type == "escalate_human":
        if obs.intent == "general_query":
            reward -= 0.30
            breakdown["unnecessary_escalation"] = -0.30

    final = max(-1.0, min(1.0, reward))

    if final >= 0.6:
        explanation = "Sahi action liya. Claim verify kiya aur empathy di."
        tip = "Aise hi karo — verify first, empathy first, then act."
    elif final >= 0.2:
        explanation = "Kuch sahi tha lekin improvement ki jagah hai."
        tip = "Frustrated customer ko pehle empathy do. Suspicious claim ko investigate karo."
    else:
        explanation = "Galat action liya — fraud enable hua ya wrong intent handle kiya."
        tip = "Jab claim_truth_label = false ho toh investigate_first lo. Kabhi seedha refund mat do."

    return Reward(
        value=final,
        breakdown=breakdown,
        explanation=explanation,
        learning_tip=tip
    )
