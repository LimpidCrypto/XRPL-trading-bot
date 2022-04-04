"""The main file of the whole project. Everything comes together here."""

from __future__ import annotations

from threading import Thread

from xrpl_trading_bot.constants import WALLET
from xrpl_trading_bot.clients import subscribe_to_account_balances


if __name__ == "__main__":
    balances_subscribtion = Thread(
        target=subscribe_to_account_balances,
        args=(WALLET, ),
    )
    balances_subscribtion.start()

    balances_subscribtion.join()
