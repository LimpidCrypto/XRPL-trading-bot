"""The main file of the whole project. Everything comes together here."""

from __future__ import annotations

from threading import Thread

from xrpl_trading_bot.clients import (
    subscribe_to_account_balances,
    subscribe_to_order_books
)
from xrpl_trading_bot.globals import WALLET, all_order_books

if __name__ == "__main__":
    balances_subscription = Thread(
        target=subscribe_to_account_balances,
        args=(WALLET,),
    )
    balances_subscription.start()

    balances_subscription.join()
