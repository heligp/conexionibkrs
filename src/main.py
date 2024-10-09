from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
import threading
import time


            
class IBApi(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)

    def error(self, reqId, errorCode, errorString,advancedOrderRejectJson):
        print(f"Error: {reqId}, Code: {errorCode}, Msg: {errorString}")

    def nextValidId(self, orderId):
        self.nextOrderId = orderId
        print(f"Next Order ID: {self.nextOrderId}")

    def contractDetails(self, reqId, contractDetails):
        print(f"Contract Details: {contractDetails}")

    def tickPrice(self, reqId, tickType, price, attrib):
        # if tickType == 1:  # Precio de oferta (bid)
        #     print(f"Oferta: {price}")
        # elif tickType == 2:  # Precio de venta (ask)
        #     print(f"Venta: {price}")
        # elif tickType == 4:  # Último precio
        #     print(f"Último precio: {price}")
        if tickType == 4:  # Último precio
            print(f"Último precio: {price}")
    
    def tickSize(self, reqId, tickType, size):
        if tickType == 0:  # Volumen de oferta (bid size)
            print(f"Volumen de oferta: {size}")
        elif tickType == 3:  # Volumen de venta (ask size)
            print(f"Volumen de venta: {size}")
        elif tickType == 5:  # Volumen negociado
            print(f"Volumen negociado: {size}")

def run_loop():
    app.run()

app = IBApi()

# Conectar a Interactive Brokers - TWS Paper Trading usa el puerto 7497
app.connect("127.0.0.1", 7497, 1)

# Iniciar el loop en un thread
api_thread = threading.Thread(target=run_loop, daemon=True)
api_thread.start()

# Esperar para establecer la conexión
time.sleep(1)

# Crear un contrato para solicitar datos (ejemplo: acciones de Apple)
contract = Contract()
contract.symbol = "BTC"
contract.secType = "CRYPTO"
contract.exchange = "PAXOS"
contract.currency = "USD"

# # Solicitar los detalles del contrato
# app.reqContractDetails(1001, contract)

# Solicitar en tiempo real
app.reqMktData(1001, contract, "", False, False, [])


try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Desconectando...")
    app.disconnect()