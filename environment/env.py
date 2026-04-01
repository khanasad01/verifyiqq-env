from environment.models import Observation, Action, Reward
from environment.state_manager import StateManager

SAMPLE_MESSAGES = [
    {
        "message": "bhai mera order 5 din pehle aaya aur bilkul toot hua tha",
        "customer_id": "C001",
        "order_id": "ORD001",
        "language": "hinglish",
        "tone": "frustrated",
        "intent": "refund_request",
        "claim_truth_score": 0.2,
        "claim_truth_label": "false",
        "region": "india"
    },
    {
        "message": "where is my order, it has been 3 days",
        "customer_id": "C002",
        "order_id": "ORD002",
        "language": "en",
        "tone": "neutral",
        "intent": "order_status",
        "claim_truth_score": 0.9,
        "claim_truth_label": "verified",
        "region": "india"
    },
    {
        "message": "mujhe refund chahiye abhi",
        "customer_id": "C003",
        "order_id": "ORD003",
        "language": "hi",
        "tone": "urgent",
        "intent": "refund_request",
        "claim_truth_score": 0.8,
        "claim_truth_label": "verified",
        "region": "india"
    },
    {
        "message": "item quality bohot kharab thi",
        "customer_id": "C004",
        "order_id": "ORD004",
        "language": "hinglish",
        "tone": "frustrated",
        "intent": "complaint",
        "claim_truth_score": 0.6,
        "claim_truth_label": "suspicious",
        "region": "india"
    },
    {
        "message": "what is your return policy",
        "customer_id": "C005",
        "order_id": None,
        "language": "en",
        "tone": "neutral",
        "intent": "general_query",
        "claim_truth_score": 1.0,
        "claim_truth_label": "verified",
        "region": "india"
    }
]

class ContextIQEnv:

    def __init__(self):
        self.state_manager = StateManager()
        self.current_obs = None

    def reset(self) -> Observation:
        self.state_manager.load_queue(SAMPLE_MESSAGES.copy())
        msg = self.state_manager.next_message()
        self.current_obs = self._build_observation(msg)
        return self.current_obs

    def step(self, action: Action):
        reward = self._calculate_reward(action)
        self.state_manager.update(action.action_type, reward.value)
        msg = self.state_manager.next_message()
        if msg:
            obs = self._build_observation(msg)
            done = False
        else:
            obs = self.current_obs
            done = True
        self.current_obs = obs
        return obs, reward, done, self.state_manager.get_snapshot()

    def state(self) -> dict:
        return self.state_manager.get_snapshot()

    def _build_observation(self, msg: dict) -> Observation:
        return Observation(
            message=msg["message"],
            language=msg["language"],
            tone=msg["tone"],
            intent=msg["intent"],
            customer_id=msg["customer_id"],
            order_id=msg.get("order_id"),
            claim_truth_score=msg.get("claim_truth_score", 1.0),
            claim_truth_label=msg.get("claim_truth_label", "verified"),
            region=msg.get("region", "india"),
            queue_size=len(self.state_manager.queue)
        )

    def _calculate_reward(self, action: Action) -> Reward:
        reward = 0.0
        breakdown = {}
        obs = self.current_obs

        CORRECT_ACTIONS = {
            "order_status":   ["track_order", "reply_only"],
            "refund_request": ["initiate_refund", "investigate_first"],
            "complaint":      ["reply_only", "escalate_human"],
            "general_query":  ["reply_only"]
        }

        if action.action_type in CORRECT_ACTIONS.get(obs.intent, []):
            reward += 0.40
            breakdown["intent_match"] = 0.40
        else:
            reward -= 0.20
            breakdown["intent_mismatch"] = -0.20

        if obs.claim_truth_label == "false":
            if action.action_type == "initiate_refund":
                reward -= 0.50
                breakdown["fraud_enabled"] = -0.50
                self.state_manager.metrics["fraud_missed"] += 1
            elif action.action_type == "investigate_first":
                reward += 0.30
                breakdown["fraud_caught"] = 0.30
                self.state_manager.metrics["fraud_caught"] += 1

        if obs.tone == "frustrated":
            empathy_words = [
                "samajh sakta hoon", "bilkul theek hai",
                "i understand", "sorry", "zaroor help",
                "main dekh raha hoon", "haan ji"
            ]
            has_empathy = any(
                w in action.reply_message.lower()
                for w in empathy_words
            )
            if has_empathy:
                reward += 0.20
                breakdown["empathy_shown"] = 0.20
            else:
                reward -= 0.15
                breakdown["empathy_missing"] = -0.15

        final = max(-1.0, min(1.0, reward))

        if final >= 0.6:
            explanation = "Sahi action liya. Claim verify kiya, empathy di."
            tip = "Aise hi karo — verify first, then act."
        elif final >= 0.2:
            explanation = "Thoda sahi, thoda galat. Improvement possible hai."
            tip = "Frustrated customer ko pehle empathy do."
        else:
            explanation = "Galat action — fraud enable hua ya intent miss hua."
            tip = "Jab claim_truth_label = false ho, investigate_first lo."

        return Reward(
            value=final,
            breakdown=breakdown,
            explanation=explanation,
            learning_tip=tip
        )
