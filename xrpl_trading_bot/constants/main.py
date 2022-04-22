"""A collection of all constants"""

from getpass import getpass

from xrpl_trading_bot.wallet.main import XRPWallet
from xrpl_trading_bot.wallet import XRPWallet

WALLET = XRPWallet(
    seed=getpass("Enter your seed value: "),
    sequence=0,
)
