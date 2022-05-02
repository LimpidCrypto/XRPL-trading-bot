"""Parse the trading paths for spatial arbitrage."""

from __future__ import annotations
from decimal import Decimal

from typing import List

from xrpl_trading_bot.order_books import OrderBook
from xrpl_trading_bot.txn_parser.utils.types import CURRENCY_AMOUNT_TYPE
from xrpl_trading_bot.wallet import XRPWallet


def parse_currency_amount(currency_amount: CURRENCY_AMOUNT_TYPE, value: Decimal):
    if isinstance(currency_amount, dict):
        currency_amount["value"] = str(value)
    else:
        currency_amount = str(value)
    return currency_amount


def build_path(
    first_step_offer,
    second_step_offer,
    first_step_counter: str,
    second_step_counter: str,
    wallet: XRPWallet
):
    first_step_taker_gets = first_step_offer["TakerPays"]
    first_step_taker_pays = first_step_offer["TakerGets"]
    second_step_taker_gets = second_step_offer["TakerPays"]
    second_step_taker_pays = second_step_offer["TakerGets"]
    first_step_taker_gets_balance = Decimal(
        wallet.balances[first_step_counter]
    )
    second_step_taker_gets_balance = Decimal(
        wallet.balances[second_step_counter]
    )
    first_step_quality = Decimal(
        first_step_offer["quality"]
    )
    second_step_quality = Decimal(
        second_step_offer["quality"]
    )
    # adjust values
    if first_step_taker_gets_balance <= second_step_taker_gets_balance:
        # adjust all values based of `first_step_taker_gets_balance`
        first_step_taker_gets_value = first_step_taker_gets_balance
        first_step_taker_pays_value = (
            first_step_taker_gets_value / first_step_quality * 0.999
        )
        second_step_taker_gets_value = first_step_taker_pays_value
        second_step_taker_pays_value = (
            second_step_taker_gets_value / second_step_quality * 0.999
        )
    else:
        # adjust all values based of `second_step_taker_gets_balance`
        second_step_taker_gets_value = second_step_taker_gets_balance
        second_step_taker_pays_value = (
            second_step_taker_gets_value / second_step_quality * 0.999
        )
        first_step_taker_pays_value = (
            second_step_taker_gets_value * 0.999
        )
        first_step_taker_gets_value = (
            first_step_taker_pays_value * first_step_taker_pays_value
        )
    first_step_taker_gets = parse_currency_amount(
        currency_amount=first_step_taker_gets,
        value=first_step_taker_gets_value
    )
    first_step_taker_pays = parse_currency_amount(
        currency_amount=first_step_taker_pays,
        value=first_step_taker_pays_value
    )
    second_step_taker_gets = parse_currency_amount(
        currency_amount=second_step_taker_gets,
        value=second_step_taker_gets_value
    )
    second_step_taker_pays = parse_currency_amount(
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
    paths = set()
    for first_path_step_order_book in liquid_order_books:
        for second_path_step_order_book in liquid_order_books:
            if (
                first_path_step_order_book.currency_pair
                != second_path_step_order_book.currency_pair
            ):
                # derive all parts from currency pair
                first_step_base, first_step_counter = (
                    first_path_step_order_book.currency_pair.split("/")
                )
                first_step_base_currency, first_step_base_issuer = (
                    first_step_base.split(".")
                )
                first_step_counter_currency, first_step_counter_issuer = (
                    first_step_counter.split(".")
                )
                second_step_base, second_step_counter = (
                    second_path_step_order_book.currency_pair.split("/")
                )
                second_step_base_currency, second_step_base_issuer = (
                    second_step_base.split(".")
                )
                second_step_counter_currency, second_step_counter_issuer = (
                    second_step_counter.split(".")
                )
                if (
                    first_step_counter_currency == second_step_base_currency
                    and first_step_base_currency == second_step_counter_currency
                ):
                    # Example: EUR/USD and USD/EUR
                    # two buy offers
                    # two ask offers need to be consumed
                    first_step_offer = first_path_step_order_book.asks[0]
                    second_step_offer = second_path_step_order_book.asks[0]
                    paths.add(
                        build_path(
                            first_step_offer=first_step_offer,
                            second_step_offer=second_step_offer,
                            first_step_counter=first_step_counter,
                            second_step_counter=second_step_counter,
                            wallet=wallet
                        )
                    )
                    # Example: USD/EUR  EUR/USD
                    # two sell offers
                    # two bid offers need to be consumed
                    first_step_offer = first_path_step_order_book.bids[0]
                    second_step_offer = second_path_step_order_book.bids[0]
                    paths.add(
                        build_path(
                            first_step_offer=first_step_offer,
                            second_step_offer=second_step_offer,
                            first_step_counter=first_step_counter,
                            second_step_counter=second_step_counter,
                            wallet=wallet
                        )
                    )
                elif (
                    first_step_counter_currency == second_step_counter_currency
                    and first_step_base_currency == second_step_base_currency
                ):
                    # Example: EUR/USD  EUR/USD
                    # first one buy and second one sell offer
                    # one ask and one bid offer need to be consumed
                    first_step_offer = first_path_step_order_book.asks[0]
                    second_step_offer = second_path_step_order_book.bids[0]
                    paths.add(
                        build_path(
                            first_step_offer=first_step_offer,
                            second_step_offer=second_step_offer,
                            first_step_counter=first_step_counter,
                            second_step_counter=second_step_counter,
                            wallet=wallet
                        )
                    )
                    # Example: USD/EUR  USD/EUR
                    # first one sell and second one buy offer
                    # one ask and one bid offer need to be consumed
                    first_step_offer = first_path_step_order_book.bids[0]
                    second_step_offer = second_path_step_order_book.asks[0]
                    paths.add(
                        build_path(
                            first_step_offer=first_step_offer,
                            second_step_offer=second_step_offer,
                            first_step_counter=first_step_counter,
                            second_step_counter=second_step_counter,
                            wallet=wallet
                        )
                    )
                else:
                    pass
            else:
                pass
