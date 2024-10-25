
from ibapi.client import EClient  # Clase base para crear un cliente de IBKR (Interactive Brokers)
from ibapi.wrapper import EWrapper  # Clase base para recibir datos y eventos de IBKR
from contract import crear_contrato  # Función para crear contratos de mercado
from order import  create_orden_market_con_bracket  # Funciones para crear diferentes tipos de órdenes
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
        self.active_bracket_orders = {}  # Estado de los brackets pendientes por ticker
        self.order_brackets_map = {}  # Mapa de los brackets de órdenes
        self.parentIds = []  # Lista de IDs de órdenes parent

    # Función que recibe los precios de los ticks
    def tickPrice(self, reqId: TickerId, tickType: TickType, price: float, attrib: TickAttrib):
        """
        Funcionamiento: Recibe los precios de los ticks desde la API de IBKR y actualiza el manejador de datos correspondiente para el ticker especificado.
        Parámetros:
        - reqId: Identificador del ticker al que se está asociando el precio.
        - tickType: Tipo de tick recibido (por ejemplo, precio último).
        - price: El precio del tick recibido.
        - attrib: Atributos asociados al tick (por ejemplo, información adicional sobre el precio).
        """
        if tickType == 4:  # Si es el último precio (tickType 4)
            if reqId in self.data_handlers:  # Si el reqId está en los data handlers
                self.data_handlers[reqId].add_tick(price)  # Añade el precio al manejador de datos
                self.data_handlers[reqId].last_tick = price  # Guarda el último precio

    # Función que recibe el tamaño del volumen de los ticks
    def tickSize(self, reqId: TickerId, tickType: TickType, size: Decimal):
        """
        Funcionamiento: Recibe el tamaño del volumen de los ticks y actualiza la referencia de volumen y los datos del manejador correspondiente.
        Parámetros:
        - reqId: Identificador del ticker al que se está asociando el tamaño del volumen.
        - tickType: Tipo de tick recibido (por ejemplo, volumen).
        - size: El tamaño del volumen recibido en forma de Decimal.
        """
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
        """
        Funcionamiento: Cancela todas las órdenes activas al iniciar la conexión. Restablece el estado de los brackets pendientes.
        Parámetros: Ninguno.
        """
        print("Cancelando todas las órdenes activas al iniciar.")
        oc = OrderCancel()  # Crear un objeto de cancelación de órdenes
        self.reqGlobalCancel(oc)  # Cancela todas las órdenes activas en la cuenta
        self.brackets_pendientes = {}  # Restablece el estado de brackets pendientes

    # Función para cancelar una orden específica basada en el ticker
    def cancelar_orden(self, ticker, oc):
        """
        Funcionamiento: Cancela una orden específica basada en el ticker proporcionado si existe una orden activa para ese ticker.
        Parámetros:
        - ticker: El símbolo del activo cuya orden se desea cancelar.
        - oc: Un objeto de tipo OrderCancel utilizado para cancelar la orden.
        """

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

    # Función para recibir el siguiente orderId válido
    def nextValidId(self, orderId: int):
        """
        Funcionamiento: Recibe el siguiente ID de orden válido desde la API y actualiza el contador de IDs de órdenes.
        Parámetros:
        - orderId: El ID de la siguiente orden válida recibido desde la API.
        """
        self.order_id_counter = orderId  # Actualiza el contador de IDs de órdenes
        print(f"Siguiente OrderId válido: {orderId}")

    # Función para obtener el próximo orderId
    def nextOrderId(self):
        """
        Funcionamiento: Retorna el próximo ID de orden disponible, incrementando el contador de IDs de órdenes.
        Parámetros: Ninguno.
        """
        current_id = self.order_id_counter  # Obtiene el orderId actual
        self.order_id_counter += 1  # Incrementa el orderId
        return current_id  # Retorna el orderId actual


    def enviar_orden(self, stock, cantidad, direccion, dif):

        """
        Funcionamiento: Envía una orden al mercado, verificando primero si hay órdenes activas o pendientes para el ticker especificado. Crea un contrato y órdenes de tipo bracket antes de enviarlas.
        Parámetros:
        - stock: Un diccionario que contiene la información del activo (incluyendo el ticker).
        - cantidad: Número de acciones que se desea comprar o vender.
        - direccion: Dirección de la orden, que puede ser 'buy' (compra) o 'sell' (venta).
        - dif: Diferencia utilizada para establecer el bracket en las órdenes.
        """
        ticker = stock['ticker']
        oc = OrderCancel()

        print("Active orders:",self.active_orders)
        # Verifica si hay una orden activa y si ha estado pendiente más de 10 segundos
        if self.active_orders.get(ticker, True) and ticker in self.active_orders:
            print(f"Ya hay una orden activa para {ticker}")
            return

        print("Active bracket orders:",self.active_bracket_orders)
        if self.active_bracket_orders.get(ticker, True) and ticker in self.active_bracket_orders: 
            print(f"Orden de bracket aún no llenada para {ticker}")
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
        for idx, orden in enumerate(ordenes):
            self.placeOrder(orden.orderId, contrato, orden)  # Coloca la orden
            print(orden.orderId)  # Muestra el orderId
            self.nextOrderId()  # Obtiene el siguiente orderId
            print(f"Orden enviada: {direccion} {cantidad} acciones de {ticker}")

            if idx == 0:
                self.active_orders[ticker] = True
                self.order_map[orden.orderId] = ticker
                self.pending_orders[ticker] =  time.time()
            else:
                self.active_bracket_orders[ticker] = True
                self.order_brackets_map[orden.orderId] = ticker
                

    # Función que maneja el estado de las órdenes
    def orderStatus(self, orderId: int, status: str, filled: Decimal, remaining: Decimal, avgFillPrice: float, permId: int, parentId: int, lastFillPrice: float, clientId: int, whyHeld: str, mktCapPrice: float):
        """
        Funcionamiento: Maneja el estado de las órdenes enviadas, actualizando la información sobre el estado de la orden (por ejemplo, si está llena o parcialmente llena).
        Parámetros:
        - orderId: El ID de la orden cuyo estado se está reportando.
        - status: El estado actual de la orden (por ejemplo, 'Filled' o 'Pending').
        - filled: Cantidad de acciones que han sido llenadas de la orden.
        - remaining: Cantidad de acciones que quedan por llenar.
        - avgFillPrice: Precio promedio al que se ha llenado la orden.
        - permId: ID permanente de la orden.
        - parentId: ID de la orden principal si es una orden de tipo bracket.
        - lastFillPrice: Precio al que se llenó la última parte de la orden.
        - clientId: ID del cliente asociado a la orden.
        - whyHeld: Razón por la que la orden está retenida.
        - mktCapPrice: Precio del mercado para la orden.
        """
        print(f"Estado de la orden ID {orderId}: {status}, llenada: {filled}, restante: {remaining}")

        if status in ["Filled"]:

            if self.order_map.get(orderId) != None:
                ticker = self.order_map.get(orderId)
            elif self.order_map.get(orderId) == None and  self.order_brackets_map.get(orderId) == None : return
            else:
                ticker = self.order_brackets_map.get(orderId)

            if self.active_orders[ticker] == True:
                # Actualiza el estado de la orden a inactiva
                self.active_orders[ticker] = False
                del self.pending_orders[ticker]
                del self.order_map[orderId]

            # Si es una orden de bracket
            elif self.active_bracket_orders[ticker] == True:
                self.active_bracket_orders[ticker] = False
                del self.order_brackets_map[orderId]
                time.sleep(2)

            # Información en tiempo real
            # def tickByTickAllLast(self, reqId: int, tickType: int, time: int, price: float, size: Decimal, tickAtrribLast: TickAttribLast, exchange: str, specialConditions: str):
            #     print(f"ReqId: {reqId}, Time: {time}, Price: {price}, Size: {size}")
            #     if reqId in self.data_handlers:
            #         self.data_handlers[reqId].add_tick(price)
            #         self.data_handlers[reqId].add_volume(size)
            