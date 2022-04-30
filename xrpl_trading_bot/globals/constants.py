"""A collection of all global constants."""

from getpass import getpass

from xrpl_trading_bot.wallet import XRPWallet

WALLET = XRPWallet(
    seed=getpass("Enter your seed value: "),
    sequence=0,
)
