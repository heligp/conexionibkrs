import sys
import ibapi
print(ibapi.__version__)
sys.exit()
import threading  # Importa threading para manejar el loop de la API en un hilo separado
from contract import crear_contrato  # Función para crear contratos de mercado para los tickers
from connector import IBKRConnection  # Conexión a la API de IBKR (Interactive Brokers)
from data_handler import DataHandler  # Manejador de datos que procesa los ticks y genera las barras OHLC
from load_model import scaler_btc, model_btc  # Importa el modelo de predicción y el escalador para Bitcoin
from symbols import symbols  # Diccionario de símbolos o tickers que se usarán
import time  # Para gestionar retrasos y temporización
import warnings  # Para manejar advertencias de usuarios

# Ignora advertencias de tipo UserWarning
warnings.simplefilter("ignore", category=UserWarning)

# Parámetros de umbral (threshold) para la generación de barras y features
threshold_bar = .00000005  # Umbral de volumen acumulado para generar una barra OHLC
threshold_features = 1  # Umbral de número de barras para generar features

# Lista de modelos y escaladores que se usarán para las predicciones
models = [model_btc]  # Solo un modelo (para Bitcoin en este caso)
scalers = [scaler_btc]  # Escalador correspondiente al modelo de Bitcoin

# Crear un diccionario de DataHandlers, uno para cada ticker
# Cada DataHandler se encarga de procesar los datos de un ticker específico
data_handlers = {i: DataHandler(symbol, threshold_bar, threshold_features, None, models[0], scalers[0]) 
                 for i, symbol in symbols.items()}  

# Inicializa la conexión a la API de IBKR y le pasa los DataHandlers creados
app = IBKRConnection(data_handlers)
app.connect("127.0.0.1", 7497, 0)  # Conecta la aplicación a la API local de IBKR en el puerto 7497
time.sleep(1)  # Espera un segundo para asegurarse de que la conexión se establezca

# Solicita las órdenes abiertas actualmente
app.reqOpenOrders()

# Cancela todas las órdenes pendientes que no han sido ejecutadas
app.cancelar_ordenes_pendientes()  

# Función para iniciar el loop de la aplicación
def run_loop():
    app.run()  # Ejecuta el ciclo principal de IBKR que recibe y procesa los eventos

# Asignar la conexión a cada DataHandler
# Ahora cada DataHandler tendrá acceso a la conexión IBKR
for handler in data_handlers.values():
    handler.connection = app

# Iniciar el loop de la API en un hilo separado
api_thread = threading.Thread(target=run_loop, daemon=True)  # El hilo es "daemon" para que termine cuando la aplicación termine
api_thread.start()  # Comienza el hilo para procesar la API

# Solicitar datos de mercado (precios y volumen) para cada ticker
for reqId, ticker in enumerate(list(symbols.values())):
    contrato = crear_contrato(ticker)  # Crea el contrato asociado al ticker
    # Solicita los datos de mercado para cada contrato (ticker)
    # reqId es un identificador único para la solicitud de datos, y "" indica que no se requieren datos adicionales
    app.reqMktData(reqId, contrato, "", False, False, [])
    # app.reqTickByTickData(reqId, contract, "Last", 0, True) # En caso sea data en vivo
    

# Mantener el programa ejecutándose hasta que el usuario lo interrumpa (ejemplo: Ctrl+C)
try:
    while True:
        time.sleep(.1)  # Mantiene el bucle activo con pequeños retrasos para no sobrecargar la CPU
except KeyboardInterrupt:
    # Si el usuario interrumpe la ejecución (con Ctrl+C), se desconecta de la API de IBKR
    print("Desconectando...")
    app.disconnect()  # Cierra la conexión correctamente
