"""A collection of all global variables."""

from decimal import Decimal
from typing import Dict

from xrpl_trading_bot.order_books import OrderBooks

all_order_books = OrderBooks()
gateway_fees: Dict[str, Decimal] = {}
