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

import random

class ContextIQEnv:

    def __init__(self):
        self.state_manager = StateManager()
        self.current_obs = None

    def reset(self, task_id: str = None) -> Observation:
        if task_id == "single_intent_triage":
            from tasks.task1 import TASK1_MESSAGES
            messages = TASK1_MESSAGES
        elif task_id == "hinglish_fraud_detection":
            from tasks.task2 import TASK2_MESSAGES
            messages = TASK2_MESSAGES
        elif task_id == "full_support_shift":
            from tasks.task3 import TASK3_MESSAGES
            messages = TASK3_MESSAGES
        else:
            messages = SAMPLE_MESSAGES

        # SHUFFLE to prevent deterministic behavior on reset
        msg_list = messages.copy()
        random.shuffle(msg_list)
        
        self.state_manager.load_queue(msg_list)
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
        from environment.reward import calculate_reward
        reward_obj = calculate_reward(action, self.current_obs)
        
        # Keep metrics updated based on the robust reward breakdown
        if "fraud_enabled" in reward_obj.breakdown:
            self.state_manager.metrics["fraud_missed"] += 1
        if "fraud_caught" in reward_obj.breakdown:
            self.state_manager.metrics["fraud_caught"] += 1
            
        return reward_obj
