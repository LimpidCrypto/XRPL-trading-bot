"""A collection of all public nodes trustworthy."""


class FullHistoryNodes:
    """Full hisory (FH) nodes provide every existing ledger version."""

    XRPLF: str = "wss://xrplcluster.com/"
    """The FH node of the XRP Ledger Foundation."""

    RIPPLE: str = "wss://s2.ripple.com/"
    """The FH node of Ripple."""


class NonFullHistoryNodes:
    """Non full history nodes provide only a fraction of the entire blockchain."""

    LIMPIDCRYPTO: str = "wss://limpidcrypto.de:6005/"
    """My own non-FH node."""

    RIPPLE: str = "wss://s1.ripple.com/"
    """The non-FH node of Ripple."""

    SOLOGENIC: str = "wss://x1.sologenic.org"
    """The non-FH node of Sologenic"""
