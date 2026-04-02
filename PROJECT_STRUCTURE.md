# 🔍 VerifyIQ-Env — Complete Project Structure Guide

> **"AI That Doesn't Just Respond. It Verifies."**
>
> This project is a **reinforcement-learning environment** (OpenEnv-compatible) that trains/evaluates an AI agent to handle **D2C (Direct-to-Consumer) customer support** — in **Hinglish, Hindi, and English** — while automatically detecting **fraudulent claims**.
>
> Live at: https://asadai1240-verifyiq-env.hf.space

---

## 📐 What Is This Project, In Simple Terms?

Imagine a customer support AI for an Indian e-commerce company. Customers message on WhatsApp in a mix of Hindi and English ("Hinglish"). Some are genuine — they have a real broken product or a missing delivery. Some are **fraudsters** — they lie about what happened to get a refund they don't deserve.

This project builds an **environment** (like a gym for AI agents) where:
1. A customer message is shown to the agent (the "observation").
2. The agent decides what action to take (reply, refund, investigate, escalate).
3. The environment scores the action (the "reward") based on whether the agent handled it correctly, showed empathy, and caught/avoided fraud.

The whole system is served over a **FastAPI REST API** and is deployable on **Hugging Face Spaces** via **Docker**.

---

## 🗺️ Full File Tree With Explanations

```
verifyiqq-env/
│
├── 📄 server.py                  ← FastAPI web server (the main entry point when deployed)
├── 📄 baseline.py                ← A ready-made GPT-4o agent that solves all 3 tasks
├── 📄 inference.py               ← An alternative/flexible LLM agent runner (supports custom models)
├── 📄 test.py                    ← Local test runner (runs all 3 tasks without the API)
├── 📄 baseline_results.json      ← Output scores saved after running baseline.py
│
├── 📄 openenv.yaml               ← The "specification file" — describes the environment to OpenEnv
├── 📄 configsindia.yaml          ← (Placeholder) India-specific config (currently empty)
├── 📄 requirements.txt           ← Python package dependencies
├── 📄 Dockerfile                 ← Docker build instructions for deployment to HuggingFace Spaces
├── 📄 README.md                  ← Short project description + live links
│
├── 📁 environment/               ← The core RL environment logic
│   ├── __init__.py
│   ├── env.py                    ← The ContextIQEnv class (reset, step, reward)
│   ├── models.py                 ← Pydantic data models (Observation, Action, Reward)
│   ├── reward.py                 ← Standalone reward calculator (more detailed than env.py's inline calc)
│   └── state_manager.py          ← Tracks queue of messages, metrics, CSAT scores
│
├── 📁 nlp/                       ← Natural Language Processing utilities
│   ├── __init__.py
│   ├── intent.py                 ← Classifies what the customer wants (refund/order status/complaint/query)
│   ├── language.py               ← Detects language (Hindi / Hinglish / English)
│   └── tone.py                   ← Detects emotional tone (frustrated / urgent / casual / neutral)
│
├── 📁 verifier/                  ← The "TruthLens" fraud detection engine
│   ├── __init__.py
│   ├── claim_extractor.py        ← Extracts verifiable claims from a message (dates, conditions, non-delivery)
│   └── claim_validator.py        ← Cross-checks extracted claims against the real orders database
│
├── 📁 graders/                   ← Task-specific scoring functions
│   ├── __init__.py
│   ├── grader1.py                ← Scores Task 1 (Easy): pure intent-action accuracy
│   ├── grader2.py                ← Scores Task 2 (Medium): intent accuracy + fraud detection rate
│   └── grader3.py                ← Scores Task 3 (Hard): intent + fraud + empathy scoring
│
├── 📁 tasks/                     ← The actual message datasets for each task
│   ├── __init__.py
│   ├── task1.py                  ← 10 simple English messages (easy)
│   ├── task2.py                  ← 20 Hinglish messages with 7 hidden fraud cases (medium)
│   └── task3.py                  ← 40 messages across India/USA/Nigeria/Indonesia (hard)
│
└── 📁 data/                      ← Ground-truth database
    ├── orders.json               ← Real order records (delivery dates, conditions, refund status)
    └── messages.json             ← Labeled message examples with ground truth intent/tone/fraud flag
```

---

## 📄 File-by-File Deep Dive

---

### 🟢 Root Level Files

---

#### `server.py` — The FastAPI Web Server
**What it does:** Exposes the entire environment as a REST API.

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Check if the server is alive |
| `/reset` | POST | Start a new episode (load message queue) |
| `/step` | POST | Submit an agent action, receive observation + reward |
| `/state` | GET | View current queue/metrics snapshot |
| `/tasks` | GET | List all 3 available tasks with descriptions |
| `/grader` | POST | Run a specific grader on an episode log |
| `/baseline` | POST | Runs `baseline.py` as a subprocess and returns output |

This is the **main entry point** when deployed via Docker. It imports and wires together the `ContextIQEnv`, all three graders, and the `Action` model.

---

#### `baseline.py` — The Reference GPT-4o Agent
**What it does:** Acts as a full-featured customer support agent using OpenAI's `gpt-4o`.

- Calls `/reset` to start an episode
- Loops: sends each observation to GPT-4o, gets a JSON action back, posts to `/step`
- Handles all 3 tasks sequentially
- Saves scores to `baseline_results.json`

**Key system prompt rules it gives GPT-4o:**
1. Show empathy first if tone is `frustrated` or `urgent`
2. **NEVER** use `initiate_refund` if `claim_truth_label` is `false`
3. Use `investigate_first` for suspicious claims
4. Keep the reply under 3 sentences

**Environment variables needed:**
- `OPENAI_API_KEY` — required (raises an error if missing)
- `VERIFYIQ_URL` — optional (defaults to `http://localhost:8000`)

---

#### `inference.py` — The Flexible LLM Runner
**What it does:** Similar to `baseline.py`, but uses the **OpenAI SDK** and supports custom models and API endpoints (e.g., HuggingFace Inference API, local models via LM Studio).

**Key difference from `baseline.py`:**
- Uses `openai.OpenAI(base_url=API_BASE_URL)` — pluggable base URL
- `MODEL_NAME` and `API_BASE_URL` are configurable via environment variables
- Uses `HF_TOKEN` as the API key (for HuggingFace Inference Endpoints)

**Environment variables:**
- `API_BASE_URL` — defaults to `https://api.openai.com/v1`
- `MODEL_NAME` — defaults to `gpt-4o`
- `HF_TOKEN` — the API key
- `VERIFYIQ_URL` — the environment server URL

---

#### `test.py` — Local Test Runner
**What it does:** Runs all 3 tasks **without needing the HTTP server**. Directly imports `ContextIQEnv`, task message lists, and graders.

- Uses a hardcoded `GOOD_ACTIONS` dict (best action per intent)
- Reply message always includes Hinglish empathy words so empathy score is always satisfied
- Prints scores for all 3 tasks
- Useful for quick local validation after code changes

---

#### `baseline_results.json` — Saved Baseline Scores
**What it does:** Output file created by `baseline.py`. Stores the average reward per task.

Currently shows zeros — meaning the baseline agent hasn't been run against the live server yet (or the server was not running when it was last executed).

```json
{
  "task_1": 0.0,
  "task_2": 0.0,
  "task_3": 0.0
}
```

---

#### `openenv.yaml` — The Environment Specification
**What it does:** Declares this project as a formal **OpenEnv-compatible environment**. This is the "contract" that tells the OpenEnv platform what the agent sees (observation space), what it can do (action space), and how it's evaluated.

**Observation Space fields an agent receives:**
| Field | Type | Description |
|---|---|---|
| `message` | string | The raw customer message |
| `language` | enum | `hi`, `hinglish`, `en` |
| `tone` | enum | `frustrated`, `urgent`, `casual`, `neutral` |
| `intent` | enum | `order_status`, `refund_request`, `complaint`, `general_query` |
| `customer_id` | string | Unique customer identifier |
| `order_id` | string / null | Order reference (may be null for general queries) |
| `claim_truth_score` | float 0–1 | Probability the customer's claim is true |
| `claim_truth_label` | enum | `verified`, `suspicious`, `false` |
| `region` | string | Geographic region |
| `queue_size` | int | Messages remaining in this episode |

**Action Space fields the agent must return:**
| Field | Type | Description |
|---|---|---|
| `action_type` | enum | `reply_only`, `track_order`, `initiate_refund`, `investigate_first`, `escalate_human` |
| `reply_message` | string | The message to send back to the customer |
| `order_id` | string / null | Order to act on |
| `refund_amount` | float / null | Amount for refund (if applicable) |

**The 3 Tasks:**
| ID | Difficulty | Description |
|---|---|---|
| `single_intent_triage` | Easy | 10 English messages, clear intents |
| `hinglish_fraud_detection` | Medium | 20 Hinglish messages, 7 fraud cases hidden |
| `full_support_shift` | Hard | 40 messages across 4 countries, 15 fraud cases |

---

#### `Dockerfile` — Container Build Instructions
**What it does:** Packages the app for deployment on **Hugging Face Spaces** (Docker SDK).

```
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt . → installs dependencies
COPY . .               → copies all project files
EXPOSE 7860            → HuggingFace Spaces standard port
CMD uvicorn server:app --host 0.0.0.0 --port 7860
```

---

#### `requirements.txt` — Python Dependencies
| Package | Purpose |
|---|---|
| `fastapi` | Web framework for the REST API |
| `uvicorn` | ASGI server to run FastAPI |
| `pydantic` | Data validation for Observation/Action/Reward models |
| `openai` | SDK to call GPT-4o (or compatible LLMs) |
| `python-dotenv` | Load `.env` files for local development |
| `pyyaml` | Parse YAML config files |
| `python-multipart` | Handle form data in FastAPI |

---

---

### 📁 `environment/` — The Core RL Environment

This is the heart of the project. It implements the standard Gym-style RL loop.

---

#### `environment/models.py` — Data Contracts (Pydantic)
**What it does:** Defines the 3 data shapes that flow through the system.

```python
class Observation   # What the agent sees (message, language, tone, fraud score...)
class Action        # What the agent does (action_type, reply_message, order_id...)
class Reward        # What score the agent gets (value, breakdown dict, explanation, tip)
```

These are Pydantic `BaseModel` classes, so they auto-validate JSON input/output and integrate seamlessly with FastAPI.

---

#### `environment/env.py` — The ContextIQEnv Class
**What it does:** The main environment class. Think of it like an OpenAI Gym environment.

**Key methods:**
| Method | What it does |
|---|---|
| `reset()` | Loads the sample message queue, returns first observation |
| `step(action)` | Scores the action, advances queue, returns (obs, reward, done, info) |
| `state()` | Returns current metrics snapshot |
| `_build_observation(msg)` | Converts a raw message dict into an `Observation` object |
| `_calculate_reward(action)` | The inline reward function (see below) |

**Reward calculation logic (inline in env.py):**

| Situation | Reward |
|---|---|
| Action matches expected intent | +0.40 |
| Action doesn't match intent | -0.20 |
| Claim is `false` + agent uses `initiate_refund` (fraud enabled!) | -0.50 |
| Claim is `false` + agent uses `investigate_first` (fraud caught!) | +0.30 |
| Customer is `frustrated` + reply has empathy words | +0.20 |
| Customer is `frustrated` + no empathy in reply | -0.15 |

Final reward is clamped to `[-1.0, 1.0]` and includes a bilingual explanation + learning tip.

> **Note:** There is also a more detailed `environment/reward.py` (see below) that adds language-match and unnecessary-escalation checks. The two reward functions are parallel implementations — the one in `env.py` is what actually runs.

---

#### `environment/reward.py` — Extended Reward Calculator
**What it does:** A standalone, more comprehensive version of the reward function (not currently wired into `env.py` but available for future use or testing).

**Extra checks not in `env.py`:**
- **Suspicious claim handling:** `investigate_first` on `suspicious` → +0.20; `initiate_refund` on `suspicious` → -0.20
- **Language match bonus:** If customer wrote in Hinglish/Hindi and the reply contains Hinglish words → +0.10
- **Unnecessary escalation penalty:** Using `escalate_human` for a `general_query` → -0.30

---

#### `environment/state_manager.py` — The Queue & Metrics Tracker
**What it does:** Manages the internal state of an episode.

**Tracks:**
- `queue` — list of upcoming messages
- `metrics.resolved` — count of resolved tickets
- `metrics.escalated` — count escalated to human
- `metrics.fraud_caught` — count of frauds correctly identified
- `metrics.fraud_missed` — count of frauds incorrectly refunded
- `metrics.csat_scores` — list of reward values (Customer Satisfaction proxy)
- `metrics.shift_minutes` — starts at 240, decreases by 5 per step (simulates a 4-hour support shift)

**Key methods:**
- `load_queue(messages)` — fills the queue and resets all metrics
- `next_message()` — pops the next message from the queue
- `update(action_type, reward_value)` — updates metrics after each step
- `get_snapshot()` — returns current queue size, averages, fraud stats

---

---

### 📁 `nlp/` — Natural Language Processing

These are **rule-based** NLP utilities (no ML model required — just keyword matching).

---

#### `nlp/intent.py` — Intent Classifier
**What it does:** Given a customer message, returns one of 4 intent categories.

**How it works:** Scores the message against 3 keyword lists:
- `REFUND_WORDS` → "refund", "wapas", "paise wapas", "cancel"…
- `ORDER_WORDS` → "order", "kahan hai", "track", "kab aayega"…
- `COMPLAINT_WORDS` → "kharab", "broken", "damaged", "bakwaas"…

The category with the most keyword hits wins. Zero hits → `general_query`.

---

#### `nlp/language.py` — Language Detector
**What it does:** Returns `hi`, `hinglish`, or `en`.

**How it works:**
1. If the text contains **Devanagari characters** (Unicode range `\u0900-\u097F`) → `hi` (pure Hindi)
2. If 1+ words match the `HINGLISH_WORDS` list → `hinglish`
3. Otherwise → `en`

---

#### `nlp/tone.py` — Tone Detector
**What it does:** Returns `frustrated`, `urgent`, `casual`, or `neutral`.

**How it works:** Keyword scoring — first positive match wins in priority order:
1. `FRUSTRATED_WORDS` → "worst", "bakwaas", "gussa", "dhoka"…
2. `URGENT_WORDS` → "urgent", "jaldi", "abhi", "asap"…
3. `CASUAL_WORDS` → "bhai", "yaar", "bro", "oye"…
4. Default → `neutral`

---

---

### 📁 `verifier/` — The TruthLens Fraud Detection Engine

This is what makes VerifyIQ-Env unique. It cross-checks customer claims against real order data.

---

#### `verifier/claim_extractor.py` — Extracts Verifiable Claims
**What it does:** Parses a customer message and pulls out specific, checkable claims.

**Types of claims it can extract:**
| Claim Type | Example trigger | What it captures |
|---|---|---|
| `delivery_date` | "5 din pehle aaya tha" | How many days ago customer says it arrived |
| `item_condition` | "toot hua tha", "not working" | What condition the customer claims (damaged, not_working, wrong_item) |
| `non_delivery` | "nahi aaya", "not delivered" | A flat claim that the item never arrived |

Uses regex patterns and keyword matching. Returns a list of claim dicts.

---

#### `verifier/claim_validator.py` — Cross-Checks Claims Against Database
**What it does:** Takes extracted claims + an order ID, loads the real order from `data/orders.json`, and checks each claim.

**Scoring logic:**

For `delivery_date` claims:
- Difference of 0 days → truth score 1.0 (verified)
- Difference of 1 day → 0.7
- Difference of 2–3 days → 0.4 (suspicious)
- Difference of 4+ days → 0.1 (false)

For `item_condition` claims:
- Claimed condition matches actual + damage report exists → 1.0 (verified)
- Matches but no damage report → 0.6 (suspicious)
- Doesn't match → 0.1 (false)

For `non_delivery` claims:
- Order not yet delivered → 1.0 (verified)
- Order IS in the DB as delivered → 0.0 (false)

**Output:** `{ truth_score: float, truth_label: "verified"|"suspicious"|"false", details: "..." }`

---

---

### 📁 `graders/` — Task Scoring Functions

Each grader takes an **episode log** (list of dicts, one per step) and returns a float score between 0 and 1.

---

#### `graders/grader1.py` — Easy Task Grader
**Scoring formula:** `correct_actions / total_messages`

Checks: did the agent pick the right action type for the detected intent?  
No fraud detection scoring here — Task 1 has no false claims.

---

#### `graders/grader2.py` — Medium Task Grader
**Scoring formula:** `fraud_score × 0.60 + action_score × 0.40`

- `fraud_score` = fraction of false-claim messages where agent used `investigate_first` (not `initiate_refund`)
- `action_score` = fraction of all messages with a correct action

Fraud detection is **weighted more** (60%) because Task 2 is about catching fraud.

---

#### `graders/grader3.py` — Hard Task Grader
**Scoring formula:** `fraud_score × 0.40 + action_score × 0.35 + empathy_score × 0.25`

- `fraud_score` — same as grader2
- `action_score` — same as grader2
- `empathy_score` — for frustrated-tone messages: fraction where the reply contained an empathy word

Task 3 is the full evaluation: get the intent right, catch fraud, AND be emotionally intelligent.

**Empathy words grader3 recognizes:** "understand", "sorry", "samajh", "help", "zaroor", "hoon", "i see"

---

---

### 📁 `tasks/` — Message Datasets

---

#### `tasks/task1.py` — Easy: 10 Single-Intent English Messages
All clear, neutral English messages. All claims are `verified`. No fraud. Tests basic intent routing.

Examples:
- "where is my order" → `order_status`
- "I want a refund please" → `refund_request`
- "what is your return policy" → `general_query`

---

#### `tasks/task2.py` — Medium: 20 Hinglish Messages With 7 Fraud Cases
Mix of genuine and fraudulent messages in Hinglish (Hindi-English). 7 messages have `claim_truth_label: false`.

Example fraud case:
```
"bhai mera order 5 din pehle aaya aur bilkul toot hua tha"
→ order ORD001 actually has delivered_days_ago=2, actual_condition="good"
→ truth_label: false
```

---

#### `tasks/task3.py` — Hard: 40 Messages Across 4 Regions
Combines all of Task 1 + Task 2 + 10 extra international messages.

Extra messages include regions: `usa`, `nigeria`, `indonesia`. Includes Nigerian Pidgin English ("dem never bring my order o") and Indonesian Bahasa ("barang yang datang salah").

Total of 15 false-claim fraud cases hidden in the 40 messages.

---

---

### 📁 `data/` — Ground-Truth Database

---

#### `data/orders.json` — Real Order Records
**16 order records.** Each record contains:
| Field | Description |
|---|---|
| `order_id` | Unique order reference (ORD001–ORD020) |
| `customer_id` | Customer who placed the order |
| `delivered_days_ago` | How many days ago the order was actually delivered |
| `actual_condition` | Real product condition: `good`, `damaged`, `wrong_item`, `not_working` |
| `damage_report` | Whether a damage report was actually filed |
| `refund_status` | `none` or `processing` |
| `amount` | Order value in ₹ |

This is what `claim_validator.py` cross-checks against.

---

#### `data/messages.json` — Labeled Message Examples
**20 pre-labeled messages** with ground truth for:
- `ground_truth_intent` — the correct intent classification
- `ground_truth_tone` — the correct tone classification
- `is_fraud` — boolean indicating if this message contains a false claim

Used for development, testing NLP accuracy, or training future ML-based intent/tone classifiers.

---

---

## 🔄 How Everything Connects — The Data Flow

```
Customer Message (WhatsApp)
        │
        ▼
   [nlp/language.py]  ← detects language (hi/hinglish/en)
   [nlp/intent.py]    ← classifies intent (refund/order/complaint/query)
   [nlp/tone.py]      ← detects tone (frustrated/urgent/casual/neutral)
        │
        ▼
[verifier/claim_extractor.py]  ← pulls out checkable claims
[verifier/claim_validator.py]  ← cross-checks against data/orders.json
        │
        ▼
   Observation built (environment/models.py → Observation)
   → sent to AI Agent via POST /step
        │
        ▼
   Agent returns Action
   (action_type, reply_message, order_id, refund_amount)
        │
        ▼
   environment/env.py → _calculate_reward()
        │
        ├── intent match? (+0.40 or -0.20)
        ├── fraud catch?  (+0.30 or -0.50)
        └── empathy?      (+0.20 or -0.15)
        │
        ▼
   Reward (value, breakdown, explanation, learning_tip)
        │
        ▼
   [state_manager.py] updates metrics
        │
        ▼
   Next message from queue  →  repeat  →  done=True
        │
        ▼
   [graders/graderN.py] → final episode score (0.0 to 1.0)
```

---

## 🚀 How To Run This Project

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn server:app --reload --port 8000

# Test all tasks locally (no server needed)
python test.py

# Run the baseline GPT-4o agent (needs server running)
OPENAI_API_KEY=your_key python baseline.py
```

### Docker / HuggingFace Spaces
```bash
docker build -t verifyiq-env .
docker run -p 7860:7860 -e OPENAI_API_KEY=your_key verifyiq-env
```

---

## 🧠 Key Concepts to Understand

| Term | What it means here |
|---|---|
| **Observation** | The current customer message + all its metadata that the agent sees |
| **Action** | What the agent decides to do (reply, refund, investigate, escalate) |
| **Reward** | A number between -1 and +1 saying how well the agent did |
| **Episode** | One full run through a task's message queue (10/20/40 messages) |
| **Hinglish** | A mix of Hindi and English commonly used in Indian WhatsApp chats |
| **claim_truth_label** | The key fraud signal — `verified`/`suspicious`/`false` |
| **OpenEnv** | The open standard this environment conforms to (like OpenAI Gym for specialized domains) |
| **TruthLens** | The internal name for the verifier module (claim extraction + validation) |
| **ContextIQ** | The internal name for the NLP module (language + intent + tone detection) |
