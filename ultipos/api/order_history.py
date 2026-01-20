# order_history.py:
import frappe
from frappe.utils import cint


@frappe.whitelist(allow_guest=True)
def get_orders_by_phone(phone: str = None, limit: int = 30):
    """
    Returns all orders for a customer using phone number.
    Also returns items preview for each order.
    """
    if not phone:
        frappe.throw("phone is required")

    phone = str(phone).strip()
    limit = cint(limit or 30)

    # ✅ find customer id(s)
    customer_ids = frappe.db.get_all(
        "Customer",
        filters={"phone": phone},
        pluck="name"
    )

    if not customer_ids:
        return {"phone": phone, "orders": []}

    # ✅ Orders list
    orders = frappe.db.get_all(
        "Order",
        filters={"customer": ["in", customer_ids]},
        fields=[
            "name",
            "order_number",
            "order_status",
            "payment_status",
            "total_amount",
            "discount_amount",
            "creation",
            "modified",
            "outlet",
            "restaurant"
        ],
        order_by="creation desc",
        limit=limit
    )

    out = []
    for o in orders:
        # ✅ Items preview for each order
        order_items = frappe.db.get_all(
            "Order Item",
            filters={"parent": o.name, "parenttype": "Order"},
            fields=["item_name", "qty", "total_price"],
            order_by="idx asc"
        )

        items_preview = []
        items_total_qty = 0

        for it in order_items:
            qty = int(it.qty or 0)
            items_total_qty += qty

            items_preview.append({
                "name": it.item_name,
                "qty": qty,
                "total_price": float(it.total_price or 0)
            })

        out.append({
            "order_id": o.name,
            "order_number": o.order_number,
            "status": o.order_status,
            "payment_status": o.payment_status,
            "grand_total": float(o.total_amount or 0),
            "discount": float(o.discount_amount or 0),
            "storeName": o.restaurant or "Store",
            "outlet": o.outlet,
            "createdAt": str(o.creation),
            "updatedAt": str(o.modified),

            # ✅ preview
            "items_total_qty": items_total_qty,
            "items_preview": items_preview
        })

    return {"phone": phone, "orders": out}