import os
import json
import requests
from openai import OpenAI

API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME   = os.getenv("MODEL_NAME", "gpt-4o")
HF_TOKEN     = os.getenv("HF_TOKEN")
BASE_URL     = os.getenv("VERIFYIQ_URL", "http://localhost:8000")

client = OpenAI(
    api_key=HF_TOKEN,
    base_url=API_BASE_URL
)

SYSTEM_PROMPT = """You are a D2C customer support agent handling WhatsApp messages.

You will receive a JSON object with customer message details.

Your rules:
1. Reply in the SAME language as the customer
2. Show empathy FIRST if tone is frustrated or urgent
3. NEVER issue refund if claim_truth_label is "false"
4. Use action_type "reject" if claim is false
5. Use action_type "escalate" if suspicious
6. Use action_type "refund" only if verified
7. Keep response under 3 sentences

Return ONLY valid JSON:
{
  "response_text": "...",
  "detected_intent": "refund|tracking|complaint|query",
  "response_language": "hindi|hinglish|english|pidgin|bahasa",
  "action_type": "refund|escalate|inform|reject"
}"""


def call_llm(observation: dict) -> dict:
    response = client.chat.completions.create(
        model=MODEL_NAME,
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(observation)}
        ]
    )
    content = response.choices[0].message.content.strip()
    content = content.replace("```json", "").replace("```", "").strip()
    return json.loads(content)


def run_task(task_id: int) -> float:
    print(f"\n{'='*50}")
    print(f"  Running Task {task_id}")
    print(f"{'='*50}")

    reset_resp = requests.post(
        f"{BASE_URL}/reset",
        json={"task_id": task_id, "region": "india"},
        timeout=10
    )
    reset_resp.raise_for_status()
    data = reset_resp.json()

    observation = data.get("observation", data)
    done = data.get("done", False)
    scores = []
    step = 0

    while not done:
        step += 1
        try:
            action = call_llm(observation)
        except Exception as e:
            print(f"  Step {step}: LLM error - {e}")
            action = {
                "response_text": "I understand your concern. Let me check this for you.",
                "detected_intent": observation.get("intent", "query"),
                "response_language": observation.get("language", "english"),
                "action_type": "inform"
            }

        step_resp = requests.post(
            f"{BASE_URL}/step",
            json=action,
            timeout=10
        )
        step_resp.raise_for_status()
        step_data = step_resp.json()

        reward_score = step_data.get("reward", {}).get("score", 0.0)
        scores.append(reward_score)
        done = step_data.get("done", False)
        observation = step_data.get("observation", {})

        label = observation.get("claim_truth_label", "?") if not done else "done"
        print(f"  Step {step:02d} | score: {reward_score:.2f} | action: {action.get('action_type')} | claim: {label}")

    avg = sum(scores) / len(scores) if scores else 0.0
    print(f"\n  Task {task_id} complete - avg score: {avg:.4f}")
    return round(avg, 4)


def main():
    print("\nVerifyIQ-Env Inference Script")
    print(f"Server:    {BASE_URL}")
    print(f"Model:     {MODEL_NAME}")
    print(f"API Base:  {API_BASE_URL}\n")

    try:
        health = requests.get(f"{BASE_URL}/health", timeout=5)
        if health.status_code != 200:
            print("ERROR: Server not responding.")
            return
    except Exception:
        print("ERROR: Cannot connect to server.")
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
    print("  RESULTS")
    print(f"{'='*50}")
    print(f"  Task 1 (Easy)   -> {results.get('task_1', 0):.4f}")
    print(f"  Task 2 (Medium) -> {results.get('task_2', 0):.4f}")
    print(f"  Task 3 (Hard)   -> {results.get('task_3', 0):.4f}")
    print(f"{'='*50}\n")

    with open("inference_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("Results saved to inference_results.json")


if __name__ == "__main__":
    main()