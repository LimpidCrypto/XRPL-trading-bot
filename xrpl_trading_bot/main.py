"""The main file of the whole project. Everything comes together here."""

from __future__ import annotations

from threading import Thread
from time import sleep
from typing import List

from xrpl_trading_bot.clients import (
    subscribe_to_account_balances,
    subscribe_to_order_books
)
from xrpl_trading_bot.globals import WALLET, all_order_books
from xrpl_trading_bot.order_books import build_subscibe_books
from xrpl_trading_bot.trading import trade


if __name__ == "__main__":
    balances_subscription = Thread(
        target=subscribe_to_account_balances,
        args=(WALLET,),
    )
    balances_subscription.start()
    sleep(3)
    subscribe_books = build_subscibe_books(wallet=WALLET)
    subscribe_book_threads: List[Thread] = []
    for chunk in subscribe_books:
        subscribe_book_threads.append(
            Thread(target=subscribe_to_order_books, args=(all_order_books, chunk,))
        )
    for num, thread in enumerate(subscribe_book_threads):
        thread.start()
        if num % 5 == 0:
            sleep(10)
    trade_thread = Thread(
        target=trade,
        args=(WALLET, all_order_books,)
    )
    trade_thread.start()
    trade_thread.join()
    for thread in subscribe_book_threads:
        thread.join()

    balances_subscription.join()
