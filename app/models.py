from sqlalchemy import Column, Integer, String, Numeric, ForeignKey
from sqlalchemy.orm import relationship

from app.utilts.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), nullable=False)
    phone = Column(String(20))
    risk_score = Column(Integer, default=0)

    orders = relationship("Order", back_populates="customer")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    category = Column(String(100))
    price = Column(Numeric(10, 2), nullable=False)
    stock = Column(Integer, default=0)

    orders = relationship("Order", back_populates="product")

    original_alternatives = relationship(
        "Alternative",
        foreign_keys="Alternative.original_product_id",
        back_populates="original_product"
    )

    alternative_products = relationship(
        "Alternative",
        foreign_keys="Alternative.alternative_product_id",
        back_populates="alternative_product"
    )


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)

    customer_id = Column(
        Integer,
        ForeignKey("customers.id"),
        nullable=False
    )

    product_id = Column(
        Integer,
        ForeignKey("products.id"),
        nullable=False
    )

    quantity = Column(Integer, nullable=False, default=1)

    status = Column(
        String(50),
        default="pending"
    )

    customer = relationship(
        "Customer",
        back_populates="orders"
    )

    product = relationship(
        "Product",
        back_populates="orders"
    )


class Alternative(Base):
    __tablename__ = "alternatives"

    id = Column(Integer, primary_key=True, index=True)

    original_product_id = Column(
        Integer,
        ForeignKey("products.id"),
        nullable=False
    )

    alternative_product_id = Column(
        Integer,
        ForeignKey("products.id"),
        nullable=False
    )

    discount_percent = Column(
        Numeric(5, 2),
        default=0
    )

    original_product = relationship(
        "Product",
        foreign_keys=[original_product_id],
        back_populates="original_alternatives"
    )

    alternative_product = relationship(
        "Product",
        foreign_keys=[alternative_product_id],
        back_populates="alternative_products"
    )

class Refund(Base):
    __tablename__ = "refunds"

    id = Column(Integer, primary_key=True, index=True)

    order_id = Column(
        Integer,
        ForeignKey("orders.id"),
        nullable=False
    )

    amount = Column(
        Numeric(10, 2),
        nullable=False
    )

    status = Column(
        String(50),
        default="pending"
    )