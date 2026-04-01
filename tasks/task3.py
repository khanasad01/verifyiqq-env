from tasks.task1 import TASK1_MESSAGES
from tasks.task2 import TASK2_MESSAGES

TASK3_EXTRA = [
    {
        "message": "I never received my package it has been 2 weeks",
        "customer_id": "C301",
        "order_id": "ORD002",
        "language": "en",
        "tone": "frustrated",
        "intent": "order_status",
        "claim_truth_score": 0.1,
        "claim_truth_label": "false",
        "region": "usa"
    },
    {
        "message": "dem never bring my order o abeg refund me",
        "customer_id": "C302",
        "order_id": "ORD007",
        "language": "en",
        "tone": "frustrated",
        "intent": "order_status",
        "claim_truth_score": 0.1,
        "claim_truth_label": "false",
        "region": "nigeria"
    },
    {
        "message": "barang yang datang salah minta refund",
        "customer_id": "C303",
        "order_id": "ORD008",
        "language": "en",
        "tone": "neutral",
        "intent": "refund_request",
        "claim_truth_score": 1.0,
        "claim_truth_label": "verified",
        "region": "indonesia"
    },
    {
        "message": "item was completely broken on arrival last week",
        "customer_id": "C304",
        "order_id": "ORD001",
        "language": "en",
        "tone": "frustrated",
        "intent": "complaint",
        "claim_truth_score": 0.1,
        "claim_truth_label": "false",
        "region": "usa"
    },
    {
        "message": "please process my refund immediately",
        "customer_id": "C305",
        "order_id": "ORD020",
        "language": "en",
        "tone": "urgent",
        "intent": "refund_request",
        "claim_truth_score": 1.0,
        "claim_truth_label": "verified",
        "region": "usa"
    },
    {
        "message": "track my order please",
        "customer_id": "C306",
        "order_id": "ORD002",
        "language": "en",
        "tone": "neutral",
        "intent": "order_status",
        "claim_truth_score": 1.0,
        "claim_truth_label": "verified",
        "region": "usa"
    },
    {
        "message": "order nahi aaya 12 din se wait kar raha hoon",
        "customer_id": "C307",
        "order_id": "ORD011",
        "language": "hinglish",
        "tone": "frustrated",
        "intent": "order_status",
        "claim_truth_score": 0.1,
        "claim_truth_label": "false",
        "region": "india"
    },
    {
        "message": "what are your business hours",
        "customer_id": "C308",
        "order_id": None,
        "language": "en",
        "tone": "neutral",
        "intent": "general_query",
        "claim_truth_score": 1.0,
        "claim_truth_label": "verified",
        "region": "usa"
    },
    {
        "message": "refund kab tak process hoga",
        "customer_id": "C309",
        "order_id": "ORD013",
        "language": "hinglish",
        "tone": "neutral",
        "intent": "refund_request",
        "claim_truth_score": 1.0,
        "claim_truth_label": "verified",
        "region": "india"
    },
    {
        "message": "product missing from box when delivered",
        "customer_id": "C310",
        "order_id": "ORD001",
        "language": "en",
        "tone": "frustrated",
        "intent": "complaint",
        "claim_truth_score": 0.1,
        "claim_truth_label": "false",
        "region": "usa"
    }
]

TASK3_MESSAGES = TASK1_MESSAGES + TASK2_MESSAGES + TASK3_EXTRA

TASK3_DESCRIPTION = "Handle 40 messages across all regions with 15 false claims"
TASK3_DIFFICULTY = "hard"
