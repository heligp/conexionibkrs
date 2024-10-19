from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from contract import crear_contrato
from ibapi.order import Order

# Clase para manejar la conexión a IBKR
class IBKRConnection(EWrapper, EClient):
    def __init__(self, data_handlers):
        EClient.__init__(self, self)
        self.data_handlers = data_handlers  # Diccionario de manejadores de datos para cada ticker
        self.order_id_counter = 1  # Contador de ID de órdenes
        self.active_orders = {}  # Diccionario para rastrear órdenes activas

    def tickPrice(self, reqId, tickType, price, attrib):

        # Validar que sea el último precio
        if tickType == 4:
        # Guardar el precio recibido en el data handler correspondiente al ticker        
            if reqId in self.data_handlers:
                self.data_handlers[reqId].add_tick(price)

    def tickSize(self, reqId, tickType, size):
        
        # Validar que sea el último precio
        if tickType == 4:
            print(size)
            # Guardar el tamaño (volumen) en el data handler correspondiente al ticker
            if reqId in self.data_handlers:
                self.data_handlers[reqId].add_volume(size)

    def enviar_orden(self, stock, cantidad, direccion, precio=None):

        # Verificar si ya hay una orden activa para este ticker
        if stock['ticker'] in self.active_orders and self.active_orders[stock['ticker']]:
            print(f"Ya hay una orden activa para {stock['ticker']}. No se enviará otra.")
            return
        
        # Crear un contrato para el ticker
        contrato = crear_contrato(stock)

        # Crear una orden
        orden = Order()
        orden.action = direccion  # 'BUY' o 'SELL'
        orden.orderType = 'MKT'  # Tipo de orden (por ejemplo, mercado)
        orden.totalQuantity = cantidad
        
        # Enviar la orden
        self.placeOrder(self.nextOrderId, contrato, orden)
        print(f"Orden enviada: {direccion} {cantidad} acciones de {stock['ticker']}")

        # Marcar la orden como activa
        self.active_orders[stock['ticker']] = True

       # Incrementar el contador de ID de órdenes
        self.order_id_counter += 1

    def nextOrderId(self):
        # Implementa la lógica para manejar el siguiente ID de orden
        return self.order_id_counter
    
    def orderStatus(self, orderId, status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice):
        print(f"Estado de la orden ID {orderId}: {status}, llenada: {filled}, restante: {remaining}")

        if status in ['Filled', 'Cancelled', 'Inactive']:
            # Actualizar el estado de la orden en active_orders
            for ticker, active in self.active_orders.items():
                if active:  # Si hay una orden activa
                    # Aquí puedes implementar lógica adicional para identificar qué orden
                    self.active_orders[ticker] = False  # Marcar como no activa

    
    