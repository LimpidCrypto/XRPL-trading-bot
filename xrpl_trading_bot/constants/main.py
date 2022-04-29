"""A collection of all constants"""

from getpass import getpass

from xrpl_trading_bot.wallet import XRPWallet

WALLET = XRPWallet(
    seed=getpass("Enter your seed value: "),
    sequence=0,
)

LIQUID_ORDER_BOOK_LIMIT = 1
