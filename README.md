# XRPL-trading-bot
A trading bot that uses the decentralized exchange of the XRP Ledger.

## Basics:
soon

## Trading types:

### Arbitrage Trading
The arbitrage trading bot takes advantage of the price differences in different liquid order books to make profit.
##### Example
| Basic Spatial Arbitrage      | Triangular Arbitrage         |
| ---------------------------- | ---------------------------- |
| 1. Step: USD.*r1* > BTC.*r1* | 1. Step: USD.*r1* > BTC.*r1* |
| 2. Step: BTC.*r2* > USD.*r2* | 2. Step: BTC.*r2* > ETH.*r1* |
|                              | 3. Step: ETH.*r2* > USD.*r2* |

### Market Maker
Place a buy and a sell order on the tip of a illiquid order book. The spread the two orders has to be big enough to cover the potential [transfer fees](https://xrpl.org/transfer-fees.html#transfer-fees). The market maker bot only trades illiquid order books, where %[^2] of the orders have been consumed in the last 2 weeks.
##### Example:
The order books most expensive bid order has a price of 50 $ and the cheapest ask order price is 52 $, so the spread is 3.85 %[^1].
<br>The bot then calculates what prices it needs to place the orders at to cover the transfer fees and still be profitable while minimize the current spread of 3.85 %. It aims to provide a spread of 0.5 %. If one or both orders are not fulfilled after a week the orders will get canceled automatically.

[^1]: (52 $ - 50 $) / 52 $ * 100
[^2]: not determined yet
