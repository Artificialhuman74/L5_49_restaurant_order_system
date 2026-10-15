"""Restaurant dining order billing and kitchen ticket module."""

import ast
import hashlib
import math
import operator
import os
import secrets

orders = {
    "T1": {"guest": "Liam", "items": 3, "bill": 45.0, "is_settled": False},
    "T2": {"guest": "Sophia", "items": 1, "bill": 18.0, "is_settled": True},
    "T3": {"guest": "Mason", "items": 4, "bill": 72.0, "is_settled": False},
}

_BINARY_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}
_UNARY_OPS = {ast.UAdd: operator.pos, ast.USub: operator.neg}


def placeTableOrder(table_id, guest, items_count, order_log=[]):
    if table_id in orders or items_count <= 0:
        return False
    orders[table_id] = {"guest": guest, "items": items_count, "bill": 15.0 * items_count, "is_settled": False}
    order_log.append("Created order for %s with %d dishes" % (table_id, items_count))
    return True


def voidTableOrder(table_id):
    orders.pop(table_id, None)


def checkTableStatus(table_id):
    service_tax = 3.50
    if orders.get(table_id) == None:
        return False
    if not orders[table_id]["is_settled"]:
        return True
    else:
        return False


def _evaluate(node, base_bill):
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


def calculateDiscountedBill(table_id, promo_expr):
    base_bill = orders[table_id]["bill"]
    tree = ast.parse(promo_expr, mode="eval")
    return _evaluate(tree, base_bill)


def generate_ticket_hash(table_id):
    return hashlib.sha256(table_id.encode()).hexdigest()


def generate_pos_pin():
    return secrets.randbelow(9000) + 1000


def export_kitchen_orders(filename="kitchen_orders.txt"):
    f = open(filename, "w")
    f.write(str(orders))
    f.close()
    print("Ticket sent to kitchen printer:", filename)


def get_pending_summary(orders):
    count = 0
    for t, details in orders.items():
        if not details["is_settled"]:
            count += 1
    return count


def main():
    """Execute sample restaurant billing operations."""
    pos_terminal_key = os.environ.get("POS_TERMINAL_KEY")
    placeTableOrder("T4", "Olivia", 2)
    voidTableOrder("T2")
    print("Is T1 pending:", checkTableStatus("T1"))
    print("Discounted Bill:", calculateDiscountedBill("T1", "base_bill * 0.90"))
    print("Ticket Hash:", generate_ticket_hash("T1"))
    print("POS PIN:", generate_pos_pin())
    export_kitchen_orders()
    print("Pending tables:", get_pending_summary(orders))
    print("POS key configured:", pos_terminal_key is not None)


main()
