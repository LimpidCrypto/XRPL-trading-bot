"""Parse order book changes caused by a transaction."""
from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, Optional, Union, cast

from xrpl_trading_bot.txn_parser.utils import (
    RawTxnType,
    SubscriptionRawTxnType,
    compute_order_book_changes,
    group_by_address_order_book,
    normalize_nodes,
    normalize_transaction,
    validate_transaction_fields,
)
from xrpl_trading_bot.txn_parser.utils.order_book_changes_utils import (
    compute_final_order_book,
)
from xrpl_trading_bot.txn_parser.utils.types import ORDER_BOOK_SIDE_TYPE


def parse_order_book_changes(
    transaction: Union[RawTxnType, SubscriptionRawTxnType],
) -> Dict[str, Any]:
    """Parse all order book changes that were caused by a transaction.

    Args:
        transaction (Union[RawTxnType, SubscriptionRawTxnType]):
            Raw transaction data including the account that
            sent the transaction and the affected nodes.

    Returns:
        Dict[str, Any]:
            Order book changes.
    """
    validate_transaction_fields(transaction_data=transaction)
    if "transaction" in transaction:
        transaction = cast(SubscriptionRawTxnType, transaction)
        transaction = normalize_transaction(transaction_data=transaction)

    nodes = normalize_nodes(transaction_data=transaction)
    order_changes = compute_order_book_changes(nodes=nodes)

    if order_changes:
        result = group_by_address_order_book(order_changes)
    else:
        result = {}

    return result


def parse_final_order_book(
    asks: ORDER_BOOK_SIDE_TYPE,
    bids: ORDER_BOOK_SIDE_TYPE,
    transaction: Optional[Union[RawTxnType, SubscriptionRawTxnType]],
    to_xrp: bool = False,
) -> Dict[str, Union[ORDER_BOOK_SIDE_TYPE, str, Optional[Decimal]]]:
    """
    Parses the new order book after a transaction affected it.

    Args:
        asks: Order books ask side.
        bids: Order books bid side.
        transaction: The raw transaction data.
        to_xrp: If the currency amount should be converted from drops to XRP.
            Defaults to False.

    Returns:
        A dictionary with the new order book, the currency pair,
        the exchange rate if an offer was modified and the order books spread.
    """
    if transaction is not None:
        validate_transaction_fields(transaction_data=transaction)
        if "transaction" in transaction:
            transaction = cast(SubscriptionRawTxnType, transaction)
            transaction = normalize_transaction(transaction_data=transaction)
    asks, bids, pair, ex_rate, spread = compute_final_order_book(
        asks=asks,
        bids=bids,
        transaction=cast(Optional[RawTxnType], transaction),
        to_xrp=to_xrp,
    )
    return {
        "asks": asks,
        "bids": bids,
        "currency_pair": pair,
        "exchange_rate": Decimal(ex_rate) if ex_rate is not None else ex_rate,
        "spread": Decimal(spread) if spread is not None else spread,
    }
