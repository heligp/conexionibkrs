# Importamos las clases necesarias desde el API de Interactive Brokers (IB API)
from ibapi.client import EClient  # Cliente que se conecta al servidor de IB
from ibapi.wrapper import EWrapper  # Envuelve las funciones de callback (retorno)
from contract import crear_contrato  # Función para crear un contrato (no definido aquí)
from ibapi.common import TickAttribLast, TickerId, TickAttrib  # Tipos comunes usados en la API de IB
from ibapi.ticktype import TickType  # Tipos de "ticks" que puede recibir el sistema
from ibapi.utils import floatMaxString, decimalMaxString, intMaxString  # Utilidades para convertir valores numéricos
from decimal import Decimal  # Tipo Decimal para mayor precisión en los cálculos financieros
from mensaje import send_message  # Función externa para enviar mensajes (no definida aquí)
import time  # Librería para manejar tiempos
from ibapi.order_cancel import OrderCancel  # Función para cancelar órdenes (no definida aquí)

# Clase principal que maneja la conexión con Interactive Brokers, extiende EWrapper (para recibir datos)
# y EClient (para enviar solicitudes)
class IBKRConnection(EWrapper, EClient):
    
    # Constructor de la clase
    def __init__(self, data_handlers):
        # Inicializa el cliente de IBKR
        EClient.__init__(self, self)
        # data_handlers es un diccionario para manejar los datos recibidos por ID
        self.data_handlers = data_handlers
        # Contador para los IDs de las órdenes
        self.order_id_counter = 1
        # Contador para medir volumen de transacciones
        self.counter_vol = 0
        # Volumen de referencia para comparar cambios en el volumen de tickers
        self.vol_ref = 0

    # Método que recibe los precios de los "ticks" del mercado en tiempo real
    # reqId: Identificador del ticker (acción, instrumento, etc.)
    # tickType: Tipo de tick (precio de oferta, demanda, último, etc.)
    # price: Precio del tick
    # attrib: Atributos adicionales del tick (como si es o no una transacción de baja latencia)
    def tickPrice(self, reqId: TickerId, tickType: TickType, price: float, attrib: TickAttrib):
        # Solo manejamos el tickType 4 (último precio de transacción)
        if tickType == 4:
            # Verifica si el reqId está en el diccionario de data_handlers
            if reqId in self.data_handlers:
                # Agrega el precio recibido al handler correspondiente
                self.data_handlers[reqId].add_tick(price)
                # Actualiza el último precio registrado
                self.data_handlers[reqId].last_tick = price

    # Método que recibe el tamaño de los ticks (volumen de operaciones)
    # reqId: Identificador del ticker
    # tickType: Tipo de tick (8 es volumen de operaciones)
    # size: Tamaño del tick (volumen)
    def tickSize(self, reqId: TickerId, tickType: TickType, size: Decimal):
        # Solo manejamos el tickType 8 (volumen de transacciones)
        if tickType == 8:
            # Si el reqId está en el diccionario de data_handlers
            if reqId in self.data_handlers:
                # Si es la primera vez que recibimos un volumen, lo tomamos como referencia
                if self.counter_vol == 0:
                    self.vol_ref = size
                else: 
                    # Calcula la diferencia entre el volumen actual y el volumen de referencia
                    self.data_handlers[reqId].add_volume(size - self.vol_ref)
                    # Actualiza el volumen de referencia
                    self.vol_ref = size
                # Incrementa el contador de volúmenes procesados
                self.counter_vol += 1
                print('tick')  # Imprime un mensaje cada vez que se recibe un nuevo tick

    # Método para enviar un mensaje (a través de una función externa)
    # stock: Diccionario con información de la acción/stock
    # cantidad: Cantidad de acciones involucradas en la transacción
    # direccion: Dirección de la operación (compra/venta)
    # dif: Diferencia de precios o volumen (cualquier dato relevante)
    def enviar_mensaje(self, stock, cantidad, direccion, dif):
        # Obtiene el ticker (símbolo de la acción) del diccionario stock
        ticker = stock['ticker']
        # Llama a la función externa send_message para enviar un mensaje
        resp = send_message(ticker, cantidad, direccion, dif)
        # Imprime la respuesta recibida después de enviar el mensaje
        print(resp[1])

    # Método que se llama cuando IB nos da el siguiente ID válido para las órdenes
    def nextValidId(self, orderId: int):
        # Actualiza el contador de IDs de órdenes con el nuevo valor
        self.order_id_counter = orderId
        # Imprime el siguiente ID de orden válido
        print(f"Siguiente OrderId válido: {orderId}")

    # Método para generar el próximo ID de orden, incrementa el contador de IDs
    def nextOrderId(self):
        # Guarda el ID actual en una variable
        current_id = self.order_id_counter
        # Incrementa el contador de IDs
        self.order_id_counter += 1
        # Devuelve el ID actual
        return current_id



        # Información en tiempo real
        # def tickByTickAllLast(self, reqId: int, tickType: int, time: int, price: float, size: Decimal, tickAtrribLast: TickAttribLast, exchange: str, specialConditions: str):
        #     print(f"ReqId: {reqId}, Time: {time}, Price: {price}, Size: {size}")
        #     if reqId in self.data_handlers:
        #         self.data_handlers[reqId].add_tick(price)
        #         self.data_handlers[reqId].add_volume(size)
        