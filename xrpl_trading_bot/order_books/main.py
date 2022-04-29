from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import List

from xrpl_trading_bot.txn_parser.utils.types import ORDER_BOOK_SIDE_TYPE


@dataclass
class OrderBook:
    asks: ORDER_BOOK_SIDE_TYPE
    bids: ORDER_BOOK_SIDE_TYPE
    currency_pair: str
    exchange_rate: Decimal
    spread: Decimal

    @property
    def is_liquid(self: OrderBook):
        return self.spread < 1


class OrderBooks:
    def set_order_book(self: OrderBooks, order_book: OrderBook) -> None:
        self.__setattr__(order_book.currency_pair, order_book)

    def get_order_book(self: OrderBooks, currency_pair: str) -> OrderBook:
        return self.__getattribute__(currency_pair)

    def get_all_order_books(self: OrderBooks) -> List[OrderBook]:
        return [
            self.__getattribute__(currency_pair)
            for currency_pair in self.__dict__.keys()
        ]

    def get_liquid_order_books(self: OrderBooks):
        return [
            order_book
            for order_book in self.get_all_order_books()
            if order_book.is_liquid
        ]

    def get_illiquid_order_books(self: OrderBooks):
        return [
            order_book
            for order_book in self.get_all_order_books()
            if not order_book.is_liquid
        ]
