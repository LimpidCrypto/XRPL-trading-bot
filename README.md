# XRPL-trading-bot
A trading bot that uses the decentralized exchange of the XRP Ledger

### Project in active development!

## TODOS:
#### Clients
- [x] Async rippled API requests
- ##### Methods
  - [ ] Subscribe to balance changes
  - [ ] Subscribe to order books
  - [ ] Submit transactions

#### Order books
- [ ] Final order book parser
- [ ] Identify all possible order books based on the accounts currencies
- [ ] Identify liquid and illiquid order books

#### Arbitrage trading

- [ ] Identify all possible trading paths[^1] based on liquid order books
  | Basic Spatial Arbitrage    | Triangular Arbitrage       |
  | -------------------------- | -------------------------- |
  | 1. PS: USD.*r1* > BTC.*r1* | 1. PS: USD.*r1* > BTC.*r1* |
  | 2. PS: BTC.*r2* > USD.*r2* | 2. PS: BTC.*r2* > ETH.*r1* |
  |                            | 3. PS: ETH.*r2* > USD.*r2* |
- [ ] Adjust values
  - The lowest value is the value to calculate every other value from
  (also take account balance in account)
- [ ] Calculate profit after fees

#### Market maker
- [ ] Identify exchange rates of buy and sell offers based on the spread of the illiquid order books after fees
- [ ] Calculate values based on accounts balance and order book depth
- [ ] Calculate profit after fees

#### Wallet
- [ ] Wallet creation by seed ***via input***
- [ ] Signing
- [ ] Make trading paths identifiable by a random memo
- [ ] Tangem integration (not in near future)


[^1]: Trading paths devided in path steps (PS)
