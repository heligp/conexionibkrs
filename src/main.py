import threading
from contract import crear_contrato
from connector import IBKRConnection
from data_handler import DataHandler
from load_model import scaler_btc, model_btc
from symbols import symbols
import time




threshold_bar = 50 
threshold_features = 10
models = [model_btc]
scalers = [scaler_btc]



def run_loop():
    app.run()

# Crear un diccionario de DataHandlers para cada ticker
data_handlers = {i: DataHandler(symbol, threshold_bar, threshold_features, None, models[0], scalers[0]) for i, symbol in enumerate(symbols)}    

# Iniciar la conexión a IBKR y pasar los data handlers
app = IBKRConnection(data_handlers)
app.connect("127.0.0.1", 7497, 0)
time.sleep(5)

# Asignar la conexión a cada DataHandler
for handler in data_handlers.values():
    handler.connection = app

#Iniciar el loop en un thread
api_thread = threading.Thread(target=run_loop, daemon = True)
api_thread.start()

# Solicitar datos de mercado para cada ticker
for reqId, ticker in enumerate(list(symbols.values())):
    print(ticker)
    contrato = crear_contrato(ticker)
    app.reqMktData(reqId, contrato, "", False, False, [])


try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Desconectando...")
    app.disconnect()