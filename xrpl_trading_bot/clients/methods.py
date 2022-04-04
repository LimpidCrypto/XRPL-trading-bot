from asyncio import run
from typing import Any, Dict, List

from xrpl.clients import WebsocketClient
from xrpl.models import AccountInfo, AccountLines, Subscribe
from xrpl.models.requests.subscribe import SubscribeBook
from xrpl.utils import drops_to_xrp

from xrpl_trading_bot.clients.main import xrp_request_async
from xrpl_trading_bot.clients.websocket_uri import FullHistoryNodes, NonFullHistoryNodes
from xrpl_trading_bot.wallet.main import XRPWallet


def get_current_account_balances(wallet: XRPWallet) -> None:
    """Get all currency balances the given account holds in a standard format.

    Args:
        account (str): The accounts address.
    """
    account_info, account_lines = run(
        xrp_request_async(
            requests=[
                AccountInfo(account=wallet.classic_address),
                AccountLines(account=wallet.classic_address),
            ]
        )
    )

    xrp_amount = {
        "XRP": str(drops_to_xrp(account_info.result["account_data"]["Balance"]))
    }

    token_amounts = {
        f"{token['currency']}.{token['account']}": token["balance"]
        for token in account_lines.result["lines"]
    }

    account_balances: Dict[str, str] = {}
    account_balances.update(xrp_amount)
    account_balances.update(token_amounts)

    wallet.balances = account_balances


def subscribe_to_account_balances(wallet: XRPWallet) -> None:
    """Receive the accounts balances once then subscribe to the account.
    The subscribtion receives transaction metadata everytime a transaction
    affects the account. It then parses the final balances and adjusts the
    balances of the wallet.

    Args:
        wallet (XRPWallet): The wallet.
    """
    get_current_account_balances(wallet=wallet)

    with WebsocketClient(url=NonFullHistoryNodes.LIMPIDCRYPTO) as client:
        client.send(Subscribe(accounts=[wallet.classic_address]))

        for message in client:
            _ = message  # only a placeholder


def subscribe_to_order_books(
    all_order_books: Any,  # future 'AllOrderBooks' class
    subscribe_books: List[SubscribeBook],
) -> None:
    """Receive all snapshots once and then receive all transactions
    that affected one order book and parse the new order books.

    Args:
        all_order_books:
            All order books.
        subscribe_books (List[SubscribeBook]):
            Max. 10 subscribe books.
    """
    with WebsocketClient(url=FullHistoryNodes.XRPLF) as client:
        client.send(Subscribe(books=subscribe_books))

        for message in client:
            # This client should only receive a snapshot
            # of all 'subscribe_books' and then close.
            _ = message  # only a placeholder

    with WebsocketClient(url=NonFullHistoryNodes.LIMPIDCRYPTO) as client:
        client.send(Subscribe(books=subscribe_books))

        for message in client:
            # This client should receive every transaction without snapshot.
            _ = message  # only a placeholder
