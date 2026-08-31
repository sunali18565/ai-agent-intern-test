from __future__ import annotations

from pathlib import Path
import json
from typing import Any


class OrderLookupTool:
    """
    Safe order lookup tool.

    Public responses contain only customer-safe order information.
    Internal fields such as email, address, internal notes, and
    risk scores are never returned.
    """

    def __init__(self, data_dir: str | Path):
        self.data_dir = Path(data_dir)
        self.orders_file = self.data_dir / "orders.json"
        self.orders = self._load_orders()

    def _load_orders(self) -> dict[str, dict[str, Any]]:
        """Load order records from the local dataset."""
        if not self.orders_file.exists():
            raise FileNotFoundError(
                f"Order data not found: {self.orders_file}"
            )

        with self.orders_file.open("r", encoding="utf-8") as file:
            data = json.load(file)

        # Support both a bare list and the assignment wrapper shape:
        # { "dataset_name": "...", "orders": [ ... ] }
        if isinstance(data, dict) and "orders" in data:
            data = data["orders"]

        if isinstance(data, list):
            return {
                order["order_id"].upper(): order
                for order in data
                if isinstance(order, dict) and "order_id" in order
            }

        if isinstance(data, dict):
            # Already keyed by order_id
            return {
                str(k).upper(): v
                for k, v in data.items()
                if isinstance(v, dict)
            }

        raise ValueError("orders.json must contain a list or dictionary.")

    def lookup(self, order_id: str) -> dict[str, Any]:
        """
        Look up an order using its order ID.
        Only safe, customer-facing fields are returned.
        """
        order_id = order_id.strip().upper()
        if not order_id:
            return {
                "found": False,
                "error": "Order ID is required.",
            }

        order = self.orders.get(order_id)
        if order is None:
            return {
                "found": False,
                "order_id": order_id,
                "error": "Order was not found.",
            }

        # Never expose internal/private fields.
        safe_fields = {
            "order_id",
            "status",
            "carrier",
            "tracking_number",
            "estimated_delivery",
            "shipped_at",
            "customer_safe_message",
        }

        safe_order = {
            key: value
            for key, value in order.items()
            if key in safe_fields
        }

        # Always include status from the raw record
        safe_order["status"] = order.get("status")
        safe_order["order_id"] = order_id

        status = str(order.get("status", "")).lower()

        # Special handling for cancelled orders — drop stale ETA/carrier.
        if status in {"cancelled", "canceled"}:
            safe_order.pop("estimated_delivery", None)
            safe_order.pop("carrier", None)
            safe_order.pop("tracking_number", None)

        # Shipped order without an ETA.
        if status == "shipped" and not order.get("estimated_delivery"):
            safe_order["delivery_estimate_available"] = False

        return {
            "found": True,
            "order": safe_order,
        }


def create_order_tool() -> OrderLookupTool:
    """Create the order lookup tool using the project dataset."""
    project_root = Path(__file__).resolve().parent.parent
    data_dir = project_root / "data"
    return OrderLookupTool(data_dir)


if __name__ == "__main__":
    tool = create_order_tool()
    for test_order_id in ["ORD-1007", "ORD-1004", "ORD-1011", "ORD-9999"]:
        result = tool.lookup(test_order_id)
        print(json.dumps(result, indent=2))