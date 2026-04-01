class StateManager:

    def __init__(self):
        self.queue = []
        self.current_message = None
        self.metrics = {
            "resolved": 0,
            "escalated": 0,
            "fraud_caught": 0,
            "fraud_missed": 0,
            "csat_scores": [],
            "shift_minutes": 240
        }

    def load_queue(self, messages: list):
        self.queue = messages.copy()
        self.metrics = {
            "resolved": 0,
            "escalated": 0,
            "fraud_caught": 0,
            "fraud_missed": 0,
            "csat_scores": [],
            "shift_minutes": 240
        }

    def next_message(self):
        if self.queue:
            self.current_message = self.queue.pop(0)
            return self.current_message
        return None

    def update(self, action_type: str, reward_value: float):
        if action_type in ["reply_only", "track_order",
                           "initiate_refund", "investigate_first"]:
            self.metrics["resolved"] += 1
        if action_type == "escalate_human":
            self.metrics["escalated"] += 1
        self.metrics["csat_scores"].append(reward_value)
        self.metrics["shift_minutes"] -= 5

    def get_snapshot(self) -> dict:
        scores = self.metrics["csat_scores"]
        return {
            "queue_remaining": len(self.queue),
            "resolved": self.metrics["resolved"],
            "escalated": self.metrics["escalated"],
            "fraud_caught": self.metrics["fraud_caught"],
            "avg_csat": sum(scores) / len(scores) if scores else 0.0,
            "shift_minutes_left": self.metrics["shift_minutes"]
        }
