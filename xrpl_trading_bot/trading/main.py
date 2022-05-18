from decimal import Decimal
from time import sleep
from xrpl_trading_bot.order_books.main import OrderBooks
from xrpl_trading_bot.trading.paths import build_trading_paths
from xrpl_trading_bot.wallet.main import XRPWallet


def trade(wallet: XRPWallet, order_books: OrderBooks):
    while True:
        trade_paths = build_trading_paths(wallet=wallet, order_books=order_books)
        profitable_paths = []
        for path in trade_paths:
            first_taker_gets = path["first_taker_gets"]
            second_taker_pays = path["second_taker_pays"]
            first_taker_gets_value = Decimal(
                first_taker_gets["value"]
                if isinstance(first_taker_gets, dict)
                else first_taker_gets
            )
            second_taker_pays_value = Decimal(
                second_taker_pays["value"]
                if isinstance(second_taker_pays, dict)
                else second_taker_pays
            )
            if second_taker_pays_value > first_taker_gets_value:
                profitable_paths.append(path)
        sleep(3)
