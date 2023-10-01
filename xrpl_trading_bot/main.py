"""The main file of the whole project. Everything comes together here."""

from __future__ import annotations

from threading import Thread
from time import sleep
from typing import List

from xrpl_trading_bot.clients import (
    subscribe_to_account_balances,
    subscribe_to_order_books,
)
from xrpl_trading_bot.clients.methods import (
    build_path_finds,
    get_gateway_fees,
    subscribe_to_payment_paths,
)
from xrpl_trading_bot.globals import (
    WALLET,
    all_order_books,
    gateway_fees,
    all_payment_paths,
)
from xrpl_trading_bot.order_books import build_subscription_books

if __name__ == "__main__":
    balances_subscribtion = Thread(
        target=subscribe_to_account_balances,
        args=(WALLET,),
    )
    balances_subscribtion.start()
    sleep(5)
    path_finds = build_path_finds(wallet=WALLET)

    paths_threads = [
        Thread(target=subscribe_to_payment_paths, args=(chunk, all_payment_paths, ))
        for chunk in path_finds
    ]
    for thread in paths_threads:
        thread.start()
    gateway_fees.update(get_gateway_fees(wallet=WALLET))
    subscribe_books = build_subscription_books(wallet=WALLET)
    subscribe_book_threads: List[Thread] = [
        Thread(
            target=subscribe_to_order_books,
            args=(
                all_order_books,
                chunk,
            ),
        )
        for chunk in subscribe_books
    ]
    for num, thread in enumerate(subscribe_book_threads):
        thread.start()
        if num % 5 == 0:
            sleep(10)
    balances_subscribtion.join()
    for thread in paths_threads:
        thread.join()
    for thread in subscribe_book_threads:
        thread.join()
