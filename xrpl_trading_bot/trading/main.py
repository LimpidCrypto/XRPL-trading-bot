from xrpl_trading_bot.order_books.main import OrderBooks
from xrpl_trading_bot.trading.paths import build_trading_paths
from xrpl_trading_bot.wallet.main import XRPWallet


def trade(wallet: XRPWallet, order_books: OrderBooks):
    print(build_trading_paths(wallet=wallet, order_books=order_books))
