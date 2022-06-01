"""Utils for order_book_changes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple, Union, cast

from pydash import filter_, group_by, map_  # type: ignore
from typing_extensions import Literal
from xrpl import XRPLException
from xrpl.utils.xrp_conversions import XRPRangeException, drops_to_xrp

from xrpl_trading_bot.txn_parser.utils.types import (
    CURRENCY_AMOUNT_TYPE,
    ORDER_BOOK_SIDE_TYPE,
    AccountBalance,
    NormalizedNode,
    RawTxnType,
    SubscriptionRawTxnType,
)

LFS_SELL = 0x00020000


@dataclass
class OrderChange:
    """Order change."""

    taker_pays: CURRENCY_AMOUNT_TYPE
    """TakerPays amount"""
    taker_gets: CURRENCY_AMOUNT_TYPE
    """TakerGets amount"""
    sell: bool
    """If flag 'sell' is set"""
    sequence: int
    """Sequence number"""
    status: Optional[
        Union[
            Literal["created"],
            Literal["partially-filled"],
            Literal["filled"],
            Literal["cancelled"],
        ]
    ]
    """Status of the offer"""
    quality: str
    """Offer quality"""
    expiration: Optional[Union[int, str]] = None
    """Expiration"""
    direction: Optional[str] = None
    """Buy or Sell."""
    total_received: Optional[CURRENCY_AMOUNT_TYPE] = None
    """Amount received"""
    total_paid: Optional[CURRENCY_AMOUNT_TYPE] = None
    """Amount paid"""
    account: Optional[str] = None
    """Accounts address"""


class ChangeAmount:
    """Amount changed by transaction."""

    def __init__(
        self: ChangeAmount,
        final_amount: Dict[str, str],
        previous_value: str,
    ) -> None:
        """
        Args:
            final_amount (Dict[str, str]): Final amount
            previous_value (str): Difference to Previous amount
        """
        self.final_amount = final_amount
        self.previous_value = previous_value


class XRPLOrderBookEmptyException(XRPLException):
    pass


def group_by_address_order_book(
    order_changes: List[Dict[str, Union[Dict[str, str], bool, int, str]]]
) -> Dict[
    str,
    List[Dict[str, Union[Dict[str, Union[Dict[str, str], str]], str, int, bool]]],
]:
    """Group order book changes by addresses.

    Args:
        order_changes (List[Dict[str, Union[Dict[str, str], bool, int, str]]]):
            Order book changes

    Returns:
        Dict[str, Union[Dict[str, Union[Dict[str, str], str]], str, int, bool]]:
            Order book changes grouped by addresses.
    """
    return group_by(order_changes, lambda change: change["account"])  # type: ignore


def _parse_currency_amount(
    currency_amount: Union[str, AccountBalance]
) -> AccountBalance:
    """Parses an accounts balance and formats it into a standard format.

    Args:
        currency_amount (Union[str, AccountBalance]):
            Currency amount.

    Returns:
        AccountBalance: Account balance.
    """
    if isinstance(currency_amount, str):
        return AccountBalance(
            currency="XRP", counterparty="", value=str(drops_to_xrp(currency_amount))
        )

    return AccountBalance(
        currency=currency_amount.currency,
        counterparty=currency_amount.counterparty,
        value=str(currency_amount.value),
    )


def _calculate_delta(
    final_amount: Optional[AccountBalance],
    previous_amount: Optional[AccountBalance],
) -> Union[Decimal, int]:
    if isinstance(final_amount, AccountBalance) and isinstance(
        previous_amount, AccountBalance
    ):
        previous_value = Decimal(previous_amount.value)
        return 0 - previous_value

    return 0


def _parse_order_status(
    node: NormalizedNode,
) -> Optional[Literal["created", "partially-filled", "filled", "cancelled"]]:
    """Parses the status of an order.

    Returns:
        Optional[Literal['created', 'partially-filled', 'filled', 'cancelled']]:
            The order status.
    """
    if node.diff_type == "CreatedNode":
        return "created"

    if node.diff_type == "ModifiedNode":
        return "partially-filled"

    if node.diff_type == "DeletedNode":
        if hasattr(node, "previous_fields") and hasattr(
            node.previous_fields, "TakerPays"
        ):
            return "filled"
        return "cancelled"

    return None


def _parse_change_amount(
    node: NormalizedNode, side: Literal["TakerPays", "TakerGets"]
) -> Optional[Union[AccountBalance, ChangeAmount]]:
    """Parse the changed amount of an order.

    Args:
        node (NormalizedNode):
            Normalized node.
        side (Literal['TakerPays', 'TakerGets']):
            Side of the order to parse.

    Returns:
        Optional[Union[AccountBalance, ChangeAmount]]:
            The changed currency amount.
    """
    status = _parse_order_status(node=node)

    if status == "cancelled":
        return (
            _parse_currency_amount(currency_amount=getattr(node.final_fields, side))
            if (hasattr(node.final_fields, side))
            else None
        )
    if status == "created":
        return (
            _parse_currency_amount(currency_amount=getattr(node.new_fields, side))
            if (hasattr(node.new_fields, side))
            else None
        )

    # Else it has modified an offer.
    # Status is 'partially-filled' or 'filled'.
    final_amount = (
        _parse_currency_amount(currency_amount=getattr(node.final_fields, side))
        if (hasattr(node.final_fields, side))
        else None
    )
    previous_amount = (
        _parse_currency_amount(currency_amount=getattr(node.previous_fields, side))
        if (hasattr(node.previous_fields, side))
        else None
    )
    value = _calculate_delta(
        final_amount=final_amount,
        previous_amount=previous_amount,
    )

    change_amount = ChangeAmount(
        final_amount=final_amount.__dict__, previous_value=str(0 - value)
    )

    return change_amount


def _get_quality(node: NormalizedNode) -> str:
    """Calculate the offers quality.

    Args:
        node (NormalizedNode): Normalized node.

    Returns:
        str: The offers quality.
    """
    if node.final_fields is not None:
        taker_gets = cast(Union[AccountBalance, str], node.final_fields.TakerGets)
        taker_pays = cast(Union[AccountBalance, str], node.final_fields.TakerPays)
    elif node.new_fields is not None:
        taker_gets = cast(Union[AccountBalance, str], node.new_fields.TakerGets)
        taker_pays = cast(Union[AccountBalance, str], node.new_fields.TakerPays)
    else:
        taker_gets = "0"
        taker_pays = "0"

    taker_gets_value = (
        drops_to_xrp(taker_gets)
        if (isinstance(taker_gets, str))
        else Decimal(taker_gets.value)
    )
    taker_pays_value = (
        drops_to_xrp(taker_pays)
        if (isinstance(taker_pays, str))
        else Decimal(taker_pays.value)
    )

    if taker_gets_value > 0 and taker_pays_value > 0:
        return str(taker_pays_value / taker_gets_value)

    return "0"


def _ripple_to_unix_timestamp(rpepoch: int) -> int:
    return rpepoch + 0x386D4380


def _get_expiration_time(node: NormalizedNode) -> Optional[str]:
    """Formats the ripple timestamp to a easy to read format.

    Args:
        node (NormalizedNode): Normalized node.

    Returns:
        Optional[str]:
            Expiration time in a easy to read format.
    """
    if node.final_fields is not None:
        expiration_time = node.final_fields.Expiration
    elif node.new_fields is not None:
        expiration_time = node.new_fields.Expiration
    else:
        expiration_time = None

    if not isinstance(expiration_time, int):
        return expiration_time

    return str(
        datetime.utcfromtimestamp(_ripple_to_unix_timestamp(expiration_time)).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )


def _remove_undefined(
    order: Union[OrderChange, NormalizedOffer]
) -> Union[OrderChange, NormalizedOffer]:
    """Remove all attributes that are 'None'.

    Args:
        order: Order change or normalized offer.

    Returns:
        Cleaned up object.
    """
    order_dict = order.__dict__.copy()

    for attr, value in order_dict.items():
        if value is None:
            delattr(order, attr)

    return order


def _calculate_received_and_paid_amount(
    taker_gets: CURRENCY_AMOUNT_TYPE,
    taker_pays: CURRENCY_AMOUNT_TYPE,
    direction: Literal["sell", "buy"],
) -> Tuple[CURRENCY_AMOUNT_TYPE, CURRENCY_AMOUNT_TYPE]:
    """Calculate what the taker had to pay and what he received.

    Args:
        taker_gets (CURRENCY_AMOUNT_TYPE):
            TakerGets amount.
        taker_pays (CURRENCY_AMOUNT_TYPE):
            TakerPays amount.
        direction (Literal["buy", "sell"]):
            'buy' or 'sell' offer.

    Returns:
        Tuple[CURRENCY_AMOUNT_TYPE, CURRENCY_AMOUNT_TYPE]:
            Both paid and received amount.
    """
    quantity = taker_pays if direction == "buy" else taker_gets
    total_price = taker_gets if direction == "buy" else taker_pays

    return quantity, total_price


def _convert_order_change(order: OrderChange) -> OrderChange:
    """Convert order change.

    Args:
        order (OrderChange):
            Order change.

    Returns:
        OrderChange:
            Converted order change.
    """
    taker_gets = order.taker_gets
    taker_pays = order.taker_pays
    direction: Literal["sell", "buy"] = "sell" if order.sell else "buy"
    quantity, total_price = _calculate_received_and_paid_amount(
        taker_gets=taker_gets,
        taker_pays=taker_pays,
        direction=direction,
    )

    order.direction = direction
    order.total_received = quantity
    order.total_paid = total_price

    cleaned_order = _remove_undefined(order=order)
    assert isinstance(cleaned_order, OrderChange)
    return cleaned_order


def _parse_order_change(
    node: NormalizedNode,
) -> Dict[str, Union[Dict[str, str], bool, int, str]]:
    """Parse a change in the order book.

    Args:
        node (NormalizedNode):
            The affected node.

    Returns:
        Dict[str, Union[Dict[str, str], bool, int, str ]]:
            A order book change.
    """
    if node.final_fields is not None:
        seq = cast(int, node.final_fields.Sequence)
    elif node.new_fields is not None:
        seq = cast(int, node.new_fields.Sequence)

    if node.final_fields is not None:
        flags = cast(int, node.final_fields.Flags)
        sell = flags & LFS_SELL != 0
    else:
        sell = False

    order_change = OrderChange(
        taker_pays=_parse_change_amount(node, "TakerPays").__dict__,
        taker_gets=_parse_change_amount(node, "TakerGets").__dict__,
        sell=sell,
        sequence=seq,
        status=_parse_order_status(node),
        quality=_get_quality(node),
        expiration=_get_expiration_time(node),
    )
    order_change = _convert_order_change(order_change)

    if node.final_fields is not None:
        order_change.account = node.final_fields.Account
    elif node.new_fields is not None:
        order_change.account = node.new_fields.Account
    else:
        order_change.account = ""

    return order_change.__dict__


def compute_order_book_changes(
    nodes: List[NormalizedNode],
) -> List[Dict[str, Union[Dict[str, str], bool, int, str]]]:
    """Filter nodes by 'EntryType': 'Offer'.

    Args:
        nodes (List[NormalizedNode]): Affected nodes.

    Returns:
        List[Dict[str, Union[Dict[str, str], bool, int, str]]]:
            A unsorted list of all order book changes.
    """
    filter_nodes = map_(
        filter_(nodes, lambda node: True if node.entry_type == "Offer" else False),
        _parse_order_change,
    )

    return filter_nodes  # type: ignore


@dataclass
class NormalizedOffer:
    diff_type: str
    identifiers: Union[Tuple[str, str], Tuple[None, None]]
    Account: str
    BookDirectory: str
    BookNode: str
    Flags: int
    OwnerNode: str
    PreviousTxnID: str
    PreviousTxnLgrSeq: int
    Sequence: int
    TakerGets: CURRENCY_AMOUNT_TYPE
    TakerPays: CURRENCY_AMOUNT_TYPE
    index: str
    quality: str
    LedgerEntryType: str = "Offer"
    owner_funds: Optional[str] = None
    taker_gets_funded: Optional[CURRENCY_AMOUNT_TYPE] = None
    taker_pays_funded: Optional[CURRENCY_AMOUNT_TYPE] = None


def _format_drops_to_xrp(
    amount: Optional[CURRENCY_AMOUNT_TYPE],
) -> Optional[CURRENCY_AMOUNT_TYPE]:
    """
    Takes a currency amount, derives its value and tries to format drops to XRP
    if needed.

    Args:
        amount: A currency amount.

    Returns:
        The adjusted currency amount
    """
    if not isinstance(amount, dict) and amount is not None:
        try:
            return str(drops_to_xrp(drops=amount))
        except XRPRangeException:
            assert isinstance(amount, str)
            return amount
    else:
        return amount


def _derive_field(node: Dict[str, Any], field_name: str, to_xrp: bool = False) -> Any:
    """
    Takes a node and derives the wanted field from it.
    If it is an currency amount it is possible to convert the value to XRP.

    Args:
        node: The node.
        field_name: The wished field name.
        to_xrp: If the field should be converted to XRP. Defaults to False.

    Returns:
        The wished field.
    """
    if "NewFields" in node[list(node.keys())[0]]:
        try:
            field = node[list(node.keys())[0]]["NewFields"][field_name]
            if to_xrp:
                field = _format_drops_to_xrp(amount=field)
            return field
        except KeyError:
            return "0"

    field = node[list(node.keys())[0]]["FinalFields"][field_name]
    if to_xrp:
        field = _format_drops_to_xrp(amount=field)
    return field


def _format_quality(quality: str) -> str:
    """
    If the quality is expressed in scientific notation
    it converts it to a normal float-point number as string.

    Args:
        quality: The quality.

    Returns:
        The formatted quality.
    """
    if "E" in quality:
        num, off = quality.split("E")
        i, d = str(float(num)).split(".")
        if float(off) < 0:
            ld = len(d)
            lenght = ld + abs(float(off))
            f = "f'{{{}:.{}f}}'".format(float(quality), int(lenght))
            f = str(eval(f))
            return f.rstrip("0")

    return quality


def _derive_quality(
    taker_gets: CURRENCY_AMOUNT_TYPE,
    taker_pays: CURRENCY_AMOUNT_TYPE,
    pair: str,
) -> str:
    """
    Derives the quality of an offer considering the order books side.

    Args:
        taker_gets: TakerGets amount.
        taker_pays: TakerPays amount.
        pair: The currency pair of the given order book.

    Returns:
        The offer's quality.
    """
    possible_base = (
        f"{taker_pays['currency']}.{taker_pays['issuer']}"
        if (isinstance(taker_pays, dict))
        else "XRP"
    )
    possible_counter = (
        f"{taker_gets['currency']}.{taker_gets['issuer']}"
        if (isinstance(taker_gets, dict))
        else "XRP"
    )
    possible_currency_pair = f"{possible_base}/{possible_counter}"

    taker_gets_value = (
        taker_gets["value"] if (isinstance(taker_gets, dict)) else taker_gets
    )
    taker_pays_value = (
        taker_pays["value"] if (isinstance(taker_pays, dict)) else taker_pays
    )

    if taker_gets_value == "0" or taker_pays_value == "0":
        return "0"

    quality = Decimal(taker_gets_value) / Decimal(taker_pays_value)
    if possible_currency_pair != pair:
        return _format_quality("{:.12}".format(1 / quality))

    return _format_quality("{:.12}".format(quality))


def _derive_unfunded_amounts(
    owner_funds: str, quality: str, taker_gets: CURRENCY_AMOUNT_TYPE
) -> Union[Tuple[str, str], Tuple[None, None]]:
    """
    Calculate the unfunded amount if `owner_funds` is lower than the `TakerGets` amount.

    Args:
        owner_funds: The TakerGets currency's amount that the owner of the offer
            actually hold's.
        quality: The offer's quality.
        taker_gets: TakerGets amount.
        to_xrp: Convert to XRP.

    Returns:
        The unfunded amount.
    """
    if isinstance(taker_gets, dict):
        taker_gets_value = taker_gets["value"]
    else:
        taker_gets_value = taker_gets
    if Decimal(taker_gets_value) > Decimal(owner_funds):
        taker_gets_funded = owner_funds
        taker_pays_funded = Decimal(owner_funds) * Decimal(quality)
        return taker_gets_funded, "{:.12}".format(taker_pays_funded)
    return (None, None)


def _derive_identifiers(
    offer: Dict[str, Any],
    diff_type: Literal["CreatedNode", "ModifiedNode", "DeletedNode"],
) -> Union[Tuple[str, str], Tuple[None, None]]:
    """
    Derive fields to identify old offers.

    Args:
        offer: Offer object.
        diff_type: Type of node.

    Returns:
        Identifier fields.
    """
    if diff_type == "ModifiedNode":
        return (
            offer["ModifiedNode"]["PreviousTxnID"],
            offer["ModifiedNode"]["PreviousTxnLgrSeq"],
        )
    elif diff_type == "DeletedNode":
        return (
            offer["DeletedNode"]["FinalFields"]["PreviousTxnID"],
            offer["DeletedNode"]["FinalFields"]["PreviousTxnLgrSeq"],
        )
    else:
        return None, None


def _normalize_offer(
    offer: Dict[
        str,
        Dict[str, Union[str, int, Dict[str, Union[str, int, Dict[str, str]]]]],
    ],
    new_prev_txn_id: str,
    new_prev_txn_lgr_seq: int,
    pair: str,
    to_xrp: bool,
    owner_funds: Optional[str] = None,
) -> NormalizedOffer:
    """
    Normalizes an offer object.

    Args:
        offer: Offer node.
        new_prev_txn_id: The transactions transaction hash
        new_prev_txn_lgr_seq: The ledger sequence the transcation was included in.
        pair: Currency pair.
        to_xrp: If currency amount should be converted from drops to XRP.
        owner_funds: The TakerGets amount that the account actually holds.
            Defaults to None.

    Returns:
        The offer in a standard format.
    """
    diff_type = cast(
        Literal["CreatedNode", "ModifiedNode", "DeletedNode"], list(offer.keys())[0]
    )
    assert diff_type in ["CreatedNode", "ModifiedNode", "DeletedNode"]
    taker_gets = _derive_field(node=offer, field_name="TakerGets", to_xrp=to_xrp)
    taker_pays = _derive_field(node=offer, field_name="TakerPays", to_xrp=to_xrp)
    quality = str(
        _derive_quality(
            taker_gets=taker_gets,
            taker_pays=taker_pays,
            pair=pair,
        )
    )
    if to_xrp and owner_funds is not None:
        owner_funds = _format_drops_to_xrp(amount=owner_funds)  # type: ignore
    taker_gets_funded, taker_pays_funded = (
        _derive_unfunded_amounts(
            owner_funds=owner_funds, quality=quality, taker_gets=taker_gets
        )
        if owner_funds is not None
        else (None, None)
    )
    return NormalizedOffer(
        diff_type=diff_type,
        identifiers=_derive_identifiers(offer=offer, diff_type=diff_type),
        Account=_derive_field(node=offer, field_name="Account"),
        BookDirectory=_derive_field(node=offer, field_name="BookDirectory"),
        Flags=_derive_field(node=offer, field_name="Flags"),
        PreviousTxnID=new_prev_txn_id,
        PreviousTxnLgrSeq=new_prev_txn_lgr_seq,
        Sequence=_derive_field(node=offer, field_name="Sequence"),
        TakerGets=taker_gets,
        TakerPays=taker_pays,
        index=cast(str, offer[diff_type]["LedgerIndex"]),
        quality=quality,
        BookNode=_derive_field(node=offer, field_name="BookNode"),
        OwnerNode=_derive_field(node=offer, field_name="OwnerNode"),
        owner_funds=owner_funds,
        taker_gets_funded=taker_gets_funded,
        taker_pays_funded=taker_pays_funded,
    )


def _normalize_offers(
    transaction: Union[RawTxnType, SubscriptionRawTxnType],
    currency_pair: str,
    to_xrp: bool,
) -> List[NormalizedOffer]:
    """
    Normalizes all offer objects the transaction has affected.

    Args:
        transaction: The raw transaction.
        currency_pair: Currency pair.
        to_xrp: If currency amount should be converted from drops to XRP.

    Returns:
        A list of offer objects in a standard format.
    """
    hash = transaction["hash"]
    ledger_index = transaction["ledger_index"]
    affected_nodes = transaction["meta"]["AffectedNodes"]
    offers = filter_(
        affected_nodes,
        lambda node: node[list(node.keys())[0]]["LedgerEntryType"] == "Offer",
    )
    return [
        _normalize_offer(
            offer=offer,
            new_prev_txn_id=hash,
            new_prev_txn_lgr_seq=ledger_index,
            pair=currency_pair,
            to_xrp=to_xrp,
            owner_funds=transaction["owner_funds"]
            if "owner_funds" in transaction
            else None,
        )
        for offer in offers
    ]


def derive_currency_pair(asks: ORDER_BOOK_SIDE_TYPE, bids: ORDER_BOOK_SIDE_TYPE) -> str:
    """
    Derives the currency pair from an order book.

    Args:
        asks: Ask side of an order book.
        bids: Bid side of an order book.

    Returns:
        The order books currency pair.
    """
    if bids:
        bid = bids[0]
        base = (
            f"{bid['TakerPays']['currency']}.{bid['TakerPays']['issuer']}"
            if (isinstance(bid["TakerPays"], dict))
            else "XRP"
        )
        counter = (
            f"{bid['TakerGets']['currency']}.{bid['TakerGets']['issuer']}"
            if (isinstance(bid["TakerGets"], dict))
            else "XRP"
        )
        return f"{base}/{counter}"
    elif asks:
        ask = asks[0]
        base = (
            f"{ask['TakerGets']['currency']}.{ask['TakerGets']['issuer']}"
            if (isinstance(ask["TakerGets"], dict))
            else "XRP"
        )
        counter = (
            f"{ask['TakerPays']['currency']}.{ask['TakerPays']['issuer']}"
            if (isinstance(ask["TakerPays"], dict))
            else "XRP"
        )
        return f"{base}/{counter}"
    else:
        raise XRPLOrderBookEmptyException(
            "Cannot derive currency pair because order book is empty."
        )


def _derive_offer_status_for_final_order_book(
    offer: NormalizedOffer,
) -> Literal["created", "partially-filled", "filled", "cancelled"]:
    """
    Derive the offers status.

    Returns:
        The offer status.
    """
    if offer.diff_type == "CreatedNode":
        return "created"
    elif offer.diff_type == "ModifiedNode":
        taker_gets_value = Decimal(
            value=offer.TakerGets["value"]
            if isinstance(offer.TakerGets, dict)
            else offer.TakerGets
        )
        if taker_gets_value > 0:
            return "partially-filled"
        else:
            return "filled"
    else:  # DeletedNode
        return "cancelled"


def _prepare_offer(offer: NormalizedOffer) -> Dict[str, Any]:
    """
    Prepares the offer before adding it to the order book.

    Args:
        offer: The offer.

    Returns:
        The offer object as dictionary.
    """
    offer.__delattr__("diff_type")
    offer.__delattr__("identifiers")
    offer = cast(NormalizedOffer, _remove_undefined(order=offer))
    return offer.__dict__


def _parse_final_order_book_side(
    side: ORDER_BOOK_SIDE_TYPE,
    offer: NormalizedOffer,
    status: Literal["created", "partially-filled", "filled", "cancelled"],
) -> Tuple[ORDER_BOOK_SIDE_TYPE, Optional[str]]:
    """
    Parses the new order book side.

    Args:
        side: Ask or Bid
        offer: Normalized offer object.
        status: The offers status.

    Returns:
        The new order book side and the exchange rate if an offer was modified.
    """
    new_exchange_rate = None
    if status == "created":
        side.append(_prepare_offer(offer=offer))
        new_exchange_rate = None
        return side, new_exchange_rate
    if status == "partially-filled":
        assert side  # side must not be empty
        prev_txn_id, prev_txn_lgr_seq = offer.identifiers
        side_copy = side
        for num, side_offer in enumerate(side_copy):
            if (
                side_offer["PreviousTxnID"] == prev_txn_id
                and side_offer["PreviousTxnLgrSeq"] == prev_txn_lgr_seq
            ):
                side[num] = _prepare_offer(offer=offer)
                new_exchange_rate = offer.quality
        return side, new_exchange_rate
    # else cancelled or filled
    prev_txn_id, prev_txn_lgr_seq = offer.identifiers
    side_copy = side
    for num, side_offer in enumerate(side_copy):
        if (
            side_offer["PreviousTxnID"] == prev_txn_id
            and side_offer["PreviousTxnLgrSeq"] == prev_txn_lgr_seq
        ):
            _ = side.pop(num)
    if status == "filled":
        new_exchange_rate = offer.quality
    return side, new_exchange_rate


def _parse_final_order_book(
    asks: ORDER_BOOK_SIDE_TYPE,
    bids: ORDER_BOOK_SIDE_TYPE,
    offer: NormalizedOffer,
    status: Literal["created", "partially-filled", "filled", "cancelled"],
    currency_pair: str,
) -> Tuple[ORDER_BOOK_SIDE_TYPE, ORDER_BOOK_SIDE_TYPE, Optional[str]]:
    """
    Parses the new order book after the transaction affected it.

    Args:
        asks: Ask side.
        bids: Bid side.
        offer: Normalized offer object.
        status: The offers status.
        currency_pair: Currency pair.

    Returns:
        The new order book and the exchange rate if an offer was modified.
    """
    base_currency = (
        f"{offer.TakerPays['currency']}.{offer.TakerPays['issuer']}"
        if (isinstance(offer.TakerPays, dict))
        else "XRP"
    )
    counter_currency = (
        f"{offer.TakerGets['currency']}.{offer.TakerGets['issuer']}"
        if (isinstance(offer.TakerGets, dict))
        else "XRP"
    )
    offer_currency_pair = f"{base_currency}/{counter_currency}"
    new_exchange_rate = None
    if base_currency in currency_pair and counter_currency in currency_pair:
        # if flipped currency pair
        if currency_pair != offer_currency_pair:
            asks, new_exchange_rate = _parse_final_order_book_side(
                side=asks, offer=offer, status=status
            )
        else:  # matching currency pair
            bids, new_exchange_rate = _parse_final_order_book_side(
                side=bids, offer=offer, status=status
            )
        return asks, bids, new_exchange_rate
    # the offer does not affect the given order book
    return asks, bids, new_exchange_rate


def _calculate_spread(
    tip_ask: Dict[str, Union[str, int, CURRENCY_AMOUNT_TYPE]],
    tip_bid: Dict[str, Union[str, int, CURRENCY_AMOUNT_TYPE]],
) -> str:
    """
    Calculates the order books quoted spread.

    Args:
        tip_ask: The cheapest ask offer.
        tip_bid: The most expensive bid offer.

    Returns:
        The spread.
    """
    ask_quality = Decimal(cast(str, tip_ask["quality"]))
    bid_quality = Decimal(cast(str, tip_bid["quality"]))
    price_difference = ask_quality - bid_quality
    midpoint = (ask_quality + bid_quality) / 2
    quoted_spread = (price_difference / midpoint) * 100
    return str(quoted_spread)


def compute_final_order_book(
    asks: ORDER_BOOK_SIDE_TYPE,
    bids: ORDER_BOOK_SIDE_TYPE,
    transaction: Optional[RawTxnType],
    to_xrp: bool,
) -> Tuple[
    ORDER_BOOK_SIDE_TYPE, ORDER_BOOK_SIDE_TYPE, str, Optional[str], Optional[str]
]:
    """
    Compute the new order book.

    Args:
        asks: Ask side.
        bids: Bid side.
        transaction: The raw transaction.
        to_xrp: If currency amount should be converted from drops to XRP.

    Returns:
        The new order book, currency pair, exchange rate and spread.
    """
    pair = derive_currency_pair(asks=asks, bids=bids)
    exchange_rate = None
    quoted_spread = None
    if transaction is not None:
        normalized_offers = _normalize_offers(
            transaction=transaction, currency_pair=pair, to_xrp=to_xrp
        )
        for offer in normalized_offers:
            offer_status = _derive_offer_status_for_final_order_book(offer=offer)
            asks, bids, new_exchange_rate = _parse_final_order_book(
                asks=asks,
                bids=bids,
                offer=offer,
                status=offer_status,
                currency_pair=pair,
            )
            if new_exchange_rate is not None:
                exchange_rate = new_exchange_rate
    for ask in asks:
        if to_xrp:
            ask["TakerGets"] = cast(
                CURRENCY_AMOUNT_TYPE,
                _format_drops_to_xrp(
                    amount=cast(CURRENCY_AMOUNT_TYPE, ask["TakerGets"])
                ),
            )
            ask["TakerPays"] = cast(
                CURRENCY_AMOUNT_TYPE,
                _format_drops_to_xrp(
                    amount=cast(CURRENCY_AMOUNT_TYPE, ask["TakerPays"])
                ),
            )
        ask["quality"] = _derive_quality(
            taker_gets=cast(CURRENCY_AMOUNT_TYPE, ask["TakerGets"]),
            taker_pays=cast(CURRENCY_AMOUNT_TYPE, ask["TakerPays"]),
            pair=pair,
        )
    for bid in bids:
        if to_xrp:
            bid["TakerGets"] = cast(
                CURRENCY_AMOUNT_TYPE,
                _format_drops_to_xrp(
                    amount=cast(CURRENCY_AMOUNT_TYPE, bid["TakerGets"])
                ),
            )
            bid["TakerPays"] = cast(
                CURRENCY_AMOUNT_TYPE,
                _format_drops_to_xrp(
                    amount=cast(CURRENCY_AMOUNT_TYPE, bid["TakerPays"])
                ),
            )
        bid["quality"] = _derive_quality(
            taker_gets=cast(CURRENCY_AMOUNT_TYPE, bid["TakerGets"]),
            taker_pays=cast(CURRENCY_AMOUNT_TYPE, bid["TakerPays"]),
            pair=pair,
        )
    sorted_asks = list(
        sorted(asks, key=lambda ask: Decimal(cast(str, ask["quality"])), reverse=False)
    )
    sorted_bids = list(
        sorted(bids, key=lambda bid: Decimal(cast(str, bid["quality"])), reverse=True)
    )
    if sorted_asks and sorted_bids:
        quoted_spread = _calculate_spread(
            tip_ask=sorted_asks[0], tip_bid=sorted_bids[0]
        )
    return (sorted_asks, sorted_bids, pair, exchange_rate, quoted_spread)
