from xrpl_trading_bot.order_books.main import OrderBooks
from xrpl_trading_bot.trading.paths.spatial_arbitrage import (
    build_spatial_arbitrage_trading_paths
)
from xrpl_trading_bot.wallet.main import XRPWallet


def build_trading_paths(wallet: XRPWallet, order_books: OrderBooks):
    liquid_order_books = order_books.get_liquid_order_books()
    illiquid_order_books = order_books.get_illiquid_order_books()

    paths = set()

    paths.update(
        build_spatial_arbitrage_trading_paths(
            liquid_order_books=liquid_order_books,
            wallet=wallet
        )
    )

    return paths
