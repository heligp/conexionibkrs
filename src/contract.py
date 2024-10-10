from ibapi.contract import Contract

# Configurar el contrato para cada ticker
def crear_contrato(symbol, secType, exchange, currency):
    contrato = Contract()
    contrato.symbol = symbol
    contrato.secType = secType
    contrato.exchange = exchange
    contrato.currency = currency
    return contrato