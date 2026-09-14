import os

from dotenv import load_dotenv
from google import genai
from google.genai import errors

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


def create_offer(
    original_product,
    alternative_product,
    discount_percent,
    customer_name=None
):
    # Database values are authoritative.
    original_price = float(original_product.price)
    alternative_price = float(alternative_product.price)
    discount = float(discount_percent)

    discounted_price = alternative_price * (
        1 - discount / 100
    )

    # AI only generates the customer-friendly message.
    prompt = f"""
You are an e-commerce customer support agent.

Create a short, polite and persuasive offer message.

Customer: {customer_name or "Customer"}

Original product:
{original_product.name}

Original price:
PKR {original_price:.2f}

The original product is out of stock.

Alternative product:
{alternative_product.name}

Alternative product price:
PKR {alternative_price:.2f}

Approved discount:
{discount:.2f}%

Final offered price:
PKR {discounted_price:.2f}

Rules:

* Do not change the product name.
* Do not change the discount.
* Do not change the final offered price.
* Do not invent any information.
* Clearly mention that the original product is out of stock.
* Clearly mention the alternative product.
* Clearly mention the discount.
* Clearly mention the final price.
* Keep the message under 40 words.
* Use simple, natural and customer-friendly language.
* Avoid unnecessary greetings, paragraphs, or repetition.
* Be professional and friendly.
"""

    try:
        response = client.models.generate_content(
                model="gemini-3.5-flash",
                contents=prompt
        )

    except errors.ServerError as e:
        print(f"[GEMINI] Server error: {e}")
        print("[GEMINI] AI offer generation temporarily unavailable.")

        # Fallback message — prices/discount remain database-controlled
        ai_message = (
            f"{original_product.name} is currently out of stock. "
            f"We can offer {alternative_product.name} with a "
            f"{discount:.0f}% discount for PKR {discounted_price:.2f}."
        )

    else:
        ai_message = response.text.strip()

    return {
        "original_product": original_product.name,
        "alternative_product": alternative_product.name,
        "original_price": original_price,
        "alternative_price": alternative_price,
        "discount_percent": discount,
        "offered_price": round(discounted_price, 2),
        "message": ai_message
    }
