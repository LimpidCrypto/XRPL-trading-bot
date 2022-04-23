# XRPL-trading-bot
A trading bot that uses the decentralized exchange of the XRP Ledger.

## Basics:
- The XRP Ledger has the world's first [`decentralized exchange`](https://xrpl.org/decentralized-exchange.html#decentralized-exchange) (`DEX`).
- Orders on the `DEX` are called [`Offers`](https://xrpl.org/offers.html#offers).
- This bot only sends [`OfferCreate` transactions](https://xrpl.org/offercreate.html) with the [Immediate or cancel](https://xrpl.org/offercreate.html#offercreate-flags) flag to the ledger.
- `Offers` consume other `Offers` in an [order book](https://en.wikipedia.org/wiki/Order_book). For example if you want to buy a currency you place a `bid Offer` that consumes an `ask Offer` that has the same or a better price than the `bid Offer`.

## Trading types:

### Arbitrage Trading
The arbitrage trading bot takes advantage of the price differences in different liquid order books to make profit.
##### Example
| Basic Spatial Arbitrage       | Triangular Arbitrage          |
| ----------------------------- | ----------------------------- |
| 1. Order: USD.*r1* > BTC.*r1* | 1. Order: USD.*r1* > BTC.*r1* |
| 2. Order: BTC.*r2* > USD.*r2* | 2. Order: BTC.*r2* > ETH.*r1* |
|                               | 3. Order: ETH.*r2* > USD.*r2* |

### Market Maker
Place a buy and a sell order on the tip of a illiquid order book. The spread the two orders has to be big enough to cover the potential [transfer fees](https://xrpl.org/transfer-fees.html#transfer-fees). The market maker bot only trades illiquid order books, where %[^2] of the orders have been consumed in the last 2 weeks.
##### Example:
The order books most expensive bid order has a price of 50 $ and the cheapest ask order price is 52 $, so the spread is 3.85 %[^1].
<br>The bot then calculates what prices it needs to place the orders at to cover the transfer fees and still be profitable while minimize the current spread of 3.85 %. It aims to provide a spread of 0.5 %. If one or both orders are not fulfilled after a week the orders will get canceled automatically.

[^1]: (52 $ - 50 $) / 52 $ * 100
[^2]: not determined yet
