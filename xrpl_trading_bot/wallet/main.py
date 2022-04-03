"""The wallet of the user."""

from __future__ import annotations

from xrpl.wallet import Wallet


class XRPWallet(Wallet):
    """Stores the cryptographic keys needed to interact with the XRP Ledger."""

    def __init__(self: XRPWallet, seed: str, sequence: int) -> None:
        super().__init__(seed, sequence)
