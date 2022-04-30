from __future__ import annotations

from decimal import Decimal
from unittest import TestCase

from xrpl_trading_bot.txn_parser import parse_final_order_book

ASKS = [
    {
        "Account": "rfEVtF3h7j9uGGvCW7Cma465dwoqyJW1kG",
        "BookDirectory": "79C54A4EBD69AB2EADCE313042F36092BE432423CC6A4F784E160833"
        "16697A00",
        "BookNode": "0",
        "Flags": 0,
        "LedgerEntryType": "Offer",
        "OwnerNode": "0",
        "PreviousTxnID": "BF80AB94ECE325F5BF99230297942DD05A348EB08FFBB1C1309EDEF3"
        "8429EF83",
        "PreviousTxnLgrSeq": 71316518,
        "Sequence": 2880874,
        "TakerGets": "1380000000",
        "TakerPays": {
            "currency": "USD",
            "issuer": "rhub8VRN55s94qWKDv6jmDy1pUykJzF3wq",
            "value": "855.80217",
        },
        "index": "CFF4CFB39DD62FFCF45E89AEBB128BC78C0D51D7969955D467A42DCBF0E9BF15",
        "owner_funds": "12925147440",
        "quality": "0.0000006201465",
    }
]

BIDS = [
    {
        "Account": "rUerwiGtq3Et6dUQJpEw4BJ6hH5vzdPtfN",
        "BookDirectory": "F0B9A528CE25FE77C51C38040A7FEC016C2C841E7"
        "4C1418D5B06D5073CE0313B",
        "BookNode": "0",
        "Flags": 0,
        "LedgerEntryType": "Offer",
        "OwnerNode": "0",
        "PreviousTxnID": "6B2074B898774F568F10913507CBABDBA0709A1BE"
        "65077AC3615051AE857D56A",
        "PreviousTxnLgrSeq": 69179487,
        "Sequence": 62,
        "TakerGets": {
            "currency": "USD",
            "issuer": "rhub8VRN55s94qWKDv6jmDy1pUykJzF3wq",
            "value": "520",
        },
        "TakerPays": "1000000000",
        "index": "2269FFC617DAAA154A261661811BE1C645BB38B8B6B3BC9739" "1F63BA0B1E393A",
        "quality": "1923076.923076923",
    }
]

TXN = {
    "engine_result": "tesSUCCESS",
    "engine_result_code": 0,
    "engine_result_message": "The transaction was applied. Only final in a validated"
    "ledger.",
    "ledger_hash": "4F0592540DD18A124D62707D9A2A7931E3B41C720136B81E36CD494205CA20DB",
    "ledger_index": 71316521,
    "meta": {
        "AffectedNodes": [
            {
                "ModifiedNode": {
                    "FinalFields": {
                        "Flags": 0,
                        "IndexNext": "0",
                        "IndexPrevious": "0",
                        "Owner": "r3Vh9ZmQxd3C5CPEB8q7VbRuMPxwuC634n",
                        "RootIndex": "12F72282F74D437C2E76C4E57710E63779A1825D5A2090"
                        "FF894FB9A22AF40AAE",
                    },
                    "LedgerEntryType": "DirectoryNode",
                    "LedgerIndex": "12F72282F74D437C2E76C4E57710E63779A1825D5A2090F"
                    "F894FB9A22AF40AAE",
                }
            },
            {
                "DeletedNode": {
                    "FinalFields": {
                        "Account": "r3Vh9ZmQxd3C5CPEB8q7VbRuMPxwuC634n",
                        "BookDirectory": "79C54A4EBD69AB2EADCE313042F36092BE432423CC6A"
                        "4F784E16A492D302F000",
                        "BookNode": "0",
                        "Flags": 0,
                        "OwnerNode": "0",
                        "PreviousTxnID": "B88A99585EECCF76BC7E68D101E42F63EE01DF00832E"
                        "A3B705A21232BD17CD90",
                        "PreviousTxnLgrSeq": 71316519,
                        "Sequence": 74738539,
                        "TakerGets": "53860000000",
                        "TakerPays": {
                            "currency": "USD",
                            "issuer": "rhub8VRN55s94qWKDv6jmDy1pUykJzF3wq",
                            "value": "34327.1324",
                        },
                    },
                    "LedgerEntryType": "Offer",
                    "LedgerIndex": "3AD9D4189FA00C22E7F80A99CBC417FE59F3A19924D1D0C"
                    "50D75AC2D597F18E9",
                }
            },
            {
                "DeletedNode": {
                    "FinalFields": {
                        "ExchangeRate": "4e16a492d302f000",
                        "Flags": 0,
                        "RootIndex": "79C54A4EBD69AB2EADCE313042F36092BE432423CC6A4F784"
                        "E16A492D302F000",
                        "TakerGetsCurrency": "0000000000000000000000000000000000000000",
                        "TakerGetsIssuer": "0000000000000000000000000000000000000000",
                        "TakerPaysCurrency": "0000000000000000000000005553440000000000",
                        "TakerPaysIssuer": "2ADB0B3959D60A6E6991F729E1918B7163925230",
                    },
                    "LedgerEntryType": "DirectoryNode",
                    "LedgerIndex": "79C54A4EBD69AB2EADCE313042F36092BE432423CC6A4F784E1"
                    "6A492D302F000",
                }
            },
            {
                "CreatedNode": {
                    "LedgerEntryType": "DirectoryNode",
                    "LedgerIndex": "79C54A4EBD69AB2EADCE313042F36092BE432423CC6A4F784E1"
                    "6A57BA7A80000",
                    "NewFields": {
                        "ExchangeRate": "4e16a57ba7a80000",
                        "RootIndex": "79C54A4EBD69AB2EADCE313042F36092BE432423CC6A4F784"
                        "E16A57BA7A80000",
                        "TakerPaysCurrency": "0000000000000000000000005553440000000000",
                        "TakerPaysIssuer": "2ADB0B3959D60A6E6991F729E1918B7163925230",
                    },
                }
            },
            {
                "CreatedNode": {
                    "LedgerEntryType": "Offer",
                    "LedgerIndex": "C7E3B90B3731C182906181FB77C51A9CEA181E0401D39C5B140"
                    "9F85259B6E3BB",
                    "NewFields": {
                        "Account": "r3Vh9ZmQxd3C5CPEB8q7VbRuMPxwuC634n",
                        "BookDirectory": "79C54A4EBD69AB2EADCE313042F36092BE432423CC6A4"
                        "F7"
                        "84E16A57BA7A80000",
                        "Sequence": 74738545,
                        "TakerGets": "53860000000",
                        "TakerPays": {
                            "currency": "USD",
                            "issuer": "rhub8VRN55s94qWKDv6jmDy1pUykJzF3wq",
                            "value": "34332.5184",
                        },
                    },
                }
            },
            {
                "ModifiedNode": {
                    "FinalFields": {
                        "Account": "r3Vh9ZmQxd3C5CPEB8q7VbRuMPxwuC634n",
                        "Balance": "53960109325",
                        "Flags": 0,
                        "OwnerCount": 10,
                        "Sequence": 74738546,
                    },
                    "LedgerEntryType": "AccountRoot",
                    "LedgerIndex": "F709D77D5D72E0C96CB029FCE21F3AF34E70ED0D8DB121B2CF"
                    "961E64E582EEF2",
                    "PreviousFields": {"Balance": "53960109345", "Sequence": 74738545},
                    "PreviousTxnID": "215C924AC990E5807A9B0C208FCE8FFFFA62AD74F476C56B2"
                    "DA89A472D69AF91",
                    "PreviousTxnLgrSeq": 71316521,
                }
            },
        ],
        "TransactionIndex": 32,
        "TransactionResult": "tesSUCCESS",
    },
    "status": "closed",
    "transaction": {
        "Account": "r3Vh9ZmQxd3C5CPEB8q7VbRuMPxwuC634n",
        "Fee": "20",
        "Flags": 0,
        "LastLedgerSequence": 71316523,
        "OfferSequence": 74738539,
        "Sequence": 74738545,
        "SigningPubKey": "03C71E57783E0651DFF647132172980B1F598334255F01DD447184B5D66"
        "501E67A",
        "TakerGets": "53860000000",
        "TakerPays": {
            "currency": "USD",
            "issuer": "rhub8VRN55s94qWKDv6jmDy1pUykJzF3wq",
            "value": "34332.5184",
        },
        "TransactionType": "OfferCreate",
        "TxnSignature": "3045022100CC71849462CB1D4C0260EF42D9EA813244F21A2F50"
        "1E5FFA1FD2A85F53E582BC02200617F89D059A21DDF8889A3CFF6D76EB7D57573BF4"
        "4B3EA5B10A679646376BCF",
        "date": 704557641,
        "hash": "7FAB18A8E29BDB4D0669D8F91A0A614BC1DB1CB9FB5A6E1ADAAF39E2B1843457",
        "owner_funds": "53930109305",
    },
    "type": "transaction",
    "validated": True,
}


class TestFinalOrderBookParser(TestCase):
    def test_add_offer(self: TestFinalOrderBookParser):
        actual = parse_final_order_book(
            asks=ASKS, bids=BIDS, transaction=TXN, to_xrp=True
        )
        expected = {
            "asks": [
                {
                    "Account": "rfEVtF3h7j9uGGvCW7Cma465dwoqyJW1kG",
                    "BookDirectory": "79C54A4EBD69AB2EADCE313042F36092BE432423CC6"
                    "A4F784E16083316697A00",
                    "BookNode": "0",
                    "Flags": 0,
                    "LedgerEntryType": "Offer",
                    "OwnerNode": "0",
                    "PreviousTxnID": "BF80AB94ECE325F5BF99230297942DD05A348EB08FF"
                    "BB1C1309EDEF38429EF83",
                    "PreviousTxnLgrSeq": 71316518,
                    "Sequence": 2880874,
                    "TakerGets": "1380.000000",
                    "TakerPays": {
                        "currency": "USD",
                        "issuer": "rhub8VRN55s94qWKDv6jmDy1pUykJzF3wq",
                        "value": "855.80217",
                    },
                    "index": "CFF4CFB39DD62FFCF45E89AEBB128BC78C0D51D7969955D467A42"
                    "DCBF0E9BF15",
                    "owner_funds": "12925147440",
                    "quality": "0.620146500000",
                },
                {
                    "Account": "r3Vh9ZmQxd3C5CPEB8q7VbRuMPxwuC634n",
                    "BookDirectory": "79C54A4EBD69AB2EADCE313042F36092BE432423CC6A4F"
                    "784E16A57BA7A80000",
                    "BookNode": "0",
                    "Flags": "0",
                    "OwnerNode": "0",
                    "PreviousTxnID": "7FAB18A8E29BDB4D0669D8F91A0A614BC1DB1CB9FB5A"
                    "6E1ADAAF39E2B1843457",
                    "PreviousTxnLgrSeq": 71316521,
                    "Sequence": 74738545,
                    "TakerGets": "53860.000000",
                    "TakerPays": {
                        "currency": "USD",
                        "issuer": "rhub8VRN55s94qWKDv6jmDy1pUykJzF3wq",
                        "value": "34332.5184",
                    },
                    "index": "C7E3B90B3731C182906181FB77C51A9CEA181E0401D39C5B1409F85"
                    "259B6E3BB",
                    "quality": "0.637440000000",
                    "LedgerEntryType": "Offer",
                    "owner_funds": "53930.109305",
                },
            ],
            "bids": [
                {
                    "Account": "rUerwiGtq3Et6dUQJpEw4BJ6hH5vzdPtfN",
                    "BookDirectory": "F0B9A528CE25FE77C51C38040A7FEC016C2C841E74C1418D"
                    "5B06D5073CE0313B",
                    "BookNode": "0",
                    "Flags": 0,
                    "LedgerEntryType": "Offer",
                    "OwnerNode": "0",
                    "PreviousTxnID": "6B2074B898774F568F10913507CBABDBA0709A1BE65077AC"
                    "3615051AE857D56A",
                    "PreviousTxnLgrSeq": 69179487,
                    "Sequence": 62,
                    "TakerGets": {
                        "currency": "USD",
                        "issuer": "rhub8VRN55s94qWKDv6jmDy1pUykJzF3wq",
                        "value": "520",
                    },
                    "TakerPays": "1000.000000",
                    "index": "2269FFC617DAAA154A261661811BE1C645BB38B8B6B3BC97391F63BA"
                    "0B1E393A",
                    "quality": "0.52",
                }
            ],
            "currency_pair": "XRP/USD.rhub8VRN55s94qWKDv6jmDy1pUykJzF3wq",
            "exchange_rate": None,
            "spread": Decimal("17.56730385086477921916174807"),
        }
        self.assertEqual(first=actual, second=expected)
