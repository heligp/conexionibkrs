from ibapi.order import Order  # Importa la clase Order para crear órdenes de mercado
from datetime import datetime, timedelta  # Importa funciones de manejo de fechas
from decimal import Decimal  # Importa el tipo Decimal para manejar valores precisos
from ibapi.order import Order  # Repetido, no es necesario

# Función para crear una orden de mercado con órdenes asociadas (bracket orders) de take profit y stop loss
def create_orden_market_con_bracket(orderid, direction, quantity, dif, price):
    """
    Crea una orden de mercado principal con órdenes adicionales de take profit y stop loss (bracket order).
    """

    # Orden principal de tipo Market (orden de compra o venta inmediata)
    orden_market = Order()  # Instancia una nueva orden
    orden_market.orderId = orderid  # Asigna el ID único de la orden
    orden_market.action = direction  # Define la acción (compra o venta) basada en "direction" (ej. "BUY" o "SELL")
    orden_market.orderType = "MKT"  # Define el tipo de orden como Market (MKT)
    orden_market.cashQty = quantity  # Define la cantidad en términos de dinero en efectivo (cash quantity)
    # orden_market.totalQuantity = round(quantity / price,8)  # Se puede usar para definir la cantidad total, pero está comentado
    orden_market.totalQuantity = ""  # Aquí no se define explícitamente la cantidad total, posiblemente se calculará en otro momento
    orden_market.tif = "IOC"  # Time In Force (TIF) define que la orden debe ejecutarse inmediatamente o cancelarse (Immediate or Cancel)
    orden_market.transmit = False  # Indica que la orden no se transmitirá aún, ya que primero se deben configurar las órdenes de bracket (take profit y stop loss)

    # Orden Take Profit: se ejecuta cuando se alcanza un precio objetivo favorable
    take_profit = Order()  # Instancia una nueva orden para Take Profit
    take_profit.orderId = orden_market.orderId + 1  # El ID de la orden de Take Profit es consecutivo al de la orden principal
    take_profit.action = "SELL" if direction == "BUY" else "BUY"  # Si la orden principal es una compra, la orden de Take Profit será de venta y viceversa
    take_profit.orderType = "LMT"  # Define el tipo de orden como Limit (LMT), es decir, se ejecuta a un precio límite o mejor
    take_profit.totalQuantity = round(quantity / price, 8)  # Calcula la cantidad total basada en el precio
    # take_profit.cashQty = quantity  # Esta línea está comentada, pero podría usarse para definir la cantidad en efectivo
    take_profit.lmtPrice = price + dif if direction == "BUY" else price - dif  # El precio límite será el precio actual más/menos la diferencia ("dif")
    take_profit.parentId = orden_market.orderId  # Indica que esta orden está vinculada a la orden principal (bracket order)
    take_profit.transmit = False  # No transmitir aún, ya que falta configurar el Stop Loss

    # Orden Stop Loss: se ejecuta cuando el precio va en contra de la posición para limitar pérdidas
    stop_loss = Order()  # Instancia una nueva orden para Stop Loss
    stop_loss.orderId = orden_market.orderId + 2  # El ID de la orden de Stop Loss es consecutivo al de Take Profit
    stop_loss.action = "SELL" if direction == "BUY" else "BUY"  # Si la orden principal es una compra, el Stop Loss será una orden de venta, y viceversa
    stop_loss.orderType = "STP"  # Define el tipo de orden como Stop (STP), que se activa cuando se alcanza un precio de activación
    stop_loss.totalQuantity = 0  # Define la cantidad total de la orden, puede que se defina después
    stop_loss.auxPrice = price - price - dif if direction == "BUY" else price + dif
    # El precio auxiliar (auxPrice) para activar el Stop Loss se calcula restando (para compras) o sumando (para ventas) un valor diferencial al precio de ejecución.
    stop_loss.parentId = orden_market.orderId  # Indica que esta orden está vinculada a la orden principal (bracket order)
    stop_loss.transmit = True  # Esta vez transmitimos la orden, ya que todas las órdenes están configuradas correctamente

    # Devuelve las tres órdenes: la principal, la de Take Profit, y la de Stop Loss
    return [orden_market, take_profit, stop_loss]
