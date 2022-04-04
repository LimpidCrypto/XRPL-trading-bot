from __future__ import annotations

from asyncio import gather
from typing import List

from xrpl.asyncio.clients import AsyncWebsocketClient
from xrpl.models.requests import Request
from xrpl.models.response import Response


async def xrp_request_async(
    requests: List[Request],
    uri: str = "wss://limpidcrypto.de:6005/",
) -> List[Response]:
    """Call mutiple request async.

    Args:
        uri (str): Websocket uri.
        requests (List[Request]): List of requests.

    Returns:
        List[Response]: List of results.

    Example::
        results = asyncio.run(
            xrp_request_async(
                uri="wss://limpidcrypto.de:6005/",
                requests=[
                    Ledger(ledger_index="validated"), Ledger(ledger_index="current")]
            )
        )
        print(results)
    """
    async with AsyncWebsocketClient(url=uri) as client:
        requests_for_gather = [client.request(request) for request in requests]
        responses = await gather(*requests_for_gather)

        return list(responses)
