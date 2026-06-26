# QueueStorm Investigator

A Django REST API service built for the **SUST CSE Carnival 2026 Codex Community Hackathon Preliminary Round**.

The service works as an internal support copilot for digital finance complaint handling. It receives a customer complaint and recent transaction history, then returns a structured JSON response with classification, routing, evidence verdict, safety-aware customer reply, and human review recommendation.

## Required Endpoints

### Health Check

```http
GET /health
```

Expected response:

```json
{
  "status": "ok"
}
```

### Analyze Ticket

```http
POST /analyze-ticket
```

This endpoint accepts one customer complaint and transaction history, then returns a structured support decision.

## Tech Stack

* Python
* Django
* Django REST Framework
* Rule-based evidence reasoning
* Rule-based safety guardrails

## Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/MuradAhmedTahmim/SUST_Hackathon_Preliminary.git
cd SUST_Hackathon_Preliminary
```

### 2. Create virtual environment

```bash
python -m venv venv
```

### 3. Activate virtual environment

For Windows CMD:

```bash
venv\Scripts\activate
```

For PowerShell:

```powershell
venv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Run the server

```bash
python manage.py runserver
```

The local API will run at:

```text
http://127.0.0.1:8000
```

## Sample Request

```json
{
  "ticket_id": "TKT-001",
  "complaint": "I sent 5000 taka to a wrong number around 2pm today",
  "language": "en",
  "channel": "in_app_chat",
  "user_type": "customer",
  "campaign_context": "boishakh_bonanza_day_1",
  "transaction_history": [
    {
      "transaction_id": "TXN-9101",
      "timestamp": "2026-04-14T14:08:22Z",
      "type": "transfer",
      "amount": 5000,
      "counterparty": "+8801719876543",
      "status": "completed"
    }
  ]
}
```

## Sample Response

```json
{
  "ticket_id": "TKT-001",
  "relevant_transaction_id": "TXN-9101",
  "evidence_verdict": "consistent",
  "case_type": "wrong_transfer",
  "severity": "high",
  "department": "dispute_resolution",
  "agent_summary": "Customer complaint classified as wrong_transfer. Relevant transaction: TXN-9101.",
  "recommended_next_action": "Review the complaint against the provided transaction history and route it to the assigned department. Do not ask for PIN, OTP, password, or secret credentials.",
  "customer_reply": "We have noted your concern. Our support team will review the provided transaction details. Please do not share your PIN, OTP, password, or any secret credentials.",
  "human_review_required": true,
  "confidence": 0.75,
  "reason_codes": [
    "wrong_transfer",
    "consistent",
    "transaction_match"
  ]
}
```

## API Response Fields

The API returns the following fields:

* `ticket_id`
* `relevant_transaction_id`
* `evidence_verdict`
* `case_type`
* `severity`
* `department`
* `agent_summary`
* `recommended_next_action`
* `customer_reply`
* `human_review_required`
* `confidence`
* `reason_codes`

## Supported Case Types

* `wrong_transfer`
* `payment_failed`
* `refund_request`
* `duplicate_payment`
* `merchant_settlement_delay`
* `agent_cash_in_issue`
* `phishing_or_social_engineering`
* `other`

## Supported Departments

* `customer_support`
* `dispute_resolution`
* `payments_ops`
* `merchant_operations`
* `agent_operations`
* `fraud_risk`

## Evidence Reasoning Logic

The service checks the customer complaint against the provided transaction history.

It tries to identify the relevant transaction by:

1. Matching transaction ID mentioned in the complaint.
2. Matching transaction amount mentioned in the complaint.
3. Using the only transaction if the history contains exactly one transaction.

Then it returns one of the following evidence verdicts:

* `consistent` — transaction data supports the complaint.
* `inconsistent` — transaction data contradicts the complaint.
* `insufficient_data` — the service cannot determine the truth from the provided data.

## Safety Logic

The service includes rule-based safety guardrails.

It never asks the customer for:

* PIN
* OTP
* Password
* Secret credentials
* Full card number

It also avoids confirming refunds, reversals, account recovery, or unblock actions without authority.

For suspicious complaints involving OTP, PIN, password, scam, fraud, fake calls, or SMS, the service classifies the case as:

```text
phishing_or_social_engineering
```

and routes it to:

```text
fraud_risk
```

## Human Review Logic

Human review is required when:

* The case is high risk.
* The case involves phishing or social engineering.
* The evidence is insufficient.
* The evidence is inconsistent.
* The case involves wrong transfer, failed payment, duplicate payment, or agent cash-in issue.

## Models Used

No external AI or LLM model is currently used.

This version uses deterministic rule-based logic because:

* It is fast.
* It is low cost.
* It avoids external API dependency.
* It gives stable JSON output.
* It reduces risk of unsafe generated replies.

## Cost Reasoning

Current model/API cost:

```text
0 BDT / 0 USD
```

No external paid API is required.

## Known Limitations

* The system uses rule-based keyword matching.
* It may not understand all Bangla or Banglish complaint variations.
* Duplicate payment detection is basic.
* It does not connect to a real payment system.
* It does not perform real refunds, reversals, or account actions.
* It only reasons from the provided synthetic transaction history.

## Repository Contents

```text
config/
investigator/
manage.py
requirements.txt
sample_output.json
README.md
.gitignore
```

## Runbook

To run locally:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py runserver
```

Then test:

```text
GET http://127.0.0.1:8000/health
POST http://127.0.0.1:8000/analyze-ticket
```

## Submission Notes

This project satisfies the required preliminary API structure:

* `GET /health`
* `POST /analyze-ticket`
* Structured JSON response
* Safety-aware customer reply
* Human review routing
* Evidence verdict based on complaint and transaction history
