"""Utils for methods and clients."""

from typing import Any, Dict


def _is_order_book(message: Dict[str, Any]) -> bool:
    """
    Checks if the received message was an order book.

    Args:
        message: Message received from subscription.

    Returns:
        If it's an order book or not.
    """
    if "result" in message:
        if "asks" in message["result"].keys() or "bids" in message["result"].keys():
            return True
    return False
