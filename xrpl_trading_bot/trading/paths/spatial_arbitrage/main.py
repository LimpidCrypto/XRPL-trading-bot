"""Parse the trading paths for spatial arbitrage."""

from __future__ import annotations
from decimal import Decimal
from itertools import combinations

from typing import List, Literal

from xrpl_trading_bot.order_books import OrderBook
from xrpl_trading_bot.txn_parser.utils.types import CURRENCY_AMOUNT_TYPE
from xrpl_trading_bot.wallet import XRPWallet


def set_currency_amount(currency_amount: CURRENCY_AMOUNT_TYPE, value: Decimal):
    if isinstance(currency_amount, dict):
        currency_amount["value"] = str(value)
    else:
        currency_amount = str(value)
    return currency_amount


def parse_currency_from_currency_amount(currency_amount: CURRENCY_AMOUNT_TYPE) -> str:
    if isinstance(currency_amount, dict):
        return f"{currency_amount['currency']}.{currency_amount['issuer']}"
    else:
        return "XRP"


def adjust_values(
    first_step_offer,
    second_step_offer,
    wallet: XRPWallet,
    to_be_consumed_example_pair: Literal[
        "XRP/USD USD/XRP",
        "USD/XRP XRP/USD",
        "XRP/USD XRP/USD",
        "USD/XRP USD/XRP"
    ]
):
    # to_be_consumed_example_pair is to arbitrage XRP
    first_step_taker_gets = first_step_offer["TakerPays"]
    first_step_taker_pays = first_step_offer["TakerGets"]
    second_step_taker_gets = second_step_offer["TakerPays"]
    second_step_taker_pays = second_step_offer["TakerGets"]
    first_step_quality = Decimal(
        first_step_offer["quality"]
    )
    second_step_quality = Decimal(
        second_step_offer["quality"]
    )
    first_step_taker_gets_balance = Decimal(
        wallet.balances[
            parse_currency_from_currency_amount(
                currency_amount=first_step_taker_gets
            )
        ]
    )
    second_step_taker_gets_balance = Decimal(
        wallet.balances[
            parse_currency_from_currency_amount(
                currency_amount=second_step_taker_gets
            )
        ]
    )
    first_step_taker_gets_value = None
    first_step_taker_pays_value = None
    second_step_taker_gets_value = None
    second_step_taker_pays_value = None
    if to_be_consumed_example_pair == "XRP/USD USD/XRP":
        # two constructed bids
        first_step_direction = "bid"
        second_step_direction = "bid"
    if to_be_consumed_example_pair == "USD/XRP XRP/USD":
        # two constructed asks
        first_step_direction = "ask"
        second_step_direction = "ask"
    if to_be_consumed_example_pair == "XRP/USD XRP/USD":
        # first constructed bid, second constructed ask
        first_step_direction = "bid"
        second_step_direction = "ask"
    if to_be_consumed_example_pair == "USD/XRP USD/XRP":
        # first constructed ask, second constructed bid
        first_step_direction = "ask"
        second_step_direction = "bid"
    first_step_taker_gets_value = first_step_taker_gets_balance
    first_step_taker_pays_value = (
        first_step_taker_gets_value
        * first_step_quality
        * Decimal(0.9999)
    ) if first_step_direction == "bid" else (
        first_step_taker_gets_value
        / first_step_quality
        * Decimal(0.9999)
    )
    second_step_taker_gets_value = first_step_taker_pays_value
    second_step_taker_pays_value = (
        second_step_taker_gets_value
        * second_step_quality
        * Decimal(0.9999)
    ) if second_step_direction == "bid" else (
        second_step_taker_gets_value
        / second_step_quality
        * Decimal(0.9999)
    )
    if second_step_taker_gets_value > second_step_taker_gets_balance:
        second_step_taker_gets_value = second_step_taker_gets_balance
        second_step_taker_pays_value = (
            second_step_taker_gets_value
            * second_step_quality
            * Decimal(0.9999)
        ) if second_step_direction == "bid" else (
            second_step_taker_gets_value
            / second_step_quality
            * Decimal(0.9999)
        )
        first_step_taker_pays_value = second_step_taker_gets_value
        first_step_taker_gets_value = (
            first_step_taker_pays_value
            / first_step_quality
            * Decimal(0.9999)
        ) if first_step_direction == "bid" else (
            first_step_taker_pays_value
            * first_step_quality
            * Decimal(0.9999)
        )
    first_step_taker_gets = set_currency_amount(
        currency_amount=first_step_taker_gets,
        value=first_step_taker_gets_value
    )
    first_step_taker_pays = set_currency_amount(
        currency_amount=first_step_taker_pays,
        value=first_step_taker_pays_value
    )
    second_step_taker_gets = set_currency_amount(
        currency_amount=second_step_taker_gets,
        value=second_step_taker_gets_value
    )
    second_step_taker_pays = set_currency_amount(
        currency_amount=second_step_taker_pays,
        value=second_step_taker_pays_value
    )
    return {
        "first_taker_gets": first_step_taker_gets,
        "first_taker_pays": first_step_taker_pays,
        "second_taker_gets": second_step_taker_gets,
        "second_taker_pays": second_step_taker_pays,
    }


def build_spatial_arbitrage_trading_paths(
    liquid_order_books: List[OrderBook],
    wallet: XRPWallet
):
    paths = []
    possible_paths = combinations(liquid_order_books, 2)
    for path in possible_paths:
        first_path_step_order_book = path[0]
        second_path_step_order_book = path[1]
        if (
            first_path_step_order_book.currency_pair
            != second_path_step_order_book.currency_pair
        ):
            # derive all parts from currency pair
            first_step_base, first_step_counter = (
                first_path_step_order_book.currency_pair.split("/")
            )
            first_step_base_currency = (
                first_step_base.split(".")
            )[0]
            first_step_counter_currency = (
                first_step_counter.split(".")
            )[0]
            second_step_base, second_step_counter = (
                second_path_step_order_book.currency_pair.split("/")
            )
            second_step_base_currency = (
                second_step_base.split(".")
            )[0]
            second_step_counter_currency = (
                second_step_counter.split(".")
            )[0]
            # print(
            #     first_step_base_currency,
            #     first_step_counter_currency,
            #     second_step_base_currency,
            #     second_step_counter_currency,
            # )
            if (
                first_step_counter_currency == second_step_base_currency
                and first_step_base_currency == second_step_counter_currency
            ):
                # This should nerver be the case, but if it somehow
                # still be possible, the trade will be parsed correctly.

                # two ask offers need to be consumed
                # two bid offers need to be constructed based on the two asks
                first_step_offer = first_path_step_order_book.asks[0]
                second_step_offer = second_path_step_order_book.asks[0]
                paths.append(
                    adjust_values(
                        first_step_offer=first_step_offer,
                        second_step_offer=second_step_offer,
                        wallet=wallet,
                        to_be_consumed_example_pair="USD/XRP XRP/USD"
                    )
                )
                # two bid offers need to be consumed
                # two ask offers need to be constructed based on the two bids
                first_step_offer = first_path_step_order_book.bids[0]
                second_step_offer = second_path_step_order_book.bids[0]
                paths.append(
                    adjust_values(
                        first_step_offer=first_step_offer,
                        second_step_offer=second_step_offer,
                        wallet=wallet,
                        to_be_consumed_example_pair="XRP/USD USD/XRP"
                    )
                )
            elif (
                first_step_counter_currency == second_step_counter_currency
                and first_step_base_currency == second_step_base_currency
            ):
                # first one ask and second one bid offer need to be consumed
                # first offer needs to be bid offer constructed
                # based on the ask offer
                # second offer needs to be a ask offer constructed
                # based on the bid offer
                first_step_offer = first_path_step_order_book.asks[0]
                second_step_offer = second_path_step_order_book.bids[0]
                paths.append(
                    adjust_values(
                        first_step_offer=first_step_offer,
                        second_step_offer=second_step_offer,
                        wallet=wallet,
                        to_be_consumed_example_pair="USD/XRP USD/XRP"
                    )
                )
                # first one bid and second one ask offer need to be consumed
                # first offer needs to be a ask offer constructed
                # based on the bid offer
                # second offer needs to be a bid offer constructed
                # based on the ask offer
                first_step_offer = first_path_step_order_book.bids[0]
                second_step_offer = second_path_step_order_book.asks[0]
                paths.append(
                    adjust_values(
                        first_step_offer=first_step_offer,
                        second_step_offer=second_step_offer,
                        wallet=wallet,
                        to_be_consumed_example_pair="XRP/USD XRP/USD"
                    )
                )
            else:
                pass
        else:
            pass

    return tuple(paths)
