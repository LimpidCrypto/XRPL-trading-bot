from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, List, cast
from xrpl import XRPLException

from xrpl.models import IssuedCurrency, XRP, Response
from xrpl.models.requests.subscribe import SubscribeBook

from xrpl_trading_bot.txn_parser.utils.types import ORDER_BOOK_SIDE_TYPE
from xrpl_trading_bot.wallet.main import XRPWallet

LIQUID_ORDER_BOOK_LIMIT = 1


def build_subscibe_books(wallet: XRPWallet) -> List[List[SubscribeBook]]:
    def chunks(lst: List[SubscribeBook], n: int):
        """Yield successive n-sized chunks from lst."""
        for i in range(0, len(lst), n):
            yield lst[i:i + n]

    balances = wallet.balances
    subscribe_books = []
    for taker_gets_token in balances:
        for taker_pays_token in balances:
            if taker_gets_token != taker_pays_token:
                if taker_gets_token != "XRP":
                    taker_gets_currency, taker_gets_issuer = taker_gets_token.split(".")
                else:
                    taker_gets_currency = taker_gets_token
                if taker_pays_token != "XRP":
                    taker_pays_currency, taker_pays_issuer = taker_pays_token.split(".")
                else:
                    taker_pays_currency = taker_pays_token

                subscribe_book = SubscribeBook(
                    taker_gets=IssuedCurrency(
                        currency=taker_gets_currency,
                        issuer=taker_gets_issuer
                    )
                    if taker_gets_currency != "XRP"
                    else XRP(),
                    taker_pays=IssuedCurrency(
                        currency=taker_pays_currency,
                        issuer=taker_pays_issuer
                    )
                    if taker_pays_currency != "XRP"
                    else XRP(),
                    taker=wallet.classic_address,
                    both=True,
                    snapshot=True
                )

                flipped_subscribe_book = SubscribeBook(
                    taker_pays=IssuedCurrency(
                        currency=taker_gets_currency,
                        issuer=taker_gets_issuer
                    )
                    if taker_gets_currency != "XRP"
                    else XRP(),
                    taker_gets=IssuedCurrency(
                        currency=taker_pays_currency,
                        issuer=taker_pays_issuer
                    )
                    if taker_pays_currency != "XRP"
                    else XRP(),
                    taker=wallet.classic_address,
                    both=True,
                    snapshot=True
                )

                if flipped_subscribe_book not in subscribe_books:
                    subscribe_books.append(subscribe_book)

    return list(chunks(subscribe_books, 10))


def derive_currency_pair(asks: ORDER_BOOK_SIDE_TYPE, bids: ORDER_BOOK_SIDE_TYPE) -> str:
    """
    Derives the currency pair from an order book.

    Args:
        asks: Ask side of an order book.
        bids: Bid side of an order book.

    Returns:
        The order books currency pair.
    """
    if bids:
        bid = bids[0]
        base = (
            f"{bid['TakerPays']['currency']}.{bid['TakerPays']['issuer']}"
            if (isinstance(bid["TakerPays"], dict))
            else "XRP"
        )
        counter = (
            f"{bid['TakerGets']['currency']}.{bid['TakerGets']['issuer']}"
            if (isinstance(bid["TakerGets"], dict))
            else "XRP"
        )
        return f"{base}/{counter}"
    elif asks:
        ask = asks[0]
        base = (
            f"{ask['TakerGets']['currency']}.{ask['TakerGets']['issuer']}"
            if (isinstance(ask["TakerGets"], dict))
            else "XRP"
        )
        counter = (
            f"{ask['TakerPays']['currency']}.{ask['TakerPays']['issuer']}"
            if (isinstance(ask["TakerPays"], dict))
            else "XRP"
        )
        return f"{base}/{counter}"
    else:
        raise XRPLException("Cannot derive currency pair because order book is empty.")


class OrderBookNotFoundException(AttributeError):
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
        return self.spread < LIQUID_ORDER_BOOK_LIMIT and self.spread > Decimal(0)

    @classmethod
    def from_parser_result(cls, result: Dict[str, Any]) -> OrderBook:
        return cls(
            asks=result["asks"],
            bids=result["bids"],
            currency_pair=result["currency_pair"],
            exchange_rate=result["exchange_rate"],
            spread=result["spread"],
        )

    @classmethod
    def from_response(cls, response: Response):
        assert response.is_successful()
        result = response.result
        return cls(
            asks=result["asks"],
            bids=result["bids"],
            currency_pair=derive_currency_pair(
                asks=result["asks"],
                bids=result["bids"]
            ),
            exchange_rate=Decimal(0),
            spread=Decimal(0),
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
            try:
                base, counter = currency_pair.split("/")
                return cast(OrderBook, self.__getattribute__(f"{counter}/{base}"))
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
