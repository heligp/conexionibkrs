from ibapi.client import EClient  # Clase base para crear un cliente de IBKR (Interactive Brokers)
from ibapi.wrapper import EWrapper  # Clase base para recibir datos y eventos de IBKR
from contract import crear_contrato  # Función para crear contratos de mercado
from order import create_bracket_order_with_expiry, create_orden_market, create_orden_market_con_bracket  # Funciones para crear diferentes tipos de órdenes
from ibapi.common import TickAttribLast, TickerId, TickAttrib  # Clases para atributos comunes de IBKR
from ibapi.ticktype import TickType  # Tipos de tick (precio, volumen, etc.)
from ibapi.utils import floatMaxString, decimalMaxString, intMaxString  # Utilidades de IBKR para formateo
from decimal import Decimal  # Para manejar valores decimales con precisión
import time  # Para manejar temporización
from ibapi.order_cancel import OrderCancel  # Clase para cancelar órdenes en IBKR

# Clase que combina las funcionalidades de EWrapper y EClient para manejar la conexión a IBKR
class IBKRConnection(EWrapper, EClient):
    def __init__(self, data_handlers):
        # Inicializa el cliente IBKR (EClient)
        EClient.__init__(self, self)
        self.data_handlers = data_handlers  # Diccionario que maneja los datos de mercado por ticker
        self.order_id_counter = 1  # Contador de IDs de órdenes
        self.active_orders = {}  # Almacena el estado de órdenes activas
        self.executed_price = None  # Precio ejecutado de la última orden
        self.current_contract = None  # El contrato actual (ticker)
        self.pending_orders = {}  # Almacena las órdenes pendientes con su timestamp
        self.order_map = {}  # Mapea los tickers a los orderId
        self.counter_vol = 0  # Contador de volumen procesado
        self.vol_ref = 0  # Referencia para el volumen acumulado
        self.brackets_pendientes = {}  # Estado de los brackets pendientes por ticker
        self.order_brackets_map = {}  # Mapa de los brackets de órdenes
        self.parentIds = []  # Lista de IDs de órdenes parent

    # Función que recibe los precios de los ticks
    def tickPrice(self, reqId: TickerId, tickType: TickType, price: float, attrib: TickAttrib):
        if tickType == 4:  # Si es el último precio (tickType 4)
            if reqId in self.data_handlers:  # Si el reqId está en los data handlers
                self.data_handlers[reqId].add_tick(price)  # Añade el precio al manejador de datos
                self.data_handlers[reqId].last_tick = price  # Guarda el último precio

    # Función que recibe el tamaño del volumen de los ticks
    def tickSize(self, reqId: TickerId, tickType: TickType, size: Decimal):
        if tickType == 8:  # Si es el tipo de volumen (tickType 8)
            if reqId in self.data_handlers:
                if self.counter_vol == 0:  # Si es el primer tick de volumen
                    self.vol_ref = size  # Guarda la referencia del volumen
                else:
                    self.data_handlers[reqId].add_volume(size - self.vol_ref)  # Añade la diferencia del volumen
                self.vol_ref = size  # Actualiza la referencia de volumen
                self.counter_vol += 1  # Incrementa el contador de volumen
                print('tick')  # Imprime que ha llegado un tick

    # Función para cancelar todas las órdenes pendientes al iniciar
    def cancelar_ordenes_pendientes(self):
        print("Cancelando todas las órdenes activas al iniciar.")
        oc = OrderCancel()  # Crear un objeto de cancelación de órdenes
        self.reqGlobalCancel(oc)  # Cancela todas las órdenes activas en la cuenta
        self.brackets_pendientes = {}  # Restablece el estado de brackets pendientes

    # Función para cancelar una orden específica basada en el ticker
    def cancelar_orden(self, ticker, oc):
        if ticker in self.active_orders and self.active_orders[ticker]:  # Si hay una orden activa para este ticker
            order_id = self.order_map.get(ticker)  # Obtiene el orderId del ticker
            if order_id is not None:
                print(f"Cancelando la orden activa para {ticker}.")
                try:
                    self.cancelOrder(order_id, oc)  # Cancela la orden
                except Exception as e:
                    print(f"Error al cancelar la orden ID {order_id} para {ticker}: {str(e)}")
                self.active_orders[ticker] = False  # Marca la orden como no activa
            else:
                print(f"No se encontró orderId para {ticker}.")
        else:
            print(f"No hay orden activa para {ticker} que cancelar.")

    # Función para enviar una orden de mercado
    def enviar_orden(self, stock, cantidad, direccion, dif):
        ticker = stock['ticker']  # Ticker del activo
        oc = OrderCancel()  # Crear un objeto de cancelación

        # Verifica si ya hay brackets pendientes para este ticker
        if ticker in self.brackets_pendientes and self.brackets_pendientes[ticker]:
            print(f"No se puede enviar una nueva orden para {ticker}: hay órdenes de bracket pendientes.")
            return

        # Verifica si hay una orden activa y si ha estado pendiente más de 10 segundos
        if ticker in self.active_orders and self.active_orders[ticker]:
            print(f"Ya hay una orden activa para {ticker}")
            if time.time() - self.pending_orders[ticker] > 10:
                print(f"La orden está hace más de 10 segundos, cancelando")
                self.cancelar_orden(ticker, oc)  # Cancela la orden si es necesario
                return
            else:
                print(f"La orden está hace menos de 10 segundos, omitir la actual")
                return

        # Encuentra el reqId correspondiente al ticker
        reqId = [key for key, val in self.data_handlers.items() if val.ticker['ticker'] == stock['ticker']][0]
        ultimo_tick = self.data_handlers[reqId].last_tick  # Último precio del ticker

        # Crear un contrato para el ticker y obtener el siguiente orderId
        contrato = crear_contrato(stock)
        self.current_contract = contrato
        order_id = self.nextOrderId()
        
        # Crear las órdenes con el bracket (orden principal, take-profit, y stop-loss)
        ordenes = create_orden_market_con_bracket(order_id, direccion, cantidad, dif, ultimo_tick)

        # Envía las órdenes al mercado
        for orden in ordenes:
            self.placeOrder(orden.orderId, contrato, orden)  # Coloca la orden
            print(orden.orderId)  # Muestra el orderId
            self.nextOrderId()  # Obtiene el siguiente orderId
            print(f"Orden enviada: {direccion} {cantidad} acciones de {ticker}")

    # Función para recibir el siguiente orderId válido
    def nextValidId(self, orderId: int):
        self.order_id_counter = orderId  # Actualiza el contador de IDs de órdenes
        print(f"Siguiente OrderId válido: {orderId}")

    # Función para obtener el próximo orderId
    def nextOrderId(self):
        current_id = self.order_id_counter  # Obtiene el orderId actual
        self.order_id_counter += 1  # Incrementa el orderId
        return current_id  # Retorna el orderId actual

    # Función que muestra el estado de una orden
    def orderStatus(self, orderId, status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice):
        print(f"Estado de la orden ID {orderId}: {status}, llenada: {filled}, restante: {remaining}")

        # # Si la orden fue cancelada o está inactiva, no se hace nada
        # if status in ['Cancelled', 'Inactive']:
        #     return

        # # Si la orden fue completamente llenada
        # if status == 'Filled' and remaining <= 0.00000001:
        #     # Si el orderId no está en parentIds y no tiene un parentId, lo añade
        #     if orderId not in self.parentIds:
        #         if parentId == 0:
        #             self.parentIds.append(orderId)
        #             self.brackets_pendientes[self.current_contract.symbol] = True  # Marca el bracket como pendiente
        #         else:
        #             self.brackets_pendientes[self.current_contract.symbol] = False  # Marca el bracket como completado

        # Información en tiempo real
        # def tickByTickAllLast(self, reqId: int, tickType: int, time: int, price: float, size: Decimal, tickAtrribLast: TickAttribLast, exchange: str, specialConditions: str):
        #     print(f"ReqId: {reqId}, Time: {time}, Price: {price}, Size: {size}")
        #     if reqId in self.data_handlers:
        #         self.data_handlers[reqId].add_tick(price)
        #         self.data_handlers[reqId].add_volume(size)
        