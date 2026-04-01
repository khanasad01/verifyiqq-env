import os
import json
import requests

BASE_URL = os.getenv("VERIFYIQ_URL", "http://localhost:8000")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable not set")

SYSTEM_PROMPT = """You are a D2C customer support agent handling WhatsApp messages.

You will receive a JSON object with:
- message: raw customer message (may be Hinglish)
- language: detected language
- intent: what they want (refund_request/order_status/complaint/general_query)
- tone: emotional state (frustrated/urgent/casual/neutral)
- claim_truth_score: float 0.0 to 1.0
- claim_truth_label: verified / suspicious / false
- region: india/usa/nigeria/indonesia

Your rules:
1. Show empathy FIRST if tone is frustrated or urgent
2. NEVER use initiate_refund if claim_truth_label is false
3. Use investigate_first if claim is suspicious
4. Use initiate_refund only if claim is verified
5. Use escalate_human for complex issues
6. Keep reply_message under 3 sentences

Return ONLY valid JSON, no markdown:
{
  "action_type": "reply_only|track_order|initiate_refund|investigate_first|escalate_human",
  "reply_message": "your response to customer",
  "order_id": null,
  "refund_amount": null
}"""


def call_openai(observation: dict) -> dict:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    payload = {
        "model": "gpt-4o",
        "temperature": 0,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(observation)}
        ]
    }
    resp = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=30
    )
    resp.raise_for_status()
    content = resp.json()["choices"][0]["message"]["content"].strip()
    content = content.replace("```json", "").replace("```", "").strip()
    return json.loads(content)


def run_task(task_id: int) -> float:
    print(f"\n{'='*50}")
    print(f"  Running Task {task_id}")
    print(f"{'='*50}")

    reset_resp = requests.post(f"{BASE_URL}/reset", timeout=10)
    reset_resp.raise_for_status()
    observation = reset_resp.json()
    done = False
    scores = []
    step = 0

    while not done:
        step += 1
        try:
            action = call_openai(observation)
        except Exception as e:
            print(f"  Step {step}: OpenAI error - {e}")
            action = {
                "action_type": "reply_only",
                "reply_message": "I understand your concern. Let me check this for you.",
                "order_id": None,
                "refund_amount": None
            }

        step_resp = requests.post(f"{BASE_URL}/step", json=action, timeout=10)
        step_resp.raise_for_status()
        step_data = step_resp.json()

        reward = step_data.get("reward", {})
        reward_score = reward.get("value", reward.get("score", 0.0))
        scores.append(reward_score)
        done = step_data.get("done", False)
        observation = step_data.get("observation", observation)

        label = observation.get("claim_truth_label", "?") if not done else "done"
        print(f"  Step {step:02d} | score: {reward_score:.2f} | action: {action.get('action_type')} | claim: {label}")

    avg = sum(scores) / len(scores) if scores else 0.0
    print(f"\n  Task {task_id} complete - avg score: {avg:.4f} ({len(scores)} steps)")
    return round(avg, 4)


def main():
    print("\nVerifyIQ-Env Baseline Agent")
    print(f"Server: {BASE_URL}")
    print(f"Model:  gpt-4o (temperature=0)\n")

    try:
        health = requests.get(f"{BASE_URL}/health", timeout=5)
        if health.status_code != 200:
            print("ERROR: Server not responding.")
            return
    except Exception:
        print("ERROR: Cannot connect to server. Start uvicorn first.")
        return

    results = {}
    for task_id in [1, 2, 3]:
        try:
            score = run_task(task_id)
            results[f"task_{task_id}"] = score
        except Exception as e:
            print(f"Task {task_id} failed: {e}")
            results[f"task_{task_id}"] = 0.0

    print(f"\n{'='*50}")
    print("  BASELINE RESULTS")
    print(f"{'='*50}")
    print(f"  Task 1 (Easy)   -> {results.get('task_1', 0):.4f}")
    print(f"  Task 2 (Medium) -> {results.get('task_2', 0):.4f}")
    print(f"  Task 3 (Hard)   -> {results.get('task_3', 0):.4f}")
    print(f"{'='*50}\n")

    with open("baseline_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("Results saved to baseline_results.json")


if __name__ == "__main__":
    main()