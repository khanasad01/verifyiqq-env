from fastapi import FastAPI
from environment.env import ContextIQEnv
from environment.models import Action
from graders.grader1 import grade as grade1
from graders.grader2 import grade as grade2
from graders.grader3 import grade as grade3

app = FastAPI()
env = ContextIQEnv()

@app.get("/health")
def health():
    return {"status": "ok", "env": "verifyiq-env"}

@app.post("/reset")
def reset():
    obs = env.reset()
    return obs.model_dump()

@app.post("/step")
def step(action: Action):
    obs, reward, done, info = env.step(action)
    return {
        "observation": obs.model_dump(),
        "reward": reward.model_dump(),
        "done": done,
        "info": info
    }

@app.get("/state")
def state():
    return env.state()

@app.get("/tasks")
def get_tasks():
    return {
        "tasks": [
            {
                "id": "single_intent_triage",
                "difficulty": "easy",
                "description": "Handle 10 single-intent messages",
                "action_schema": {
                    "action_type": "str — reply_only / track_order / initiate_refund / investigate_first / escalate_human",
                    "reply_message": "str",
                    "order_id": "str | None",
                    "refund_amount": "float | None"
                }
            },
            {
                "id": "hinglish_fraud_detection",
                "difficulty": "medium",
                "description": "Handle 20 Hinglish messages with 7 false claims"
            },
            {
                "id": "full_support_shift",
                "difficulty": "hard",
                "description": "Handle 40 messages across all regions"
            }
        ]
    }

@app.post("/grader")
def run_grader(task_id: str, episode_log: list):
    graders = {
        "single_intent_triage":    grade1,
        "hinglish_fraud_detection": grade2,
        "full_support_shift":       grade3
    }
    if task_id not in graders:
        return {"error": "Invalid task_id"}
    score = graders[task_id](episode_log)
    return {"task_id": task_id, "score": score}

