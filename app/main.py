from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import traceback
from app.utils.database import SessionLocal
from app.models import Customer, Product, Order, Alternative, Refund

from app.services.risk_service import check_risk
from app.services.stock_service import check_stock
from app.services.alternative_service import find_alternatives
from app.services.offer_service import create_offer
from app.services.email_service import check_customer_response

import threading
import time

from app.workflow.order_workflow import order_workflow

from langgraph.types import Command


app = FastAPI(
    title="OrderOps AI",
    description="AI-Based Order Management System",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def automatic_email_checker():

    while True:

        db = SessionLocal()

        try:

            orders = db.query(Order).filter(
                ~Order.status.in_([
                    "ready_for_fulfillment",
                    "alternative_accepted",
                    "refunded"
                ])
            ).all()

            for order in orders:

                try:

                    email_response = check_customer_response(
                        order.id
                    )

                    if not email_response:
                        continue

                    decision = email_response.get(
                        "decision"
                    )

                    if decision not in [
                        "ACCEPT",
                        "REJECT"
                    ]:
                        continue

                    thread_id = f"order-{order.id}"

                    config = {
                        "configurable": {
                            "thread_id": thread_id
                        }
                    }

                    current_state = order_workflow.get_state(
                        config
                    )

                    if not current_state.values:

                        print(
                            f"[AUTO][ORDER #{order.id}] "
                            f"No workflow state found"
                        )

                        continue

                    print(
                        f"[AUTO][ORDER #{order.id}] "
                        f"Customer response: {decision}"
                    )

                    result = order_workflow.invoke(
                        Command(
                            resume=decision.lower()
                        ),
                        config=config
                    )

                    print(
                        f"[AUTO][ORDER #{order.id}] "
                        f"Completed: "
                        f"{result.get('final_status')}"
                    )

                except Exception as e:

                    print(
                        f"[AUTO][ERROR][ORDER #{order.id}] "
                        f"{e}"
                    )

        except Exception as e:

            print(
                f"[AUTO][ERROR] "
                f"Email checker: {e}"
            )

        finally:

            db.close()

        time.sleep(30)


email_checker_thread = threading.Thread(
    target=automatic_email_checker,
    daemon=True
)

email_checker_thread.start()


def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


class OrderCreate(BaseModel):

    customer_id: int
    product_id: int
    quantity: int = 1


class CustomerResponse(BaseModel):

    response: str


@app.get("/")
def home():

    return {
        "message": "OrderOps AI API is running!"
    }


@app.get("/products")
def get_products(
    db: Session = Depends(get_db)
):

    return db.query(Product).all()


@app.get("/customers")
def get_customers(
    db: Session = Depends(get_db)
):

    return db.query(Customer).all()


@app.get("/orders")
def get_orders(
    db: Session = Depends(get_db)
):

    return db.query(Order).all()


@app.post("/orders")
def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db)
):

    customer = db.query(Customer).filter(
        Customer.id == order_data.customer_id
    ).first()

    if not customer:

        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

    product = db.query(Product).filter(
        Product.id == order_data.product_id
    ).first()

    if not product:

        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    if order_data.quantity <= 0:

        raise HTTPException(
            status_code=400,
            detail="Quantity must be greater than 0"
        )

    new_order = Order(
        customer_id=order_data.customer_id,
        product_id=order_data.product_id,
        quantity=order_data.quantity,
        status="pending"
    )

    db.add(new_order)

    db.commit()

    db.refresh(new_order)

    return {
        "message": "Order created successfully",
        "order_id": new_order.id,
        "customer_id": new_order.customer_id,
        "product_id": new_order.product_id,
        "quantity": new_order.quantity,
        "status": new_order.status
    }


@app.get("/orders/{order_id}/risk-check")
def risk_check_order(
    order_id: int,
    db: Session = Depends(get_db)
):

    order = db.query(Order).filter(
        Order.id == order_id
    ).first()

    if not order:

        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    customer = db.query(Customer).filter(
        Customer.id == order.customer_id
    ).first()

    if not customer:

        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

    result = check_risk(customer)

    return {
        "order_id": order.id,
        "customer_id": customer.id,
        "customer_name": customer.name,
        "risk_score": result["risk_score"],
        "decision": result["decision"]
    }


@app.get("/orders/{order_id}/stock-check")
def stock_check_order(
    order_id: int,
    db: Session = Depends(get_db)
):

    order = db.query(Order).filter(
        Order.id == order_id
    ).first()

    if not order:

        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    product = db.query(Product).filter(
        Product.id == order.product_id
    ).first()

    if not product:

        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    result = check_stock(
        product,
        order.quantity
    )

    return {
        "order_id": order.id,
        "product_id": product.id,
        "product": product.name,
        "required_quantity": order.quantity,
        "available_stock": product.stock,
        "available": result["available"],
        "message": result["message"]
    }


@app.get("/orders/{order_id}/alternatives")
def get_order_alternatives(
    order_id: int,
    db: Session = Depends(get_db)
):

    order = db.query(Order).filter(
        Order.id == order_id
    ).first()

    if not order:

        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    alternatives = find_alternatives(
        order.product_id,
        db
    )

    result = []

    for alternative in alternatives:

        product = db.query(Product).filter(
            Product.id == alternative.alternative_product_id
        ).first()

        if not product:
            continue

        result.append({
            "product_id": product.id,
            "product_name": product.name,
            "price": float(product.price),
            "stock": product.stock,
            "discount_percent": float(
                alternative.discount_percent
            )
        })

    return {
        "order_id": order.id,
        "original_product_id": order.product_id,
        "alternatives": result
    }


@app.get("/orders/{order_id}/offer")
def get_order_offer(
    order_id: int,
    db: Session = Depends(get_db)
):

    order = db.query(Order).filter(
        Order.id == order_id
    ).first()

    if not order:

        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    original_product = db.query(Product).filter(
        Product.id == order.product_id
    ).first()

    if not original_product:

        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    alternative = db.query(Alternative).filter(
        Alternative.original_product_id == original_product.id
    ).first()

    if not alternative:

        raise HTTPException(
            status_code=404,
            detail="No alternative product found"
        )

    alternative_product = db.query(Product).filter(
        Product.id == alternative.alternative_product_id
    ).first()

    if not alternative_product:

        raise HTTPException(
            status_code=404,
            detail="Alternative product not found"
        )

    offer = create_offer(
        original_product,
        alternative_product,
        alternative.discount_percent
    )

    return offer


@app.post("/orders/{order_id}/process")
def process_order(
    order_id: int,
    db: Session = Depends(get_db)
):

    order = db.query(Order).filter(
        Order.id == order_id
    ).first()

    if not order:

        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    thread_id = f"order-{order_id}"

    try:

        result = order_workflow.invoke(
            {
                "order_id": order_id
            },
            config={
                "configurable": {
                    "thread_id": thread_id
                }
            }
        )

    except Exception as e:
        traceback.print_exc()
        
        raise HTTPException(
                status_code=500,
                detail=f"Workflow execution failed: {type(e).__name__}: {str(e)}"
        )

    if "__interrupt__" in result:

        interrupt_data = result[
            "__interrupt__"
        ][0].value

        return {
            "status": "waiting_for_customer",
            "order_id": order_id,
            "thread_id": thread_id,
            "message": interrupt_data["message"],
            "offer": interrupt_data["offer"]
        }

    return {
        "status": "completed",
        "order_id": order_id,
        "thread_id": thread_id,
        "final_status": result.get("final_status")
    }


@app.post("/orders/{order_id}/response")
def customer_response(
    order_id: int,
    response_data: CustomerResponse,
    db: Session = Depends(get_db)
):

    order = db.query(Order).filter(
        Order.id == order_id
    ).first()

    if not order:

        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    response = response_data.response.lower().strip()

    if response not in ["accept", "reject"]:

        raise HTTPException(
            status_code=400,
            detail="Response must be accept or reject"
        )

    thread_id = f"order-{order_id}"

    try:

        result = order_workflow.invoke(
            Command(resume=response),
            config={
                "configurable": {
                    "thread_id": thread_id
                }
            }
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Workflow resume failed: {str(e)}"
        )

    if "__interrupt__" in result:

        interrupt_data = result[
            "__interrupt__"
        ][0].value

        return {
            "status": "waiting_for_customer",
            "order_id": order_id,
            "thread_id": thread_id,
            "message": interrupt_data["message"],
            "offer": interrupt_data["offer"]
        }

    return {
        "status": "completed",
        "order_id": order_id,
        "thread_id": thread_id,
        "customer_response": response,
        "final_status": result.get("final_status")
    }


@app.post("/orders/{order_id}/refund")
def process_refund(
    order_id: int,
    db: Session = Depends(get_db)
):

    order = db.query(Order).filter(
        Order.id == order_id
    ).first()

    if not order:

        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    product = db.query(Product).filter(
        Product.id == order.product_id
    ).first()

    if not product:

        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    amount = float(product.price) * order.quantity

    refund = Refund(
        order_id=order.id,
        amount=amount,
        status="processed"
    )

    order.status = "refunded"

    db.add(refund)

    db.commit()

    db.refresh(refund)

    return {
        "message": "Refund processed successfully",
        "order_id": order.id,
        "refund_id": refund.id,
        "amount": amount,
        "status": order.status
    }


@app.post("/orders/{order_id}/fulfill")
def fulfill_order(
    order_id: int,
    db: Session = Depends(get_db)
):

    order = db.query(Order).filter(
        Order.id == order_id
    ).first()

    if not order:

        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    if order.status != "alternative_accepted":

        raise HTTPException(
            status_code=400,
            detail="Order is not ready for fulfillment"
        )

    order.status = "ready_for_fulfillment"

    db.commit()

    db.refresh(order)

    return {
        "message": "Order sent to fulfillment",
        "order_id": order.id,
        "status": order.status
    }


@app.post("/orders/{order_id}/fulfill-direct")
def fulfill_direct_order(
    order_id: int,
    db: Session = Depends(get_db)
):

    order = db.query(Order).filter(
        Order.id == order_id
    ).first()

    if not order:

        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    product = db.query(Product).filter(
        Product.id == order.product_id
    ).first()

    if not product:

        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    if product.stock < order.quantity:

        raise HTTPException(
            status_code=400,
            detail="Product does not have enough stock"
        )

    product.stock -= order.quantity

    order.status = "ready_for_fulfillment"

    db.commit()

    db.refresh(order)
    db.refresh(product)

    return {
        "message": "Order sent to fulfillment successfully",
        "order_id": order.id,
        "product": product.name,
        "quantity": order.quantity,
        "remaining_stock": product.stock,
        "status": order.status
    }


@app.post("/orders/{order_id}/check-email")
def check_email_response(
    order_id: int,
    db: Session = Depends(get_db)
):

    order = db.query(Order).filter(
        Order.id == order_id
    ).first()

    if not order:

        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    if order.status in [
        "ready_for_fulfillment",
        "alternative_accepted",
        "refunded"
    ]:

        return {
            "status": "already_completed",
            "order_id": order_id,
            "message": f"Order {order_id} has already been completed.",
            "final_status": order.status
        }

    try:

        email_response = check_customer_response(
            order_id
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Email checking failed: {str(e)}"
        )

    if not email_response:

        return {
            "status": "waiting_for_customer",
            "order_id": order_id,
            "message": "No customer response found yet."
        }

    if email_response.get("order_id") != order_id:

        return {
            "status": "different_order_response",
            "requested_order_id": order_id,
            "email_order_id": email_response.get(
                "order_id"
            ),
            "message": "Email response belongs to another order."
        }

    decision = email_response.get("decision")

    if decision not in ["ACCEPT", "REJECT"]:

        return {
            "status": "invalid_response",
            "order_id": order_id,
            "decision": decision,
            "message": "Customer response must contain ACCEPT or REJECT."
        }

    thread_id = f"order-{order_id}"

    try:

        result = order_workflow.invoke(
            Command(
                resume=decision.lower()
            ),
            config={
                "configurable": {
                    "thread_id": thread_id
                }
            }
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Workflow resume failed: {str(e)}"
        )

    return {
        "status": "completed",
        "order_id": order_id,
        "customer_response": decision.lower(),
        "final_status": result.get(
            "final_status"
        )
    }