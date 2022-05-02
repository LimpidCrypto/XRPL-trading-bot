
# Warning 🚨
**This repository is in active development and is not working yet**. The bot currently requires you to put in your seed value via terminal.
It is planned to use the Tangem wallet in the future so you will never be required to give away your secrets. At the current stage I would never use a bot like this, even if it should work! 
```diff
- NEVER GIVE AWAY YOUR SECRETS!!!
```

## Main tasks:
- [ ] Get it running
  - - [ ] Build trading paths
    - - [ ] Spatial Arbitrage
    - - [ ] Triangular Arbitrage
    - - [ ] Market Maker
  - [ ] Determine which trade would be the most profitable
  - [ ] Build `OfferCreate` transactions
  - [ ] Sign transactions
  - [ ] Submit transactions
- [ ] Add support for Tangem wallet
- [ ] First release

# XRPL-trading-bot
A trading bot that uses the decentralized exchange of the XRP Ledger. It uses arbitrage trading and market making to make profit.

## 📖 Basics:
- The XRP Ledger updates apporx. every 4 seconds.
- The XRP Ledger has the world's first [`decentralized exchange`](https://xrpl.org/decentralized-exchange.html#decentralized-exchange) (`DEX`).
- Orders on the `DEX` are called [`Offers`](https://xrpl.org/offers.html#offers).
- This bot only sends [`OfferCreate` transactions](https://xrpl.org/offercreate.html) with the [Immediate or cancel](https://xrpl.org/offercreate.html#offercreate-flags) flag to the ledger.
- `Offers` consume other `Offers` in an [order book](https://en.wikipedia.org/wiki/Order_book). For example if you want to buy a currency you place a `bid Offer` that consumes an `ask Offer` that has the same or a better price than the `bid Offer`.
- Arbitrage trading and market making are not known to make huge profits. There are known to make profits with low risk.
- The term 'currency' describes both XRP and tokens in this repo.

## How does the bot operate?
#### Example account:
Classic address: raiuHwMbTTKbtjWTj8FrfpTtVk8RgYVxWH
Seed: sn8gyEtTt4ZcKkeiTPA8t36CbqhHu
Balances:
- XRP: 1.000
- USD.Bitstamp = 200
- USD.Gatehub = 150
- EUR.Gatehub = 100
- EUR.Bitstamp = 50

<details><summary>1. Get users seed value</summary>
<p>

In the current version the user must provide his secret seed value via input from the terminal.
Before the first official release the trading bot will be able to interact with the Tangem wallet.
Advantages of using Tangem:
  - The user's key pair is stored safely on the Tangem wallet
  - The user does not have to give away their secret seed value

</p>
</details>
<details><summary>2. Generate wallet</summary>
<p>

Generate the wallet using the [`Wallet`](https://github.com/XRPLF/xrpl-py/blob/master/xrpl/wallet/main.py#L12) object from the [xrpl-py](https://github.com/XRPLF/xrpl-py) library.
By doing so, we are able to access the account's classic address (r-address) and sign transactions.

</p>
</details>
<details><summary>3. Receive the accounts balances once</summary>
<p>

Receive all balances the account holds using the [`account_info`](https://xrpl.org/account_info.html) and the [`account_lines`](https://xrpl.org/account_lines.html#account_lines) methods once. The `account_info` method returns the `Balance` field which contains the accounts XRP values expressed in [drops](https://xrpl.org/xrp.html#xrp-properties). The `account_lines` method returns a list of all [tokens](https://xrpl.org/tokens.html) the account holds. Each object in that list contains the `acccount` field (describes the issuer of the token), the `currency` field (describes the currency code, e.g. 'USD') and the `balance` field (describes the amount the account holds of that token). These balances will be stored in the [`XRPWallet`](https://github.com/LimpidCrypto/XRPL-trading-bot/blob/main/xrpl_trading_bot/wallet/main.py#L10) object which is a child class of the [`Wallet`](https://github.com/XRPLF/xrpl-py/blob/master/xrpl/wallet/main.py#L12) object of the xrpl-py library.

</p>
</details>
<details><summary>4. Subscribe to the accounts transaction stream</summary>
<p>

Receive a message every time a transaction affects the user's account. This message include precise information how the transaction affected the ledger and the account.

</p>
</details>
<details><summary>5. Derive new balances on every new transaction</summary>
<p>

Every time the bot receives a message (described in step 4) that a transaction affected the user's account, the bot makes use of a [transaction parser](https://github.com/XRPLF/xrpl-py/pull/342) (currently added in directly to the bot. The parser will be integrated into the xrpl-py library as soon as possible. When integrated the parser will be deleted from the bot.). The transaction parser parses the accounts final balances after the transaction happend and corrects them in the `XRPWallet` object.

</p>
</details>
<details><summary>6. Parse all possible currency pairs</summary>
<p>

Because we now always know what currencies the account holds, we can parse all possible [currency pairs](https://www.investopedia.com/terms/c/currencypair.asp) the account could trade from them.
If we take the above example account the possible currency pairs would be the following:
- XRP/USD.Bitstamp
- XRP/USD.Gatehub
- XRP/EUR.Gatehub
- XRP/EUR.Bitstamp
- USD.Bitstamp/USD.Gatehub
- USD.Bitstamp/EUR.Gatehub
- USD.Bitstamp/EUR.Bitstamp
- USD.Gatehub/EUR.Gatehub
- USD.Gatehub/EUR.Bitstamp
- EUR.Gatehub/EUR.Bitstamp

</p>
</details>
<details><summary>7. Receive the entire order book for each currency pair once</summary>
<p>

Receive the entire [order book](https://www.investopedia.com/terms/o/order-book.asp) for every currency pair once, using the [`subscribe`](https://xrpl.org/subscribe.html) method. The subscription will immediately be canceled after the order book is received because the bot is retreiving it from a full history node. We do not want to load them unnecessarily. The order books will be stored in the [`OrderBooks`](https://github.com/LimpidCrypto/XRPL-trading-bot/blob/main/xrpl_trading_bot/order_books/main.py#L52) object.

</p>
</details>
<details><summary>8. Subscribe to the transaction stream of each order book</summary>
<p>

Receive a message every time a transaction affects the given order book. This message include precise information how the transaction affected the ledger and the order book.

</p>
</details>
<details><summary>9. Derive new order books on every new transaction</summary>
<p>

Everytime the bot receives a new message (described in step 4) that a transaction affected an order book. The bot takes the transaction and the affected order book to see how the transaction changed the order book. It then parses the final state of the order book. To do this it uses the [`parse_final_order_book`](https://github.com/LimpidCrypto/XRPL-trading-bot/blob/main/xrpl_trading_bot/txn_parser/order_book_changes.py#L52) parser.

</p>
</details>
<details><summary>10. Build trade paths</summary>
<p>

You could say that the decentralized exchange of the XRP Ledger is nothing more than a collection of limit orders. Orders are called [`Offers`](https://xrpl.org/offers.html#offers) on the XRP Ledger. Every time the user wants to trade a currency against another he needs to find another participant, who wants to trade the exact same currencies in the other direction, at the same or better exchange rate. For Examlple:
<br>Person A is willing to pay 10.70 USD in order to receive 10 EUR. To let everybody know he is willing to so he submits an [`OfferCreate`](https://xrpl.org/offercreate.html) transaction to the network. This transaction creates an [`Offer`](https://xrpl.org/offer.html#offer) object on the XRP Ledger which everybody in the network is able to see. Now Person B comes into play. Person B sees that offer of Person A and wants to trade it. So Person B is willing to pay 10 EUR in order to receive 10.70 USD. Person B now submits a `OfferCreate` transaction just as Person A did before. Because both `Offers` have the same exchange rate they are consuming each other. Person A gets 10 EUR from Person B and Person B gets 10.70 USD from Person A.
<br><br>You can imagine that the trading bot is Person B. The bot is constantly searching for `Offers` which combined will result in profit due to price differences. If the bot combine and compare two or more `Offers` with each other this is called a *trade path*.
<br><br>

</p>
</details>
<details><summary>10.5. Adjust values for each trade path</summary>
<p>

</p>
</details>
<details><summary>11. Calulate the profit of each trade path</summary>
<p>

</p>
</details>
<details><summary>12. Filter for the profitable trade paths</summary>
<p>

</p>
</details>
</details>
<details><summary>13. Build the OfferCreate transactions</summary>
<p>

</p>
</details>
</details>
<details><summary>14. Sign the transactions</summary>
<p>

</p>
</details>
</details>
<details><summary>15. Submit the transactions</summary>
<p>

</p>
</details>
</details>
<details><summary>16. Wait for all transaction results</summary>
<p>

</p>
</details>
</details>
<details><summary>17. Repeat from step 6</summary>
<p>

</p>
</details>

## 📈 Trading types:

### 💱 Arbitrage Trading
The arbitrage trading bot takes advantage of the price differences in different liquid order books to make profit.
##### Types:
| [Basic Spatial Arbitrage](https://en.wikipedia.org/wiki/Arbitrage#Spatial_arbitrage)       | [Triangular Arbitrage](https://en.wikipedia.org/wiki/Triangular_arbitrage)          |
| ----------------------------- | ----------------------------- |
| 1. Order: USD.*r1* > BTC.*r1* | 1. Order: USD.*r1* > BTC.*r1* |
| 2. Order: BTC.*r2* > USD.*r2* | 2. Order: BTC.*r2* > ETH.*r1* |
|                               | 3. Order: ETH.*r2* > USD.*r2* |
##### Example:
The bot places an immediate or cancel offer that trades 10 USD.r1 for 9 EUR.r1. The bot then places a second immediate or cancel offer that trades 9 EUR.r2 for 11 USD.r2. The profit for this trade is 1 USD. Neither the `TakerGets` nor the `TakerPays` issuers have to be the same for both trades. All four issuers can be completely different. Doing so brings the most flexibility.
<br>The bot only trades liquid order books and adjusts all `Offer` values from the lowest `TakerGets` balance.

### 🌊 [Market Maker](https://en.wikipedia.org/wiki/Market_maker)
Market makers provide liquidity to a market. Place a buy and a sell order on the tip of a illiquid order book. The spread the two orders has to be big enough to cover the potential [transfer fees](https://xrpl.org/transfer-fees.html#transfer-fees). The market maker bot only trades illiquid order books, where %[^1] of the orders have been consumed in the last 2 weeks.
##### Example:
The order books most expensive bid order has a price of 50 $ and the cheapest ask order price is 52 $, so the spread is 3.85 %[^2].
<br>The bot then calculates what prices it needs to place the orders at to cover the transfer fees and still be profitable while minimize the current spread of 3.85 %. It aims to provide a spread of 0.5 %. If one or both orders are not fulfilled after a week the orders will get canceled automatically.

[^1]: not determined yet
[^2]: [quoted spread](https://en.wikipedia.org/wiki/Bid%E2%80%93ask_spread#Quoted_spread) = (52 $ - 50 $) / 51 $ * 100    ((ask - bid) / midpoint * 100)
