# Warning 🚨
This repository is in active development and is not working yet. The bot currently requires you to put in your seed value via terminal.
It is planned to use the Tangem wallet in the future so you will never be required to give away your secrets. At the current stage I would never use a bot like this, even if it should work! 
```diff
- NEVER GIVE AWAY YOUR SECRETS!!!
```

# XRPL-trading-bot
A trading bot that uses the decentralized exchange of the XRP Ledger. It uses arbitrage trading and market making to make profit.

## 📖 Basics:
- The XRP Ledger has the world's first [`decentralized exchange`](https://xrpl.org/decentralized-exchange.html#decentralized-exchange) (`DEX`).
- Orders on the `DEX` are called [`Offers`](https://xrpl.org/offers.html#offers).
- This bot only sends [`OfferCreate` transactions](https://xrpl.org/offercreate.html) with the [Immediate or cancel](https://xrpl.org/offercreate.html#offercreate-flags) flag to the ledger.
- `Offers` consume other `Offers` in an [order book](https://en.wikipedia.org/wiki/Order_book). For example if you want to buy a currency you place a `bid Offer` that consumes an `ask Offer` that has the same or a better price than the `bid Offer`.
- Arbitrage trading and market making are not known to make huge profits. There are known to make profits with low risk.

## 📈 Trading types:

### 💱 Arbitrage Trading
The arbitrage trading bot takes advantage of the price differences in different liquid order books to make profit.
##### Types
| [Basic Spatial Arbitrage](https://en.wikipedia.org/wiki/Arbitrage#Spatial_arbitrage)       | [Triangular Arbitrage](https://en.wikipedia.org/wiki/Triangular_arbitrage)          |
| ----------------------------- | ----------------------------- |
| 1. Order: USD.*r1* > BTC.*r1* | 1. Order: USD.*r1* > BTC.*r1* |
| 2. Order: BTC.*r2* > USD.*r2* | 2. Order: BTC.*r2* > ETH.*r1* |
|                               | 3. Order: ETH.*r2* > USD.*r2* |
##### Example
The bot places an immediate or cancel offer that trades 10 USD.r1 for 9 EUR.r1. The bot then places a second immediate or cancel offer that trades 9 EUR.r2 for 11 USD.r2. The profit for this trade is 1 USD. Neither the `TakerGets` nor the `TakerPays` issuers have to be the same for both trades. All four issuers can be completely different. Doing so brings the most flexibility.
<br>The bot only trades liquid order books and adjusts all `Offer` values from the lowest `TakerGets` balance.

### 🌊 [Market Maker](https://en.wikipedia.org/wiki/Market_maker)
Market makers provide liquidity to a market. Place a buy and a sell order on the tip of a illiquid order book. The spread the two orders has to be big enough to cover the potential [transfer fees](https://xrpl.org/transfer-fees.html#transfer-fees). The market maker bot only trades illiquid order books, where %[^1] of the orders have been consumed in the last 2 weeks.
##### Example:
The order books most expensive bid order has a price of 50 $ and the cheapest ask order price is 52 $, so the spread is 3.85 %[^2].
<br>The bot then calculates what prices it needs to place the orders at to cover the transfer fees and still be profitable while minimize the current spread of 3.85 %. It aims to provide a spread of 0.5 %. If one or both orders are not fulfilled after a week the orders will get canceled automatically.

[^1]: not determined yet
[^2]: [quoted spread](https://en.wikipedia.org/wiki/Bid%E2%80%93ask_spread#Quoted_spread) = (52 $ - 50 $) / 51 $ * 100    ((ask - bid) / midpoint * 100)
