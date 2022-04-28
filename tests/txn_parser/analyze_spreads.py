from decimal import Decimal
import json

with open("tests/txn_parser/spreads.json", "r") as infile:
    spreads = json.load(infile)

sum = 0

assert isinstance(spreads, dict)
spreads = spreads.values()
num_spreads = len(list(spreads))
for spread in spreads:
    spread = Decimal(spread)
    sum += spread

print(sum / num_spreads)
