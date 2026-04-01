from environment.env import ContextIQEnv
from environment.models import Action
from tasks.task1 import TASK1_MESSAGES
from tasks.task2 import TASK2_MESSAGES
from tasks.task3 import TASK3_MESSAGES
from graders.grader1 import grade as grade1
from graders.grader2 import grade as grade2
from graders.grader3 import grade as grade3

GOOD_ACTIONS = {
    "order_status":   "track_order",
    "refund_request": "investigate_first",
    "complaint":      "reply_only",
    "general_query":  "reply_only"
}

def run_task(messages, grader, name):
    env = ContextIQEnv()
    env.state_manager.load_queue(messages.copy())
    env.current_obs = env._build_observation(
        env.state_manager.next_message()
    )
    episode_log = []
    done = False
    while not done:
        obs = env.current_obs
        action_type = GOOD_ACTIONS.get(obs.intent, "reply_only")
        action = Action(
            action_type=action_type,
            reply_message="i understand, main help karta hoon aapki zaroor"
        )
        episode_log.append({
            "message": obs.message,
            "action_type": action_type,
            "intent": obs.intent,
            "tone": obs.tone,
            "claim_truth_label": obs.claim_truth_label,
            "reply_message": action.reply_message
        })
        obs, reward, done, info = env.step(action)
    score = grader(episode_log)
    print(f"{name} SCORE: {score}")
    return score

print("=== ALL TASKS ===")
s1 = run_task(TASK1_MESSAGES, grade1, "TASK 1 (Easy)  ")
s2 = run_task(TASK2_MESSAGES, grade2, "TASK 2 (Medium)")
s3 = run_task(TASK3_MESSAGES, grade3, "TASK 3 (Hard)  ")
print()
print(f"Task 1: {s1} | Task 2: {s2} | Task 3: {s3}")
print("All tasks complete!")
