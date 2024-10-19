from ibapi.contract import Contract

# Configurar el contrato para cada ticker
def crear_contrato(stock):
    contrato = Contract()
    contrato.symbol = stock['ticker']
    contrato.secType = stock['sectype']
    contrato.exchange = stock['exchange']
    contrato.currency = stock['currency']
    return contrato