from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from contract import crear_contrato
from order import create_bracket_order_with_expiry, create_orden_market, create_orden_market_con_bracket
from ibapi.common import TickAttribLast, TickerId, TickAttrib
from ibapi.ticktype import TickType
from ibapi.utils import floatMaxString, decimalMaxString, intMaxString
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
        self.counter_vol = 0
        self.vol_ref = 0
        self.brackets_pendientes = {}  # Estado para rastrear brackets pendientes por ticker
        self.order_brackets_map = {}
        self.parentIds = []

    def tickPrice(self, reqId: TickerId, tickType: TickType, price: float, attrib: TickAttrib):
        if tickType == 4:
            if reqId in self.data_handlers:
                self.data_handlers[reqId].add_tick(price)
                self.data_handlers[reqId].last_tick = price

    def tickSize(self, reqId: TickerId, tickType: TickType, size: Decimal):
        if tickType == 8:
            if reqId in self.data_handlers:
                if self.counter_vol == 0:
                    self.vol_ref = size
                else: 
                    self.data_handlers[reqId].add_volume(size - self.vol_ref)
                    # print("TickSize. TickerId:", reqId, "TickType:", tickType, "Size: ", decimalMaxString(size - self.vol_ref))
                
                self.vol_ref = size
                self.counter_vol += 1
                print('tick')

    def cancelar_ordenes_pendientes(self):
        print("Cancelando todas las órdenes activas al iniciar.")
        oc = OrderCancel()  # Crear un objeto de cancelación
        self.reqGlobalCancel(oc)  # Cancela todas las órdenes activas en la cuenta
        self.brackets_pendientes = {}  # Restablecer estado para todos los tickers

    def cancelar_orden(self, ticker, oc):
        if ticker in self.active_orders and self.active_orders[ticker]:
            order_id = self.order_map.get(ticker)  # Obtener el orderId del ticker
            if order_id is not None:
                print(f"Cancelando la orden activa para {ticker}.")
                try:
                    self.cancelOrder(order_id, oc)  # Intentar cancelar la orden con el objeto oc
                except Exception as e:
                    print(f"Error al cancelar la orden ID {order_id} para {ticker}: {str(e)}")
                self.active_orders[ticker] = False  # Marcar como no activa
            else:
                print(f"No se encontró orderId para {ticker}.")
        else:
            print(f"No hay orden activa para {ticker} que cancelar.")

    def enviar_orden(self, stock, cantidad, direccion, dif):
        ticker = stock['ticker']
        oc = OrderCancel()  # Crear un objeto de cancelación para uso posterior

        # Bloquear el envío de nuevas órdenes si hay brackets pendientes para este ticker
        if ticker in self.brackets_pendientes and self.brackets_pendientes[ticker]:
            print(f"No se puede enviar una nueva orden para {ticker}: hay órdenes de bracket pendientes.")
            return

        if ticker in self.active_orders and self.active_orders[ticker]:
            print(f"Ya hay una orden activa para {ticker}")
            if time.time() - self.pending_orders[ticker] > 10:
                print(f"La orden está hace más de 10 segundos, cancelando")
                self.cancelar_orden(ticker, oc)
                return
            else:
                print(f"La orden está hace menos de 10 segundos, omitir la actual")
                return
        
        # contrato = crear_contrato(stock)
        # self.current_contract = contrato
        # orden = create_orden_market(direccion, cantidad,)

        # # Obtener el siguiente OrderId y enviar la orden
        # order_id = self.nextOrderId()
        # self.placeOrder(order_id, contrato, orden)
        # print(f"Orden enviada: {direccion} {cantidad} acciones de {ticker}")
        

        # # Registrar la orden como activa
        # self.active_orders[ticker] = True
        # self.order_map[ticker] = order_id  # Guardar el orderId para este ticker
        # self.pending_orders[ticker] = time.time()
        
        # print(self.data_handlers.items())
        # print(stock['ticker'])
        # for key,val in self.data_handlers.items():
        #     print(key,val,val.ticker)

        reqId = [key for key, val in self.data_handlers.items() if val.ticker['ticker'] == stock['ticker']][0]
        ultimo_tick = self.data_handlers[reqId].last_tick
        
        contrato = crear_contrato(stock)
        self.current_contract = contrato
        order_id = self.nextOrderId()
        ordenes = create_orden_market_con_bracket(order_id,direccion, cantidad, dif, ultimo_tick)

        # Obtener el siguiente OrderId y enviar la orden
        for orden in ordenes:
            self.placeOrder(orden.orderId, contrato, orden)
            print(orden.orderId)
            self.nextOrderId()
            print(f"Orden enviada: {direccion} {cantidad} acciones de {ticker}")
        

        # Registrar la orden como activa
        self.active_orders[ticker] = True
        self.order_map[ticker] = order_id  # Guardar el orderId para este ticker
        self.pending_orders[ticker] = time.time()
        



    def nextValidId(self, orderId: int):
        self.order_id_counter = orderId
        print(f"Siguiente OrderId válido: {orderId}")

    def nextOrderId(self):
        current_id = self.order_id_counter
        self.order_id_counter += 1
        return current_id

    def orderStatus(self, orderId, status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice):
        print(f"Estado de la orden ID {orderId}: {status}, llenada: {filled}, restante: {remaining}")



        if status in ['Cancelled','Inactive']:
            return
        
        if status in ['Filled'] and remaining <= 0.00000001:
            if orderId not in self.parentIds:
                if parentId == 0:
                    self.parentIds.append(orderId)
                    # try:
                    #     take_profit_sl_orders = create_bracket_order_with_expiry(avgFillPrice, int(orderId),  
                    #                                                              "BUY" if filled > 0 else "SELL", filled, 20, 20)
                    #     for order in take_profit_sl_orders:
                    #         self.placeOrder(order.orderId, self.current_contract, order)
                    #     print(f"Orden {order.orderId} de tipo {order.orderType} enviada con precio {order.lmtPrice if order.orderType == 'LMT' else order.auxPrice}")
                    # except Exception as e:
                    #     print(f"Error al enviar la orden de bracket {order.orderId} para {orderId}: {str(e)}")
                    self.brackets_pendientes[self.current_contract.symbol] = True

                else:
                    self.brackets_pendientes[self.current_contract.symbol] = False  # Marca como no pendiente



        # Información en tiempo real
        # def tickByTickAllLast(self, reqId: int, tickType: int, time: int, price: float, size: Decimal, tickAtrribLast: TickAttribLast, exchange: str, specialConditions: str):
        #     print(f"ReqId: {reqId}, Time: {time}, Price: {price}, Size: {size}")
        #     if reqId in self.data_handlers:
        #         self.data_handlers[reqId].add_tick(price)
        #         self.data_handlers[reqId].add_volume(size)
        