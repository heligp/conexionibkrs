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
    orden_market.tif = "IOC"
    return orden_market

def create_bracket_order_with_expiry(execution_price, parentOrderId, action, quantity, take_profit_diff=10, stop_loss_diff=10, window=5):
    """
    Crear una orden bracket con take profit, stop loss y tiempo límite de ejecución.
    
    :param execution_price: Precio al que se ejecutó la orden Market.
    :param parentOrderId: ID de la orden principal.
    :param action: 'BUY' o 'SELL'.
    :param quantity: Cantidad de la orden.
    :param take_profit_diff: Diferencia de precio para el take profit (+10 por defecto).
    :param stop_loss_diff: Diferencia de precio para el stop loss (-10 por defecto).
    :param window: Ventana de tiempo para la vigencia de la orden en horas.
    :return: Lista de órdenes bracket (take profit y stop loss).
    """
    
    # Calcular la fecha y hora de expiración (5 horas desde ahora)
    expiry_time = datetime.now() + timedelta(hours=window)
    tif_gtd = expiry_time.strftime("%Y%m%d %H:%M:%S")
    
    # Orden de take profit
    take_profit = Order()
    take_profit.orderId = parentOrderId + 1
    take_profit.action = "SELL" if action == "BUY" else "BUY"
    take_profit.orderType = "LMT"
    take_profit.totalQuantity = quantity
    take_profit.lmtPrice = execution_price + take_profit_diff if action == "BUY" else execution_price - take_profit_diff
    take_profit.parentId = parentOrderId
    take_profit.transmit = False  # No transmitir hasta que las dos órdenes estén listas
    take_profit.tif = "GTD"  # Good Till Date
    take_profit.goodTillDate = tif_gtd

    # Orden de stop loss
    stop_loss = Order()
    stop_loss.orderId = parentOrderId + 2
    stop_loss.action = "SELL" if action == "BUY" else "BUY"
    stop_loss.orderType = "STP"
    stop_loss.totalQuantity = quantity
    stop_loss.auxPrice = execution_price - stop_loss_diff if action == "BUY" else execution_price + stop_loss_diff
    stop_loss.parentId = parentOrderId
    stop_loss.transmit = True  # Transmitir todas las órdenes en este punto
    stop_loss.tif = "GTD"  # Good Till Date
    stop_loss.goodTillDate = tif_gtd

    return [take_profit, stop_loss]