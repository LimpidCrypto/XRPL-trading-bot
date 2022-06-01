from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from itertools import combinations
from typing import Any, Dict, Generator, List, Union, cast

from xrpl import XRPLException
from xrpl.models import XRP, IssuedCurrency, Response
from xrpl.models.requests.subscribe import SubscribeBook

from xrpl_trading_bot.txn_parser import (
    ORDER_BOOK_SIDE_TYPE,
    SubscriptionRawTxnType,
    XRPLOrderBookEmptyException,
    parse_final_order_book,
)
from xrpl_trading_bot.wallet import XRPWallet

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

    @property
    def spread(self: OrderBook) -> Decimal:
        """The spread of the order book."""
        if self.asks and self.bids:
            ask_quality = Decimal(cast(str, self.asks[0]["quality"]))
            bid_quality = Decimal(cast(str, self.bids[0]["quality"]))
            price_difference = ask_quality - bid_quality
            midpoint = (ask_quality + bid_quality) / 2
            quoted_spread = (price_difference / midpoint) * 100
            if quoted_spread < 0:
                raise BaseException(f"ask: {self.asks[0]}   bid: {self.bids[0]}")
            return Decimal(quoted_spread)
        else:
            return Decimal(0)

    @property
    def is_liquid(self: OrderBook) -> bool:
        """
        Determine if an order book is liquid or not.

        Returns:
            If an order book is liquid or not.
        """
        if self.spread < LIQUID_ORDER_BOOK_LIMIT:
            return True
        return False

    @classmethod
    def from_parser_result(cls, result: Dict[str, Any]) -> OrderBook:
        return cls(
            asks=result["asks"],
            bids=result["bids"],
            currency_pair=result["currency_pair"],
            exchange_rate=result["exchange_rate"],
        )

    @classmethod
    def from_response(cls, response: Response) -> OrderBook:
        assert response.is_successful()
        result = response.result
        return cls(
            asks=result["asks"],
            bids=result["bids"],
            currency_pair=derive_currency_pair(
                asks=result["asks"], bids=result["bids"]
            ),
            exchange_rate=Decimal(0),
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

    def update_order_books(
        self: OrderBooks,
        transaction: SubscriptionRawTxnType,
    ) -> None:
        all_order_books = self.get_all_order_books()
        for order_book in all_order_books:
            asks = order_book.asks
            bids = order_book.bids
            try:
                self.set_order_book(
                    order_book=order_book.from_parser_result(
                        parse_final_order_book(asks, bids, transaction, True)
                    )
                )
            except XRPLOrderBookEmptyException:
                pass

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


def _derive_currency(currency_issuer_pair: str) -> Union[XRP, IssuedCurrency]:
    if currency_issuer_pair == "XRP":
        return XRP()
    currency, issuer = currency_issuer_pair.split(".")
    return IssuedCurrency(currency=currency, issuer=issuer)


def _chunk_subscribe_books(
    subscribe_books: List[SubscribeBook],
) -> Generator[List[SubscribeBook], None, None]:
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(subscribe_books), 10):
        yield subscribe_books[i : i + 10]


def build_subscription_books(wallet: XRPWallet) -> List[List[SubscribeBook]]:
    balances = wallet.balances
    currencies = list(balances.keys())
    currency_combinations = [
        f"{pair[0]}/{pair[1]}" for pair in combinations(currencies, 2)
    ]
    subscribe_books: List[SubscribeBook] = []
    for combo in currency_combinations:
        taker_pays_currency, taker_gets_currency = combo.split("/")
        subscribe_books.append(
            SubscribeBook(
                taker_pays=_derive_currency(taker_pays_currency),
                taker_gets=_derive_currency(taker_gets_currency),
                taker=wallet.classic_address,
                snapshot=True,
                both=True,
            )
        )
    chunked_subscribe_books: List[List[SubscribeBook]] = list(
        _chunk_subscribe_books(subscribe_books)
    )
    return chunked_subscribe_books


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
