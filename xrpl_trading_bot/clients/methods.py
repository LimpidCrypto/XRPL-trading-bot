from asyncio import run
from decimal import Decimal
from typing import Dict, List, cast

from websockets.exceptions import ConnectionClosedError
from xrpl.clients import WebsocketClient
from xrpl.models import AccountInfo, AccountLines, IssuedCurrency, Subscribe
from xrpl.models.requests.subscribe import SubscribeBook
from xrpl.utils import drops_to_xrp

from xrpl_trading_bot.clients.main import xrp_request_async
from xrpl_trading_bot.clients.utils import is_order_book
from xrpl_trading_bot.clients.websocket_uri import FullHistoryNodes, NonFullHistoryNodes
from xrpl_trading_bot.order_books import OrderBook, OrderBooks
from xrpl_trading_bot.txn_parser import parse_final_balances
from xrpl_trading_bot.txn_parser.order_book_changes import parse_final_order_book
from xrpl_trading_bot.txn_parser.utils.types import SubscriptionRawTxnType
from xrpl_trading_bot.wallet.main import XRPWallet


def get_current_account_balances(wallet: XRPWallet) -> None:
    """
    Get all currency balances the given account holds in a standard format.

    Args:
        account: The accounts address.
    """
    account_info, account_lines = run(
        xrp_request_async(
            requests=[
                AccountInfo(account=wallet.classic_address),
                AccountLines(account=wallet.classic_address),
            ]
        )
    )

    xrp_amount = {
        "XRP": str(drops_to_xrp(account_info.result["account_data"]["Balance"]))
    }

    token_amounts = {
        f"{token['currency']}.{token['account']}": token["balance"]
        for token in account_lines.result["lines"]
    }

    account_balances: Dict[str, str] = {}
    account_balances.update(xrp_amount)
    account_balances.update(token_amounts)

    wallet.balances = account_balances


def subscribe_to_account_balances(wallet: XRPWallet) -> None:
    """
    Receive the accounts balances once then subscribe to the account.
    The subscribtion receives transaction metadata everytime a transaction
    affects the account. It then parses the final balances and adjusts the
    balances of the wallet.

    Args:
        wallet: The wallet.
    """
    get_current_account_balances(wallet=wallet)

    with WebsocketClient(url=NonFullHistoryNodes.LIMPIDCRYPTO) as client:
        try:
            client.send(Subscribe(accounts=[wallet.classic_address]))
            for message in client:
                if "result" not in message:
                    txn = cast(SubscriptionRawTxnType, message)
                    final_balances = parse_final_balances(transaction=txn)
                    account_balances = final_balances[wallet.classic_address]
                    for balance in account_balances:
                        if balance["Currency"] == "XRP":
                            wallet.balances["XRP"] = balance["Value"]
                        else:
                            token = f"{balance['Currency']}.{balance['Counterparty']}"
                            wallet.balances[token] = balance["Value"]
                else:
                    pass
        except ConnectionClosedError:
            return None


def _get_snapshots_once(
    subscribe_books: List[SubscribeBook]
):
    responses = run(
        xrp_request_async(
            requests=[Subscribe(books=[book]) for book in subscribe_books],
            uri=FullHistoryNodes.XRPLF,
        )
    )
    assert len(responses) == len(subscribe_books)
    assert all([response.is_successful() for response in responses])
    order_books = [
        OrderBook.from_response(response=response)
        for response in responses if response.result["asks"] or response.result["bids"]
    ]
    successful_currency_pairs = set(
        order_book.currency_pair for order_book in order_books
    )
    subscribe_books_currency_pairs = []
    for book in subscribe_books:
        base = f"{book.taker_pays.currency}.{book.taker_pays.issuer}" if (
            isinstance(book.taker_pays, IssuedCurrency)
        ) else "XRP"
        counter = f"{book.taker_gets.currency}.{book.taker_gets.issuer}" if (
            isinstance(book.taker_gets, IssuedCurrency)
        ) else "XRP"
        currency_pair = f"{base}/{counter}"
        subscribe_books_currency_pairs.append(currency_pair)
    currency_pairs_diff = set(subscribe_books_currency_pairs).difference(
        successful_currency_pairs
    )
    order_books.extend(
        [
            OrderBook(
                asks=[],
                bids=[],
                currency_pair=pair,
                exchange_rate=Decimal(0),
                spread=Decimal(0)
            )
            for pair in currency_pairs_diff
        ]
    )
    assert len(order_books) == len(subscribe_books)

    return order_books


def subscribe_to_order_books(
    all_order_books: OrderBooks,  # future 'AllOrderBooks' class
    subscribe_books: List[SubscribeBook],
) -> None:
    """
    Receive all snapshots once and then receive all transactions
    that affected one order book and parse the new order books.

    Args:
        all_order_books:
            All order books.
        subscribe_books:
            Max. 10 SubscribeBook objects.
    """
    assert len(subscribe_books) <= 10
    order_books = _get_snapshots_once(
        subscribe_books=subscribe_books,
    )
    for order_book in order_books:
        all_order_books.set_order_book(order_book=order_book)

    all_subscription_book_currency_pairs = set()
    for book in subscribe_books:
        base = (
            f"{book.taker_pays.currency}.{book.taker_pays.issuer}"
            if (isinstance(book.taker_pays, IssuedCurrency))
            else "XRP"
        )
        counter = (
            f"{book.taker_gets.currency}.{book.taker_gets.issuer}"
            if (isinstance(book.taker_gets, IssuedCurrency))
            else "XRP"
        )
        all_subscription_book_currency_pairs.add(f"{base}/{counter}")
    with WebsocketClient(url=NonFullHistoryNodes.LIMPIDCRYPTO) as client:
        client.send(Subscribe(books=subscribe_books))
        for message in client:
            if is_order_book(message=message):
                continue
            else:
                parse_final_order_book(
                    all_order_books=all_order_books,
                    transaction=message,
                    to_xrp=True
                )
    return subscribe_books
