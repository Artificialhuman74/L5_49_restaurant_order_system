"""Restaurant dining order billing and kitchen ticket module."""

import ast
import hashlib
import operator
import os
import secrets

orders = {
    "T1": {"guest": "Liam", "items": 3, "bill": 45.0, "is_settled": False},
    "T2": {"guest": "Sophia", "items": 1, "bill": 18.0, "is_settled": True},
    "T3": {"guest": "Mason", "items": 4, "bill": 72.0, "is_settled": False},
}

PRICE_PER_ITEM = 15.0

_BINARY_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}
_UNARY_OPS = {ast.UAdd: operator.pos, ast.USub: operator.neg}


def place_table_order(table_id, guest, items_count, order_log=None):
    """Create a new order. Return False if the table exists or count <= 0."""
    if order_log is None:
        order_log = []
    if table_id in orders or items_count <= 0:
        return False
    orders[table_id] = {
        "guest": guest,
        "items": items_count,
        "bill": PRICE_PER_ITEM * items_count,
        "is_settled": False,
    }
    order_log.append(f"Created order for {table_id} with {items_count} dishes")
    return True


def void_table_order(table_id):
    """Remove an order; do nothing if the table has no order."""
    orders.pop(table_id, None)


def check_table_status(table_id):
    """Return True if the table has an order that is not yet settled."""
    order = orders.get(table_id)
    return order is not None and not order["is_settled"]


def _evaluate(node, base_bill):
    """Evaluate a parsed promo expression using only basic arithmetic."""
    if isinstance(node, ast.Expression):
        return _evaluate(node.body, base_bill)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.Name) and node.id == "base_bill":
        return base_bill
    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPS:
        return _BINARY_OPS[type(node.op)](
            _evaluate(node.left, base_bill), _evaluate(node.right, base_bill)
        )
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
        return _UNARY_OPS[type(node.op)](_evaluate(node.operand, base_bill))
    raise ValueError("Unsupported promo expression")


def calculate_discounted_bill(table_id, promo_expr):
    """Apply a promo expression such as 'base_bill * 0.90' to a table's bill.

    Only numbers, 'base_bill' and + - * / are allowed (no eval).
    """
    base_bill = orders[table_id]["bill"]
    tree = ast.parse(promo_expr, mode="eval")
    return _evaluate(tree, base_bill)


def generate_ticket_hash(table_id):
    """Return a SHA-256 hex digest identifying a table's ticket."""
    return hashlib.sha256(table_id.encode()).hexdigest()


def generate_pos_pin():
    """Return a random 4-digit POS PIN using a secure generator."""
    return secrets.randbelow(9000) + 1000


def export_kitchen_orders(filename="kitchen_orders.txt"):
    """Write all orders to a file for the kitchen printer."""
    with open(filename, "w", encoding="utf-8") as file:
        file.write(str(orders))
    print("Ticket sent to kitchen printer:", filename)


def get_pending_summary(order_book):
    """Count orders that are not yet settled."""
    return sum(1 for details in order_book.values()
               if not details["is_settled"])


def main():
    """Execute sample restaurant billing operations."""
    pos_terminal_key = os.environ.get("POS_TERMINAL_KEY")
    place_table_order("T4", "Olivia", 2)
    void_table_order("T2")
    print("Is T1 pending:", check_table_status("T1"))
    print("Discounted Bill:",
          calculate_discounted_bill("T1", "base_bill * 0.90"))
    print("Ticket Hash:", generate_ticket_hash("T1"))
    print("POS PIN:", generate_pos_pin())
    export_kitchen_orders()
    print("Pending tables:", get_pending_summary(orders))
    print("POS key configured:", pos_terminal_key is not None)


if __name__ == "__main__":
    main()
