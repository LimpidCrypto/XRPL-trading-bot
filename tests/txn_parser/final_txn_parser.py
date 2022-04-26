from xrpl_trading_bot.txn_parser.order_book_changes import parse_final_order_book

from xrpl.clients import WebsocketClient
from xrpl.models import Subscribe, IssuedCurrency, XRP
from xrpl.models.requests.subscribe import SubscribeBook


asks = []
bids = []

with WebsocketClient(url="wss://xrplcluster.com/") as client:
    client.send(
        Subscribe(
            books=[
                SubscribeBook(
                    taker_gets=IssuedCurrency(
                        currency="USD",
                        issuer="rhub8VRN55s94qWKDv6jmDy1pUykJzF3wq"
                    ),
                    taker_pays=XRP(),
                    taker="rPu2feBaViWGmWJhvaF5yLocTVD8FUxd2A",
                    both=True,
                    snapshot=True
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
            asks, bids = parse_final_order_book(
                asks=asks,
                bids=bids,
                transaction=message,
                to_xrp=True
            )
            print(f"""
{bids[0]['quality']}          {asks[0]['quality']}
{bids[1]['quality']}          {asks[1]['quality']}
{bids[2]['quality']}          {asks[2]['quality']}
{bids[3]['quality']}          {asks[3]['quality']}
{bids[4]['quality']}          {asks[4]['quality']}
{bids[5]['quality']}          {asks[5]['quality']}
{bids[6]['quality']}          {asks[6]['quality']}
{bids[7]['quality']}          {asks[7]['quality']}
{bids[8]['quality']}          {asks[8]['quality']}
{bids[9]['quality']}          {asks[9]['quality']}
""")
