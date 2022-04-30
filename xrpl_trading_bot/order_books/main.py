from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, List, cast

from xrpl_trading_bot.txn_parser.utils.types import ORDER_BOOK_SIDE_TYPE

LIQUID_ORDER_BOOK_LIMIT = 1


class OrderBookNotFoundException(BaseException):
    """Gets raised if a requested order book could not be found."""

    pass


@dataclass
class OrderBook:
    asks: ORDER_BOOK_SIDE_TYPE
    """Ask side of an order book."""
    bids: ORDER_BOOK_SIDE_TYPE
    """Bid side of an order book."""
    currency_pair: str
    """The order books currency pair."""
    exchange_rate: Decimal
    """The currency exchange rate of the order book."""
    spread: Decimal
    """The spread of the order book."""

    @property
    def is_liquid(self: OrderBook) -> bool:
        """
        Determine if an order book is liquid or not.

        Returns:
            If an order book is liquid or not.
        """
        return self.spread < LIQUID_ORDER_BOOK_LIMIT

    @classmethod
    def from_parser_result(cls, result: Dict[str, Any]) -> OrderBook:
        return cls(
            asks=result["asks"],
            bids=result["bids"],
            currency_pair=result["currency_pair"],
            exchange_rate=result["exchange_rate"],
            spread=result["spread"],
        )


class OrderBooks:
    def set_order_book(self: OrderBooks, order_book: OrderBook) -> None:
        """
        Adds a new or replaces an old order book.

        Args:
            order_book: The order book.
        """
        new_exchange_rate = order_book.exchange_rate
        try:
            current_exchange_rate = self.get_order_book(
                currency_pair=order_book.currency_pair
            ).exchange_rate
        except OrderBookNotFoundException:
            current_exchange_rate = None
        if new_exchange_rate is not None:
            pass
        else:
            order_book.exchange_rate = current_exchange_rate
        self.__setattr__(order_book.currency_pair, order_book)

    def get_order_book(self: OrderBooks, currency_pair: str) -> OrderBook:
        """
        Get a specific order book by currency pair.

        Args:
            currency_pair: The order books currency pair.

        Raises:
            OrderBookNotFoundException: If the requested order book is not
                in this object.

        Returns:
            The requested order book.
        """
        try:
            return cast(OrderBook, self.__getattribute__(currency_pair))
        except AttributeError:
            raise OrderBookNotFoundException(
                "The requested order book could not be found."
            )

    def get_all_order_books(self: OrderBooks) -> List[OrderBook]:
        """
        Get all order books.

        Returns:
            A list of all order books.
        """
        return [
            self.__getattribute__(currency_pair)
            for currency_pair in self.__dict__.keys()
        ]

    def get_all_currency_pairs(self: OrderBooks) -> List[str]:
        return list(self.__dict__.keys())

    def get_liquid_order_books(self: OrderBooks) -> List[OrderBook]:
        """
        Get all liquid order books.

        Returns:
            A list of all liquid order books.
        """
        return [
            order_book
            for order_book in self.get_all_order_books()
            if order_book.is_liquid
        ]

    def get_illiquid_order_books(self: OrderBooks) -> List[OrderBook]:
        """
        Get all illiquid order books.

        Returns:
            A list of all illiquid order books.
        """
        return [
            order_book
            for order_book in self.get_all_order_books()
            if not order_book.is_liquid
        ]
