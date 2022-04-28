from decimal import Decimal

from xrpl.clients import WebsocketClient
from xrpl.models import XRP, IssuedCurrency, Subscribe
from xrpl.models.requests.subscribe import SubscribeBook

from xrpl_trading_bot.txn_parser.order_book_changes import parse_final_order_book

asks = []
bids = []

exchange_rate = None

with WebsocketClient(url="wss://xrplcluster.com/") as client:
    client.send(
        Subscribe(
            books=[
                SubscribeBook(
                    taker_gets=IssuedCurrency(
                        currency="USD", issuer="rvYAfWj5gh67oV6fW32ZzP3Aw4Eubs59B"
                    ),
                    taker_pays=XRP(),
                    taker="rPu2feBaViWGmWJhvaF5yLocTVD8FUxd2A",
                    both=True,
                    snapshot=True,
                )
            ]
        )
    )
    for num, message in enumerate(client):
        if num == 0:
            result = message["result"]
            asks = result["asks"]
            bids = result["bids"]
        else:
            final_order_book = parse_final_order_book(
                asks=asks, bids=bids, transaction=message, to_xrp=True
            )
            asks = final_order_book["asks"]
            bids = final_order_book["bids"]
            ex_rate = final_order_book["exchange_rate"]
            spread = Decimal(final_order_book["spread"])
            print("Bids          Asks")
            for num in range(10):
                print(
                    "{:.4}".format(Decimal(bids[num]["quality"])),
                    "      ",
                    "{:.4}".format(Decimal(asks[num]["quality"])),
                )
            if ex_rate is not None:
                exchange_rate = ex_rate
            print("Rate:", exchange_rate)
            print("Spread:", "{:.6}".format(spread))
