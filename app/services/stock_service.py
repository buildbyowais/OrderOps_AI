def check_stock(product, quantity):
    if product.stock >= quantity:
        return {
            "available": True,
            "message": "Product is in stock"
        }

    return {
        "available": False,
        "message": "Product is out of stock"
    }