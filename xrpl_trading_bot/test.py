from threading import Thread
from xrpl.models import IssuedCurrencyAmount, PathFindSubcommand, PathFind
from xrpl.clients import WebsocketClient


def sub():
    with WebsocketClient("wss://xrplcluster.com/") as client:
        req = PathFind(
            subcommand=PathFindSubcommand.CREATE,
            source_account="rPu2feBaViWGmWJhvaF5yLocTVD8FUxd2A",
            destination_account="rPu2feBaViWGmWJhvaF5yLocTVD8FUxd2A",
            destination_amount="-1"
        )
        req2 = PathFind(
            subcommand=PathFindSubcommand.CREATE,
            source_account="rPu2feBaViWGmWJhvaF5yLocTVD8FUxd2A",
            destination_account="rPu2feBaViWGmWJhvaF5yLocTVD8FUxd2A",
            destination_amount=IssuedCurrencyAmount(
                currency="USD",
                issuer="rvYAfWj5gh67oV6fW32ZzP3Aw4Eubs59B",
                value=-1
            )
        )
        client.send(req)
        client.send(req2)
        for message in client:
            print(message)


t = Thread(target=sub)
t.start()
t.join()
