from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from db import get_db
from models import Order, OrderItem, Payment
from schemas import OrderOut

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("/{email}", response_model=list[OrderOut])
def get_orders_by_email(email: str, db: Session = Depends(get_db)):
    """
    Returns all orders for a given email address, with items and payment history.

    Returns orders for an email, with items and payments loaded in one ORM query.
    """
    orders = (
        db.query(Order)
        .options(
            joinedload(Order.items),
            joinedload(Order.payments),
        )
        .filter(Order.user_email == email)
        .order_by(Order.created_at.desc())
        .all()
    )

    result = []
    for order in orders:
        order_dict = {
            "id":              order.id,
            "order_number":    order.order_number,
            "user_email":      order.user_email,
            "status":          order.status,
            "subtotal":        float(order.subtotal),
            "discount_amount": float(order.discount_amount or 0),
            "total":           float(order.total),
            "promo_code":      order.promo_code,
            "created_at":      order.created_at,
        }

        order_dict["items"] = [
            {
                "product_id":   i.product_id,
                "product_name": i.product_name,
                "quantity":     i.quantity,
                "unit_price":   float(i.unit_price),
                "total_price":  float(i.total_price),
            }
            for i in order.items
        ]

        ordered_payments = sorted(order.payments, key=lambda p: p.created_at)
        order_dict["payments"] = [
            {
                "id":             p.id,
                "amount":         float(p.amount),
                "status":         p.status,
                "payment_method": p.payment_method,
                "created_at":     p.created_at,
            }
            for p in ordered_payments
        ]

        result.append(order_dict)

    return result


@router.get("/detail/{order_id}", response_model=OrderOut)
def get_order(order_id: str, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    items    = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
    payments = db.query(Payment).filter(Payment.order_id == order.id).all()

    return {
        "id":              order.id,
        "order_number":    order.order_number,
        "user_email":      order.user_email,
        "status":          order.status,
        "subtotal":        float(order.subtotal),
        "discount_amount": float(order.discount_amount or 0),
        "total":           float(order.total),
        "promo_code":      order.promo_code,
        "created_at":      order.created_at,
        "items":           [
            {
                "product_id":   i.product_id,
                "product_name": i.product_name,
                "quantity":     i.quantity,
                "unit_price":   float(i.unit_price),
                "total_price":  float(i.total_price),
            }
            for i in items
        ],
        "payments": [
            {
                "id":             p.id,
                "amount":         float(p.amount),
                "status":         p.status,
                "payment_method": p.payment_method,
                "created_at":     p.created_at,
            }
            for p in payments
        ],
    }
