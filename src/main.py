from contract import crear_contrato
from connector import IBKRConnection
from data_handler import DataHandler
from load_model import scaler_btc, model_btc
import time


tickers = ['BTC']
sectype = "CRYPTO"
exchange = "PAZOS"
currency = "USD"
    
threshold_bar = 50 
threshold_features = 500
models = [model_btc]
scalers = [scaler_btc]

if __name__ == "__main__":

    # Crear un diccionario de DataHandlers para cada ticker
    data_handlers = {i: DataHandler(ticker, threshold_bar, threshold_features, None, models[0], scalers[0]) for i, ticker in enumerate(tickers)}    
    
    # Iniciar la conexión a IBKR y pasar los data handlers
    app = IBKRConnection(data_handlers)
    app.connect("127.0.0.1", 7497, 0)
    
    # Asignar la conexión a cada DataHandler
    for handler in data_handlers.values():
        handler.connection = app

    # Solicitar datos de mercado para cada ticker
    for reqId, ticker in enumerate(tickers):
        contrato = crear_contrato(ticker, sectype, exchange, currency)
        app.reqMarketDataType(1)  # Tipo de datos
        app.reqMktData(reqId, contrato, "", False, False, [])
    print("asdfasd")

    app.run()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Desconectando...")
        app.disconnect()