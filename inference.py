"""
VerifyIQ-Env — Inference Script
================================
Runs a GPT-4o (or compatible) agent against all 3 tasks in the VerifyIQ-Env
environment and emits structured logs in the required [START]/[STEP]/[END] format.

Environment variables:
  API_BASE_URL   — LLM API endpoint  (default: https://api.openai.com/v1)
  MODEL_NAME     — Model identifier  (default: gpt-4o)
  HF_TOKEN       — API key (HuggingFace token or OpenAI key)
  VERIFYIQ_URL   — Environment server URL (default: http://localhost:8000)
"""

import os
import sys
import json
import requests
from openai import OpenAI

# ── Environment variables (required by hackathon spec) ──────────────────────
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME   = os.getenv("MODEL_NAME",   "gpt-4o")
HF_TOKEN     = os.getenv("HF_TOKEN")
BASE_URL     = os.getenv("VERIFYIQ_URL", "http://localhost:8000")

if not HF_TOKEN:
    print("[ERROR] HF_TOKEN environment variable is not set.", flush=True)
    sys.exit(1)

# ── OpenAI-compatible client (required by hackathon spec) ───────────────────
client = OpenAI(
    api_key=HF_TOKEN,
    base_url=API_BASE_URL
)

# ── Task definitions (string IDs matching openenv.yaml) ─────────────────────
TASKS = [
    {
        "id":         "single_intent_triage",
        "difficulty": "easy",
        "steps":      10,
    },
    {
        "id":         "hinglish_fraud_detection",
        "difficulty": "medium",
        "steps":      20,
    },
    {
        "id":         "full_support_shift",
        "difficulty": "hard",
        "steps":      40,
    },
]

# ── System prompt — action types match the server's Action model exactly ─────
SYSTEM_PROMPT = """You are a D2C customer support agent handling WhatsApp messages.

You will receive a JSON observation with these fields:
- message: raw customer message (may be Hinglish / Hindi / English)
- language: detected language (hi / hinglish / en)
- tone: emotional state (frustrated / urgent / casual / neutral)
- intent: what the customer wants (order_status / refund_request / complaint / general_query)
- claim_truth_score: float 0.0 to 1.0 — how truthful the claim is
- claim_truth_label: verified / suspicious / false
- region: india / usa / nigeria / indonesia

Your decision rules:
1. Show empathy FIRST if tone is frustrated or urgent (use words like "I understand", "sorry", "samajh sakta hoon")
2. NEVER use initiate_refund if claim_truth_label is "false"
3. Use investigate_first if claim_truth_label is "suspicious"
4. Use initiate_refund ONLY if claim_truth_label is "verified"
5. Use track_order for order_status intent
6. Use escalate_human only for genuinely complex issues, not general queries
7. Keep reply_message under 3 sentences
8. Reply in the same language as the customer

Return ONLY valid JSON, no markdown, no extra text:
{
  "action_type": "reply_only | track_order | initiate_refund | investigate_first | escalate_human",
  "reply_message": "your response to the customer",
  "order_id": null,
  "refund_amount": null
}"""


# ── LLM call ────────────────────────────────────────────────────────────────
def call_llm(observation: dict) -> dict:
    """Send an observation to the LLM and return a validated action dict."""
    response = client.chat.completions.create(
        model=MODEL_NAME,
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": json.dumps(observation)}
        ]
    )
    content = response.choices[0].message.content.strip()
    # Strip any accidental markdown code fences
    content = content.replace("```json", "").replace("```", "").strip()
    action = json.loads(content)

    # Validate action_type — fall back safely if LLM hallucinates
    valid_action_types = {
        "reply_only", "track_order", "initiate_refund",
        "investigate_first", "escalate_human"
    }
    if action.get("action_type") not in valid_action_types:
        action["action_type"] = "reply_only"

    # Ensure reply_message exists
    if not action.get("reply_message"):
        action["reply_message"] = "I understand your concern. Let me look into this for you."

    return action


# ── Fallback action when LLM fails ──────────────────────────────────────────
def fallback_action(observation: dict) -> dict:
    """Rule-based fallback so episodes don't crash on LLM errors."""
    intent = observation.get("intent", "general_query")
    claim  = observation.get("claim_truth_label", "verified")
    tone   = observation.get("tone", "neutral")

    empathy = ""
    if tone in ("frustrated", "urgent"):
        empathy = "I understand your concern and I'm sorry for the trouble. "

    intent_map = {
        "order_status":   "track_order",
        "refund_request": "investigate_first" if claim != "verified" else "initiate_refund",
        "complaint":      "reply_only",
        "general_query":  "reply_only",
    }
    action_type = intent_map.get(intent, "reply_only")

    # Never refund false claims even in fallback
    if claim == "false" and action_type == "initiate_refund":
        action_type = "investigate_first"

    return {
        "action_type":   action_type,
        "reply_message": f"{empathy}Let me check this and get back to you right away.",
        "order_id":      observation.get("order_id"),
        "refund_amount": None,
    }


# ── Single task runner ───────────────────────────────────────────────────────
def run_task(task: dict) -> float:
    """
    Runs one task episode and returns the average reward score.
    Emits [START], [STEP], and [END] structured logs to stdout.
    """
    task_id    = task["id"]
    episode_log = []
    scores      = []

    # ── [START] log ──────────────────────────────────────────────────────────
    print(
        f"[START] task_id={task_id} model={MODEL_NAME} "
        f"difficulty={task['difficulty']} server={BASE_URL}",
        flush=True
    )

    # Reset the environment
    try:
        reset_resp = requests.post(f"{BASE_URL}/reset", timeout=15)
        reset_resp.raise_for_status()
    except Exception as e:
        print(f"[ERROR] task_id={task_id} reset failed: {e}", flush=True)
        print(f"[END] task_id={task_id} score=0.0 steps=0 status=error", flush=True)
        return 0.0

    observation = reset_resp.json()
    done = False
    step = 0

    # ── Episode loop ─────────────────────────────────────────────────────────
    while not done:
        step += 1

        # Get action from LLM (with fallback)
        try:
            action = call_llm(observation)
        except Exception as e:
            print(f"[WARN] task_id={task_id} step={step} llm_error={repr(e)}", flush=True)
            action = fallback_action(observation)

        # Send action to environment
        try:
            step_resp = requests.post(f"{BASE_URL}/step", json=action, timeout=15)
            step_resp.raise_for_status()
            step_data = step_resp.json()
        except Exception as e:
            print(f"[ERROR] task_id={task_id} step={step} step_failed={repr(e)}", flush=True)
            break

        # Parse response — reward model uses "value" not "score"
        reward_obj   = step_data.get("reward", {})
        reward_score = reward_obj.get("value", reward_obj.get("score", 0.0))
        done         = step_data.get("done", False)
        next_obs     = step_data.get("observation", {})

        scores.append(reward_score)

        # Build episode log entry for grader
        episode_log.append({
            "message":          observation.get("message", ""),
            "intent":           observation.get("intent", "general_query"),
            "tone":             observation.get("tone", "neutral"),
            "claim_truth_label": observation.get("claim_truth_label", "verified"),
            "action_type":      action["action_type"],
            "reply_message":    action["reply_message"],
            "reward":           reward_score,
        })

        # ── [STEP] log ────────────────────────────────────────────────────────
        print(
            f"[STEP] task_id={task_id} step={step} "
            f"action={action['action_type']} "
            f"reward={reward_score:.4f} "
            f"claim={observation.get('claim_truth_label', 'verified')} "
            f"intent={observation.get('intent', 'general_query')} "
            f"done={str(done).lower()}",
            flush=True
        )

        observation = next_obs

    # ── Call grader for official episode score ────────────────────────────────
    grader_score = None
    try:
        grader_resp = requests.post(
            f"{BASE_URL}/grader",
            params={"task_id": task_id},
            json=episode_log,
            timeout=15
        )
        if grader_resp.status_code == 200:
            grader_score = grader_resp.json().get("score")
    except Exception:
        pass  # Fall back to avg reward score

    final_score = grader_score if grader_score is not None else (
        round(sum(scores) / len(scores), 4) if scores else 0.0
    )

    # ── [END] log ─────────────────────────────────────────────────────────────
    print(
        f"[END] task_id={task_id} score={final_score:.4f} "
        f"steps={step} avg_reward={round(sum(scores)/len(scores), 4) if scores else 0.0} "
        f"status=success",
        flush=True
    )

    return final_score


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    print(f"VerifyIQ-Env Inference  |  model={MODEL_NAME}  |  server={BASE_URL}", flush=True)

    # Health check
    try:
        health = requests.get(f"{BASE_URL}/health", timeout=10)
        if health.status_code != 200:
            print("[ERROR] Server health check failed.", flush=True)
            sys.exit(1)
        print(f"[INFO] Server healthy: {health.json()}", flush=True)
    except Exception as e:
        print(f"[ERROR] Cannot connect to server at {BASE_URL}: {e}", flush=True)
        sys.exit(1)

    results = {}

    for task in TASKS:
        try:
            score = run_task(task)
            results[task["id"]] = score
        except Exception as e:
            print(f"[ERROR] task_id={task['id']} failed with: {repr(e)}", flush=True)
            results[task["id"]] = 0.0
            # Still emit [END] so the parser always gets a complete record
            print(
                f"[END] task_id={task['id']} score=0.0 steps=0 status=error",
                flush=True
            )

    # Save results
    with open("inference_results.json", "w") as f:
        json.dump(results, f, indent=2)

    # Summary
    print("\n" + "=" * 52, flush=True)
    print("  FINAL RESULTS", flush=True)
    print("=" * 52, flush=True)
    for task in TASKS:
        tid = task["id"]
        print(f"  {tid:<28} -> {results.get(tid, 0.0):.4f}", flush=True)
    print("=" * 52, flush=True)
    print("Results saved to inference_results.json", flush=True)


if __name__ == "__main__":
    main()