from pydantic import BaseModel
from typing import Optional

class Observation(BaseModel):
    message: str
    language: str
    tone: str
    intent: str
    customer_id: str
    order_id: Optional[str] = None
    claim_truth_score: float = 1.0
    claim_truth_label: str = "verified"
    region: str = "india"
    queue_size: int = 0

class Action(BaseModel):
    action_type: str
    reply_message: str
    order_id: Optional[str] = None
    refund_amount: Optional[float] = None

class Reward(BaseModel):
    value: float
    breakdown: dict
    explanation: str
    learning_tip: str