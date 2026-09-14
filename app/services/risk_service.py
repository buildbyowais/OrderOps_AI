def check_risk(customer):
    if customer.risk_score >= 70:
        return {
            "decision": "manual_review",
            "risk_score": customer.risk_score
        }

    return {
        "decision": "continue",
        "risk_score": customer.risk_score
    }