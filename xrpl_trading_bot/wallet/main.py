"""The wallet of the user."""

from __future__ import annotations

from typing import Dict

from xrpl.wallet import Wallet


class XRPWallet(Wallet):
    """Stores the cryptographic keys needed to interact with the XRP Ledger."""

    balances: Dict[str, str]
    """All currency balances the account holds."""

    def __init__(self: XRPWallet, seed: str, sequence: int) -> None:
        super().__init__(seed, sequence)
