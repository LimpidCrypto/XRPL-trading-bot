"""A collection of all constants"""

from xrpl_trading_bot.wallet import XRPWallet

WALLET = XRPWallet(
    seed=input("Enter your seed value: "),
    sequence=0,
)
