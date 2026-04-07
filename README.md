---
title: VerifyIQ-Env
emoji: 🔍
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
---

<div align="center">
  <h1>VerifyIQ-Env</h1>
  <h3>AI That Doesn't Just Respond. It Verifies.</h3>

  <p>A sophisticated D2C customer support Reinforcement Learning environment with built-in fraud detection.</p>

<a target="_blank" href="https://asadai1240-verifyiq-env.hf.space"><img src="https://img.shields.io/badge/Live%20Demo-HuggingFace%20Space-blue?style=for-the-badge" alt="Live Demo" /></a>
<br/>
<br/>

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![OpenEnv](https://img.shields.io/badge/OpenEnv-Compatible-purple.svg)](https://openenv.ai/)
[![OpenAI](https://img.shields.io/badge/OpenAI-SDK_Integration-darkgrey.svg)](https://openai.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## Table of Contents

- [Overview](#overview)
- [The Problem & Solution](#the-problem--solution)
- [System Architecture](#system-architecture)
- [Environment Tasks](#environment-tasks)
- [Observation Space](#observation-space)
- [Action Space](#action-space)
- [Reward Mechanism](#reward-mechanism)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [License](#license)

---

## Overview

**VerifyIQ-Env** is an open-source, OpenEnv-compatible reinforcement learning environment that simulates a highly realistic Direct-to-Consumer (D2C) customer support scenario. Built for the OpenEnv Hackathon Round 1, it trains and evaluates AI agents to handle support queries in multiple languages (including regional dialects like Hinglish and Pidgin).

Unlike standard conversational environments, VerifyIQ-Env features the **TruthLens** verification engine. Agents are rigorously penalized for blindly trusting users and hallucinating refunds, forcing them to learn investigation and data cross-referencing.

### Live Deployment
- **HuggingFace Space:** [https://asadai1240-verifyiq-env.hf.space](https://asadai1240-verifyiq-env.hf.space)
- **API Health Check:** [https://asadai1240-verifyiq-env.hf.space/health](https://asadai1240-verifyiq-env.hf.space/health)

---

## The Problem & Solution

### The Shortfall of Current LLM Support Agents
Current LLM-based support agents suffer from critical business vulnerabilities:
- **Blind Trust:** They process refunds based purely on customer sentiment and claims without checking backend truth.
- **Language Barriers:** They struggle to effectively map code-mixed languages like Hinglish to actionable intents.
- **Tone Deafness:** They respond robotically to highly frustrated users, decreasing customer satisfaction (CSAT).

### The VerifyIQ Solution
VerifyIQ-Env provides a rigorous training ground to fix these behaviors:
- **Truth Verification:** Cross-references dynamic customer claims against a ground-truth order database.
- **Strict Penalty System:** Severely penalizes agents for enabling fraud (-0.50 points) while rewarding proactive investigation.
- **Empathy Scoring:** Programmatically rewards agents for de-escalating frustrated customers using culturally appropriate empathy markers.

---

## System Architecture
┌──────────────────────────────────────────────────────────────────┐
│                     VERIFY-IQ ENVIRONMENT                        │
└──────────────────────────────────────────────────────────────────┘
┌──────────────────────┐         ┌───────────────────────────────┐
│  CUSTOMER GENERATOR  │         │  AI AGENT (LLM / INFERENCE)   │
│                      │         │                               │
│  - Raw Messages      │         │  - Receives Observation       │
│  - Hinglish / En     │         │  - Generates Action JSON      │
│  - Genuine & Fraud   │         │  - OpenAI API Integration     │
└──────────┬───────────┘         └───────────────┬───────────────┘
│                                     │
▼                                     ▼
┌──────────────────────────────────────────────────────────────────┐
│                 FASTAPI SERVER (OpenEnv Spec)                    │
│                                                                  │
│  [POST] /reset           [POST] /step           [GET] /state     │
└──────────┬─────────────────────────────┬─────────────────────────┘
│                             │
▼                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                 INTERNAL PROCESSING PIPELINES                    │
│                                                                  │
│  1. NLP ENGINE                         2. TRUTHLENS VERIFIER     │
│  - Intent Classifier                   - Claim Extractor         │
│  - Tone Analyzer                       - DB Cross-validator      │
│  - Language Detector                   - Truth Scorer            │
│                 \                       /                        │
│                  \                     /                         │
│                   ▼                   ▼                          │
│                 3. ENVIRONMENT STATE MANAGER                     │
│                 - Calculates Reward Breakdown                    │
│                 - Updates CSAT & Empathy Stats                   │
│                 - Generates Next Observation                     │
└──────────────────────────────────────────────────────────────────┘

---

## Environment Tasks

| Task ID | Difficulty | Message Count | Fraud Rate | Focus Area |
|---------|------------|---------------|------------|------------|
| `single_intent_triage` | **Easy** | 10 | 0% | Pure intent triage in clear English. No fake claims. |
| `hinglish_fraud_detection` | **Medium** | 20 | 35% (7 cases) | Code-mixed Hinglish. Agent must detect hidden false claims. |
| `full_support_shift` | **Hard** | 40 | 37.5% (15 cases) | Global regions (India, USA, Nigeria). Strict empathy scaling required. |

---

## Observation Space

| Field | Type | Description |
|-------|------|-------------|
| `message` | string | Raw customer message. |
| `language` | string | Detected dialect: [hi, hinglish, en] |
| `tone` | string | Emotional state: [frustrated, urgent, casual, neutral] |
| `intent` | string | Classified issue: [order_status, refund_request, complaint, general_query] |
| `customer_id` | string | Unique customer identifier. |
| `order_id` | string/null | Target order ID (if applicable). |
| `claim_truth_label` | string | TruthLens label: [verified, suspicious, false] |
| `claim_truth_score` | float | 0.0 - 1.0 confidence of truth. |
| `region` | string | Geographic origin. |
| `queue_size` | integer | Active messages remaining in the shift. |

---

## Action Space

| Field | Type | Description |
|-------|------|-------------|
| `action_type` | string | Must be: [reply_only, track_order, initiate_refund, investigate_first, escalate_human] |
| `reply_message` | string | The actual text response to the customer. |
| `order_id` | string/null | The order ID being acted upon. |
| `refund_amount` | float/null | The numeric amount if initiating a refund. |

---

## Reward Mechanism

**1. Intent Matching**
- `+0.40`: Correct system action selected for the customer's intent.
- `-0.20`: Incorrect system action selected.

**2. TruthLens Fraud Validation**
- `+0.30`: Agent safely investigates a suspicious or false claim.
- `-0.50`: SEVERE PENALTY. Agent blindly initiates a refund for a false claim.

**3. Empathy & Tone Control**
- `+0.20`: Agent includes empathy keywords when user tone is frustrated or urgent.
- `-0.15`: Agent fails to show empathy to a frustrated user.

---

## Tech Stack

- **Framework:** FastAPI (Python 3.11)
- **RL Standard:** OpenEnv API compliance
- **Data Validation:** Pydantic
- **Inference Engine:** OpenAI SDK
- **Deployment:** Docker & HuggingFace Spaces

---

## Getting Started
```bash
git clone https://github.com/khanasad01/verifyiqq-env.git
cd verifyiqq-env
pip install -r requirements.txt
cp .env.example .env
uvicorn server:app --reload --port 8000
python inference.py
```

---

## Project Structure
verifyiqq-env/
├── server.py
├── inference.py
├── openenv.yaml
├── environment/
├── nlp/
├── verifier/
├── graders/
└── data/

---

## License

MIT License - Built for the OpenEnv Hackathon 2026