from ibapi.order import Order
from datetime import datetime, timedelta
from decimal import Decimal
from ibapi.order import Order


def create_orden_market(direction, quantity):
    orden_market = Order()
    orden_market.action = direction
    orden_market.orderType = "MKT"  # Orden Market
    orden_market.cashQty = quantity
    orden_market.totalQuantity = 0
    # orden_market.totalQuantity = quantity
    orden_market.tif = "IOC"

    
    return orden_market


def create_orden_market_con_bracket(orderid, direction, quantity, dif, price):
    orden_market = Order()
    orden_market.orderId = orderid
    orden_market.action = direction
    orden_market.orderType = "MKT"  # Orden Market
    orden_market.cashQty = quantity
    # orden_market.totalQuantity = round(quantity / price,8)
    orden_market.totalQuantity = ""
    # orden_market.totalQuantity = quantity
    orden_market.tif = "IOC"
    orden_market.transmit = False
    
    take_profit = Order()
    take_profit.orderId = orden_market.orderId + 1
    take_profit.action = "SELL" if direction == "BUY" else "BUY"
    take_profit.orderType = "LMT"
    take_profit.totalQuantity = round(quantity / price,8)
    # take_profit.cashQty = quantity
    # take_profit.totalQuantity = 0
    take_profit.lmtPrice = price + dif if direction == "BUY" else price - dif
    take_profit.parentId = orden_market.orderId
    take_profit.transmit = True 
    
    return [orden_market, take_profit]

def create_bracket_order_with_expiry(execution_price, parentOrderId, action, quantity, take_profit_diff=10, stop_loss_diff=10):
    """
    Crear una orden bracket con take profit, stop loss y tiempo límite de ejecución.
    
    :param execution_price: Precio al que se ejecutó la orden Market.
    :param parentOrderId: ID de la orden principal.
    :param action: 'BUY' o 'SELL'.
    :param quantity: Cantidad de la orden.
    :param take_profit_diff: Diferencia de precio para el take profit (+10 por defecto).
    :param stop_loss_diff: Diferencia de precio para el stop loss (-10 por defecto).
    :param window: Ventana de tiempo para la vigencia de la orden en horas.
    :return: Lista de órdenes bracket (take profit, stop loss y cierre al final del tiempo).
    """
    
    
    # Orden de take profit
    take_profit = Order()

    take_profit.orderId = parentOrderId + 1
    take_profit.action = "SELL" if action == "BUY" else "BUY"
    take_profit.orderType = "LMT"
    # take_profit.cashQty = 1000
    # take_profit.totalQuantity = 0
    take_profit.totalQuantity = quantity
    take_profit.lmtPrice = execution_price + take_profit_diff if action == "BUY" else execution_price - take_profit_diff
    take_profit.parentId = parentOrderId
    take_profit.transmit = True  # No transmitir hasta que las dos órdenes estén listas
    # take_profit.tif = "GTD"  # Good Till Date
    # take_profit.goodTillDate = tif_gtd

    # Orden de stop loss
    # stop_loss = Order()
    # stop_loss.orderId = parentOrderId + 2
    # stop_loss.action = "SELL" if action == "BUY" else "BUY"
    # stop_loss.orderType = "STP"
    # stop_loss.cashQty = 1000
    # stop_loss.totalQuantity = 0
    # # stop_loss.totalQuantity = quantity
    # stop_loss.auxPrice = execution_price - stop_loss_diff if action == "BUY" else execution_price + stop_loss_diff
    # stop_loss.parentId = parentOrderId
    # stop_loss.transmit = True  # No transmitir hasta que las dos órdenes estén listas
    # stop_loss.tif = "GTD"
    # stop_loss.goodTillDate = tif_gtd


    return [take_profit]