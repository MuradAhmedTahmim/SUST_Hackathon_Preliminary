from django.shortcuts import render

# Create your views here.
import re
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status


CASE_DEPARTMENT_MAP = {
    "wrong_transfer": "dispute_resolution",
    "payment_failed": "payments_ops",
    "refund_request": "customer_support",
    "duplicate_payment": "payments_ops",
    "merchant_settlement_delay": "merchant_operations",
    "agent_cash_in_issue": "agent_operations",
    "phishing_or_social_engineering": "fraud_risk",
    "other": "customer_support",
}


@api_view(["GET"])
def health(request):
    return Response({"status": "ok"})


def contains_any(text, keywords):
    text = text.lower()
    return any(keyword in text for keyword in keywords)


def classify_case(complaint):
    text = complaint.lower()

    if contains_any(text, [
        "otp", "pin", "password", "passcode", "login code",
        "scam", "fraud", "suspicious", "fake call", "sms",
        "ওটিপি", "পিন", "পাসওয়ার্ড", "প্রতারক", "ভুয়া কল"
    ]):
        return "phishing_or_social_engineering", "critical"

    if contains_any(text, [
        "wrong number", "wrong recipient", "wrong person",
        "wrongly sent", "sent to wrong", "ভুল নাম্বার", "ভুল নম্বর"
    ]):
        return "wrong_transfer", "high"

    if contains_any(text, [
        "failed", "deducted", "balance deducted", "money cut",
        "payment failed", "টাকা কেটে", "টাকা কেটে গেছে"
    ]):
        return "payment_failed", "high"

    if contains_any(text, [
        "refund", "money back", "return my money",
        "রিফান্ড", "ফেরত"
    ]):
        return "refund_request", "medium"

    if contains_any(text, [
        "duplicate", "twice", "double charged", "charged twice",
        "দুইবার"
    ]):
        return "duplicate_payment", "high"

    if contains_any(text, [
        "settlement", "merchant settlement", "merchant balance",
        "merchant payment"
    ]):
        return "merchant_settlement_delay", "medium"

    if contains_any(text, [
        "cash in", "cash-in", "agent cash", "agent", "ক্যাশ ইন"
    ]):
        return "agent_cash_in_issue", "high"

    return "other", "low"


def find_relevant_transaction(complaint, transactions):
    complaint_lower = complaint.lower()

    # Match by transaction ID
    for tx in transactions:
        tx_id = str(tx.get("transaction_id", "")).lower()
        if tx_id and tx_id in complaint_lower:
            return tx

    # Match by amount
    numbers = re.findall(r"\d+", complaint)

    for tx in transactions:
        tx_amount = tx.get("amount")
        if tx_amount is None:
            continue

        for number in numbers:
            try:
                if float(number) == float(tx_amount):
                    return tx
            except ValueError:
                continue

    # If only one transaction is provided, assume likely relevant
    if len(transactions) == 1:
        return transactions[0]

    return None


def get_evidence_verdict(case_type, tx):
    if tx is None:
        return "insufficient_data"

    tx_status = str(tx.get("status", "")).lower()

    if case_type == "payment_failed":
        if tx_status in ["failed", "pending"]:
            return "consistent"
        if tx_status == "completed":
            return "inconsistent"
        return "insufficient_data"

    if case_type == "wrong_transfer":
        if tx_status == "completed":
            return "consistent"
        return "insufficient_data"

    if case_type == "duplicate_payment":
        return "insufficient_data"

    if case_type == "phishing_or_social_engineering":
        return "insufficient_data"

    return "consistent"


def make_customer_reply(case_type):
    if case_type == "phishing_or_social_engineering":
        return (
            "Please do not share your PIN, OTP, password, or account details with anyone. "
            "Use only official support channels. Your concern has been noted for review."
        )

    return (
        "We have noted your concern. Our support team will review the provided transaction details. "
        "Please do not share your PIN, OTP, password, or any secret credentials."
    )


@api_view(["POST"])
def analyze_ticket(request):
    data = request.data

    if "ticket_id" not in data:
        return Response(
            {"error": "Missing required field: ticket_id"},
            status=status.HTTP_400_BAD_REQUEST
        )

    if "complaint" not in data:
        return Response(
            {"error": "Missing required field: complaint"},
            status=status.HTTP_400_BAD_REQUEST
        )

    ticket_id = data.get("ticket_id")
    complaint = data.get("complaint")

    if not isinstance(complaint, str) or not complaint.strip():
        return Response(
            {"error": "Complaint cannot be empty."},
            status=status.HTTP_422_UNPROCESSABLE_ENTITY
        )

    transaction_history = data.get("transaction_history", [])

    if transaction_history is None:
        transaction_history = []

    if not isinstance(transaction_history, list):
        return Response(
            {"error": "transaction_history must be a list."},
            status=status.HTTP_400_BAD_REQUEST
        )

    case_type, severity = classify_case(complaint)
    department = CASE_DEPARTMENT_MAP[case_type]

    relevant_tx = find_relevant_transaction(complaint, transaction_history)

    if relevant_tx:
        relevant_transaction_id = relevant_tx.get("transaction_id")
    else:
        relevant_transaction_id = None

    evidence_verdict = get_evidence_verdict(case_type, relevant_tx)

    human_review_required = (
        case_type in [
            "wrong_transfer",
            "payment_failed",
            "duplicate_payment",
            "agent_cash_in_issue",
            "phishing_or_social_engineering",
        ]
        or severity in ["high", "critical"]
        or evidence_verdict in ["insufficient_data", "inconsistent"]
    )

    reason_codes = [case_type, evidence_verdict]

    if relevant_transaction_id:
        reason_codes.append("transaction_match")
    else:
        reason_codes.append("no_transaction_match")

    response_data = {
        "ticket_id": ticket_id,
        "relevant_transaction_id": relevant_transaction_id,
        "evidence_verdict": evidence_verdict,
        "case_type": case_type,
        "severity": severity,
        "department": department,
        "agent_summary": (
            f"Customer complaint classified as {case_type}. "
            f"Relevant transaction: {relevant_transaction_id if relevant_transaction_id else 'not found'}."
        ),
        "recommended_next_action": (
            "Review the complaint against the provided transaction history and route it to the assigned department. "
            "Do not ask for PIN, OTP, password, or secret credentials."
        ),
        "customer_reply": make_customer_reply(case_type),
        "human_review_required": human_review_required,
        "confidence": 0.75 if relevant_transaction_id else 0.45,
        "reason_codes": reason_codes,
    }

    return Response(response_data, status=status.HTTP_200_OK)