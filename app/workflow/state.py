from typing import TypedDict, Optional


class OrderState(TypedDict, total=False):
    order_id: int

    customer_id: int
    product_id: int
    quantity: int

    risk_score: int
    risk_decision: str

    stock_available: bool
    stock_deducted: bool

    alternative_product_id: Optional[int]

    offer: dict

    customer_response: str

    final_status: str
