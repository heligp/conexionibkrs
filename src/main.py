import threading  # Importa threading para ejecutar el ciclo de la API en un hilo separado
from contract import crear_contrato  # Importa la función que crea contratos para la solicitud de datos de mercado
from connector import IBKRConnection  # Clase de conexión con Interactive Brokers
from data_handler import DataHandler  # Clase para manejar los datos de ticks y volumen
from load_model import scaler_btc, model_btc  # Importa el modelo y el escalador (scaler) para Bitcoin
from symbols import symbols  # Diccionario con los símbolos (tickers) de los activos a monitorear
import time  # Módulo para manejar tiempos de espera
import warnings  # Módulo para manejar advertencias

# Ignorar advertencias específicas de UserWarning
warnings.simplefilter("ignore", category=UserWarning)

# Definir el umbral de volumen para generar una barra OHLC
threshold_bar = .00000005  # Umbral mínimo de volumen para generar una barra OHLC
threshold_features = 1  # Número de barras necesarias para calcular los features

# Lista de modelos y escaladores, en este caso solo hay uno para Bitcoin
models = [model_btc]  # Modelo de predicción cargado para Bitcoin
scalers = [scaler_btc]  # Escalador para normalizar los datos antes de pasarlos al modelo

# Crear un diccionario de DataHandlers, uno para cada símbolo en "symbols"
data_handlers = {i: DataHandler(symbol, threshold_bar, threshold_features, None, models[0], scalers[0]) 
                 for i, symbol in symbols.items()}  
# Itera sobre "symbols" y crea un objeto DataHandler para cada ticker. El índice es "i" y el valor es "symbol".
# A cada DataHandler se le pasa el ticker, el umbral de volumen, el umbral de features, el modelo y el escalador.

# Iniciar la conexión a Interactive Brokers (IBKR) y pasar los data handlers
app = IBKRConnection(data_handlers)  # Crea la conexión a IBKR con los data handlers
app.connect("127.0.0.1", 7497, 0)  # Se conecta al servidor de IBKR en localhost (127.0.0.1), puerto 7497 (por defecto)
time.sleep(1)  # Espera un segundo para asegurarse de que la conexión esté establecida

# Función que ejecuta el ciclo de eventos de IBKR
def run_loop():
    app.run()  # Inicia el ciclo de eventos de IBKR que maneja la recepción de datos de mercado, órdenes, etc.

# Asignar la conexión "app" a cada DataHandler (ya que ahora la conexión está activa)
for handler in data_handlers.values():
    handler.connection = app  # Asigna la conexión IBKR a cada DataHandler

# Iniciar el ciclo de eventos de IBKR en un hilo separado
api_thread = threading.Thread(target=run_loop, daemon=True)  
# Crea un hilo para ejecutar el ciclo "app.run()" en segundo plano (daemon), para que no bloquee el hilo principal.
api_thread.start()  # Inicia el hilo

# Solicitar datos de mercado para cada símbolo (ticker)
for reqId, ticker in enumerate(list(symbols.values())):
    contrato = crear_contrato(ticker)  # Crea un contrato para cada símbolo
    app.reqMktData(reqId, contrato, "", False, False, [])  
    # Solicita los datos de mercado para el contrato (ticker) creado. 
    # "reqId" es el identificador de la solicitud, y la lista vacía es para campos adicionales (opcional).

# Bloque try-except para mantener el programa corriendo y permitir la desconexión limpia en caso de interrupción
try:
    while True:  # Mantiene el programa corriendo indefinidamente
        time.sleep(.1)  # Espera 0.1 segundos entre cada iteración del bucle para evitar consumo excesivo de CPU
except KeyboardInterrupt:  # Captura una interrupción del teclado (Ctrl+C)
    print("Desconectando...")  # Muestra un mensaje antes de desconectar
    app.disconnect()  # Desconecta la aplicación de IBKR de manera limpia