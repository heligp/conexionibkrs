tickers = ['BTC']
sectype = ["CRYPTO"]
exchange = ["PAXOS"]
currency = ["USD"]

symbols = {}
for idx, (t, s, e, c) in enumerate(zip(tickers, sectype, exchange, currency)):
    temp_dict = {}
    temp_dict['ticker'] = t
    temp_dict['sectype'] = s
    temp_dict['exchange'] = e
    temp_dict['currency'] = c
    symbols[idx] = temp_dict


# for i, symbol in enumerate(symbols.values()):
#     print(symbol)
# import sys
# sys.exit()