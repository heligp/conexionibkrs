from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from contract import crear_contrato
from order import create_bracket_order_with_expiry, create_orden_market
from ibapi.common import TickAttribLast
# from ibapi.utils import floatMaxString, decimalMaxString, intMaxString
from decimal import Decimal
import time
from ibapi.order_cancel import OrderCancel

class IBKRConnection(EWrapper, EClient):
    def __init__(self, data_handlers):
        EClient.__init__(self, self)
        self.data_handlers = data_handlers
        self.order_id_counter = 1
        self.active_orders = {}
        self.executed_price = None
        self.current_contract = None
        self.pending_orders = {}
        self.order_map = {}  # Almacena el mapeo de ticker a orderId
        

    def tickByTickAllLast(self, reqId: int, tickType: int, time: int, price: float, size: Decimal, tickAtrribLast: TickAttribLast, exchange: str, specialConditions: str):
        print(f"ReqId: {reqId}, Time: {time}, Price: {price}, Size: {size}")
        if reqId in self.data_handlers:
            self.data_handlers[reqId].add_tick(price)
            self.data_handlers[reqId].add_volume(size)
    
    def cancelar_ordenes_pendientes(self):
        print("Cancelando todas las órdenes activas al iniciar.")
        oc = OrderCancel()
        self.reqGlobalCancel(oc)  # Cancela todas las órdenes activas en la cuenta

    def cancelar_orden(self, ticker):
        if ticker in self.active_orders and self.active_orders[ticker]:
            order_id = self.order_map.get(ticker)  # Obtener el orderId del ticker
            if order_id is not None:
                print(f"Cancelando la orden activa para {ticker}.")
                oc = OrderCancel()
                self.cancelOrder(order_id,oc)  # Cancelar la orden
                self.active_orders[ticker] = False  # Marcar como no activa
            else:
                print(f"No se encontró orderId para {ticker}.")
        else:
            print(f"No hay orden activa para {ticker} que cancelar.")

    def enviar_orden(self, stock, cantidad, direccion):
        # Verificar si hay una orden activa para el ticker
        ticker = stock['ticker']
        if ticker in self.active_orders and self.active_orders[ticker]:
            print(f"Ya hay una orden activa para {ticker}. Cancelando la anterior.")
            self.cancelar_orden(ticker)
        
        # Crear un contrato y una orden de mercado
        contrato = crear_contrato(stock)
        self.current_contract = contrato
        orden = create_orden_market(direccion, cantidad)

        
        # Obtener el siguiente OrderId y enviar la orden
        order_id = self.nextOrderId()
        self.placeOrder(order_id, contrato, orden)
        print(f"Orden enviada: {direccion} {cantidad} acciones de {ticker}")
        

        # Registrar la orden como activa
        self.active_orders[ticker] = True
        self.order_map[ticker] = order_id  # Guardar el orderId para este ticker
        self.pending_orders[ticker] = time.time()

    def nextValidId(self, orderId: int):
        
        self.order_id_counter = orderId
        print(f"Siguiente OrderId válido: {orderId}")
        # self.cancelar_ordenes_pendientes()  # Cancelar cualquier orden pendiente

    def nextOrderId(self):

        current_id = self.order_id_counter
        self.order_id_counter += 1
        return current_id

    def orderStatus(self, orderId, status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice):
        print(f"Estado de la orden ID {orderId}: {status}, llenada: {filled}, restante: {remaining}")
        
        if status == 'Filled':
            self.executed_price = avgFillPrice
            print(f"Orden ID {orderId} ejecutada a {avgFillPrice}")
            
            # Crear y enviar órdenes de stop loss y take profit
            take_profit_sl_orders = create_bracket_order_with_expiry(avgFillPrice, orderId, "BUY" if filled > 0 else "SELL", filled, 10, 10, 5)
            
            for order in take_profit_sl_orders:
                self.placeOrder(order.orderId, self.current_contract, order)
                print(f"Orden {order.orderId} de tipo {order.orderType} enviada con precio {order.lmtPrice if order.orderType == 'LMT' else order.auxPrice}")

        if status in ['Filled', 'Cancelled', 'Inactive']:
            for ticker in list(self.active_orders.keys()):
                if self.active_orders[ticker]:
                    self.active_orders[ticker] = False  # Marcar como no activa
                    self.order_map.pop(ticker, None)  # Eliminar el orderId del mapeo