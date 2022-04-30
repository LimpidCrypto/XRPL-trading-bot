from __future__ import annotations

from asyncio import run
from unittest import TestCase

from xrpl.models import Ledger

from xrpl_trading_bot.clients import xrp_request_async


class TestXRPClientAsync(TestCase):
    def test(self: TestXRPClientAsync):
        self.assertTrue(
            run(xrp_request_async(requests=[Ledger(ledger_index="validated")]))
        )
