from typing import Literal

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command

from app.utils.database import SessionLocal
from app.models import (
    Order,
    Customer,
    Product,
    Alternative,
    Refund
)

from app.services.risk_service import check_risk
from app.services.stock_service import check_stock
from app.services.offer_service import create_offer
from app.services.email_service import send_offer_email

from app.workflow.state import OrderState


def start_order(state: OrderState):

    print(
        f"[WORKFLOW][ORDER #{state['order_id']}] "
        f"Starting order workflow"
    )

    db = SessionLocal()

    try:
        order = db.query(Order).filter(
            Order.id == state["order_id"]
        ).first()

        if not order:
            raise ValueError(
                f"Order {state['order_id']} not found"
            )

        print(
            f"[WORKFLOW][ORDER #{order.id}] "
            f"Order loaded"
        )

        return {
            "customer_id": order.customer_id,
            "product_id": order.product_id,
            "quantity": order.quantity,
            "final_status": "workflow_started"
        }

    finally:
        db.close()


def risk_check_node(state: OrderState):

    print(
        f"[RISK][ORDER #{state['order_id']}] "
        f"Checking customer risk"
    )

    db = SessionLocal()

    try:
        customer = db.query(Customer).filter(
            Customer.id == state["customer_id"]
        ).first()

        if not customer:
            raise ValueError(
                f"Customer {state['customer_id']} not found"
            )

        result = check_risk(customer)

        print(
            f"[RISK][ORDER #{state['order_id']}] "
            f"Score: {result['risk_score']} | "
            f"Decision: {result['decision']}"
        )

        return {
            "risk_score": result["risk_score"],
            "risk_decision": result["decision"]
        }

    finally:
        db.close()


def route_after_risk(state: OrderState) -> Literal[
    "stock_check",
    "manual_review"
]:

    if state["risk_decision"] == "manual_review":
        return "manual_review"

    return "stock_check"


def stock_check_node(state: OrderState):

    print(
        f"[STOCK][ORDER #{state['order_id']}] "
        f"Checking product stock"
    )

    db = SessionLocal()

    try:
        product = db.query(Product).filter(
            Product.id == state["product_id"]
        ).first()

        if not product:
            raise ValueError(
                f"Product {state['product_id']} not found"
            )

        result = check_stock(
            product,
            state["quantity"]
        )

        print(
            f"[STOCK][ORDER #{state['order_id']}] "
            f"Available: {result['available']}"
        )

        return {
            "stock_available": result["available"],
            "stock_deducted": False
        }

    finally:
        db.close()


def route_after_stock(state: OrderState) -> Literal[
    "fulfillment",
    "alternative"
]:

    if state["stock_available"]:
        return "fulfillment"

    return "alternative"


def fulfillment_node(state: OrderState):

    print(
        f"[FULFILLMENT][ORDER #{state['order_id']}] "
        f"Processing fulfillment"
    )

    db = SessionLocal()

    try:
        order = db.query(Order).filter(
            Order.id == state["order_id"]
        ).first()

        if not order:
            raise ValueError(
                f"Order {state['order_id']} not found"
            )

        product = db.query(Product).filter(
            Product.id == order.product_id
        ).first()

        if not product:
            raise ValueError(
                f"Product {order.product_id} not found"
            )

        if not state.get("stock_deducted", False):

            if product.stock < order.quantity:
                raise ValueError(
                    "Product does not have enough stock"
                )

            product.stock -= order.quantity

            print(
                f"[STOCK][ORDER #{order.id}] "
                f"Deducted: {order.quantity} | "
                f"Remaining: {product.stock}"
            )

        else:

            print(
                f"[STOCK][ORDER #{order.id}] "
                f"Already deducted | Skipping"
            )

        order.status = "ready_for_fulfillment"

        db.commit()

        db.refresh(order)
        db.refresh(product)

        print(
            f"[FULFILLMENT][ORDER #{order.id}] "
            f"Ready for fulfillment"
        )

        return {
            "final_status": "ready_for_fulfillment",
            "stock_deducted": True
        }

    finally:
        db.close()


def alternative_node(state: OrderState):

    print(
        f"[ALTERNATIVE][ORDER #{state['order_id']}] "
        f"Searching for alternative"
    )

    db = SessionLocal()

    try:
        alternatives = db.query(Alternative).filter(
            Alternative.original_product_id
            == state["product_id"]
        ).all()

        if not alternatives:
            return {
                "alternative_product_id": None,
                "final_status": "no_alternative_found"
            }

        for alternative in alternatives:

            alternative_product = db.query(Product).filter(
                Product.id
                == alternative.alternative_product_id
            ).first()

            if not alternative_product:
                continue

            if alternative_product.stock >= state["quantity"]:

                print(
                    f"[ALTERNATIVE][ORDER #{state['order_id']}] "
                    f"Found: {alternative_product.name}"
                )

                return {
                    "alternative_product_id":
                        alternative_product.id,
                    "final_status":
                        "alternative_found"
                }

        return {
            "alternative_product_id": None,
            "final_status":
                "no_available_alternative"
        }

    finally:
        db.close()


def offer_node(state: OrderState):

    print(
        f"[OFFER][ORDER #{state['order_id']}] "
        f"Creating AI-powered offer"
    )

    db = SessionLocal()

    try:

        order = db.query(Order).filter(
            Order.id == state["order_id"]
        ).first()

        if not order:
            raise ValueError(
                f"Order {state['order_id']} not found"
            )

        original_product = db.query(Product).filter(
            Product.id == state["product_id"]
        ).first()

        if not original_product:
            raise ValueError(
                f"Original product "
                f"{state['product_id']} not found"
            )

        alternative_id = state.get(
            "alternative_product_id"
        )

        if not alternative_id:
            return {
                "offer": {},
                "final_status": "no_offer_available"
            }

        alternative_product = db.query(Product).filter(
            Product.id == alternative_id
        ).first()

        if not alternative_product:
            raise ValueError(
                f"Alternative product "
                f"{alternative_id} not found"
            )

        alternative = db.query(Alternative).filter(
            Alternative.original_product_id
            == state["product_id"],

            Alternative.alternative_product_id
            == alternative_id
        ).first()

        if not alternative:
            raise ValueError(
                "Alternative relationship not found"
            )

        customer = db.query(Customer).filter(
            Customer.id == state["customer_id"]
        ).first()

        if not customer:
            raise ValueError(
                f"Customer "
                f"{state['customer_id']} not found"
            )

        customer_name = customer.name

        offer = create_offer(
            original_product=original_product,
            alternative_product=alternative_product,
            discount_percent=alternative.discount_percent,
            customer_name=customer_name
        )

        send_offer_email(
            customer_email=customer.email,
            customer_name=customer_name,
            offer=offer,
            order_id=order.id
        )

        print(
            f"[OFFER][ORDER #{order.id}] "
            f"Alternative: {alternative_product.name} | "
            f"Price: PKR {offer['offered_price']}"
        )

        print(
            f"[EMAIL][ORDER #{order.id}] "
            f"Offer sent to: {customer.email}"
        )

        return {
            "offer": offer,
            "final_status": "offer_created"
        }

    finally:
        db.close()


def customer_response_node(state: OrderState):

    print(
        f"[HITL][ORDER #{state['order_id']}] "
        f"Waiting for customer response"
    )

    response = interrupt({
        "message": "Please accept or reject the alternative offer.",
        "order_id": state["order_id"],
        "offer": state["offer"]
    })

    response = response.lower().strip()

    if response not in ["accept", "reject"]:
        raise ValueError(
            "Customer response must be 'accept' or 'reject'"
        )

    print(
        f"[HITL][ORDER #{state['order_id']}] "
        f"Customer response: {response.upper()}"
    )

    return {
        "customer_response": response
    }


def route_after_customer_response(
    state: OrderState
) -> Literal["accept", "reject"]:

    if state["customer_response"] == "accept":
        return "accept"

    return "reject"


def accept_node(state: OrderState):

    print(
        f"[ACCEPT][ORDER #{state['order_id']}] "
        f"Processing accepted alternative"
    )

    db = SessionLocal()

    try:
        order = db.query(Order).filter(
            Order.id == state["order_id"]
        ).first()

        if not order:
            raise ValueError(
                f"Order {state['order_id']} not found"
            )

        alternative_product_id = state.get(
            "alternative_product_id"
        )

        if not alternative_product_id:
            raise ValueError(
                "No alternative product selected"
            )

        alternative_product = db.query(Product).filter(
            Product.id == alternative_product_id
        ).first()

        if not alternative_product:
            raise ValueError(
                f"Alternative product "
                f"{alternative_product_id} not found"
            )

        quantity = state["quantity"]

        if alternative_product.stock < quantity:
            raise ValueError(
                "Alternative product does not have enough stock"
            )

        alternative_product.stock -= quantity

        order.product_id = alternative_product.id

        order.status = "alternative_accepted"

        db.commit()

        db.refresh(order)
        db.refresh(alternative_product)

        print(
            f"[ACCEPT][ORDER #{order.id}] "
            f"Product: {alternative_product.name} | "
            f"Remaining stock: {alternative_product.stock}"
        )

        return {
            "product_id": alternative_product.id,
            "stock_deducted": True,
            "final_status":
                "alternative_accepted"
        }

    finally:
        db.close()


def reject_node(state: OrderState):

    print(
        f"[REJECT][ORDER #{state['order_id']}] "
        f"Customer rejected the offer"
    )

    db = SessionLocal()

    try:
        order = db.query(Order).filter(
            Order.id == state["order_id"]
        ).first()

        if not order:
            raise ValueError(
                f"Order {state['order_id']} not found"
            )

        product = db.query(Product).filter(
            Product.id == order.product_id
        ).first()

        if not product:
            raise ValueError(
                f"Product {order.product_id} not found"
            )

        refund_amount = (
            float(product.price)
            * order.quantity
        )

        refund = Refund(
            order_id=order.id,
            amount=refund_amount,
            status="processed"
        )

        order.status = "refunded"

        db.add(refund)

        db.commit()

        db.refresh(refund)
        db.refresh(order)

        print(
            f"[REFUND][ORDER #{order.id}] "
            f"Processed: PKR {refund_amount}"
        )

        return {
            "final_status": "refunded"
        }

    finally:
        db.close()


def manual_review_node(state: OrderState):

    print(
        f"[MANUAL REVIEW][ORDER #{state['order_id']}] "
        f"Order flagged for manual review"
    )

    return {
        "final_status": "manual_review"
    }


builder = StateGraph(OrderState)


builder.add_node(
    "start_order",
    start_order
)

builder.add_node(
    "risk_check",
    risk_check_node
)

builder.add_node(
    "stock_check",
    stock_check_node
)

builder.add_node(
    "fulfillment",
    fulfillment_node
)

builder.add_node(
    "alternative",
    alternative_node
)

builder.add_node(
    "offer",
    offer_node
)

builder.add_node(
    "customer_response",
    customer_response_node
)

builder.add_node(
    "accept",
    accept_node
)

builder.add_node(
    "reject",
    reject_node
)

builder.add_node(
    "manual_review",
    manual_review_node
)


builder.add_edge(
    START,
    "start_order"
)

builder.add_edge(
    "start_order",
    "risk_check"
)


builder.add_conditional_edges(
    "risk_check",
    route_after_risk,
    {
        "stock_check": "stock_check",
        "manual_review": "manual_review"
    }
)


builder.add_conditional_edges(
    "stock_check",
    route_after_stock,
    {
        "fulfillment": "fulfillment",
        "alternative": "alternative"
    }
)


builder.add_edge(
    "fulfillment",
    END
)


builder.add_edge(
    "alternative",
    "offer"
)

builder.add_edge(
    "offer",
    "customer_response"
)


builder.add_conditional_edges(
    "customer_response",
    route_after_customer_response,
    {
        "accept": "accept",
        "reject": "reject"
    }
)


builder.add_edge(
    "accept",
    "fulfillment"
)


builder.add_edge(
    "reject",
    END
)


builder.add_edge(
    "manual_review",
    END
)


memory = MemorySaver()

order_workflow = builder.compile(
    checkpointer=memory
)