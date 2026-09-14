def find_alternatives(original_product_id, db):
    from models import Alternative

    alternatives = db.query(Alternative).filter(
        Alternative.original_product_id == original_product_id
    ).all()

    return alternatives