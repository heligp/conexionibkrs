from ibapi.order import Order

def create_bracket_order(action, quantity, take_profit_price, stop_loss_price):
    """
    Crea un Bracket Order (orden con stop loss y take profit).
    
    Args:
    - action: "BUY" o "SELL"
    - quantity: cantidad de contratos o acciones
    - take_profit_price: precio objetivo para el take profit
    - stop_loss_price: precio objetivo para el stop loss
    
    Returns:
    - Una lista de 3 órdenes: la orden principal, el stop loss y el take profit
    """
    
    # 1. Crear la orden principal
    parent_order = Order()
    parent_order.orderId = 1  # Necesitas asignar dinámicamente el ID
    parent_order.action = action
    parent_order.orderType = "MKT"  # Orden de mercado
    parent_order.totalQuantity = quantity
    parent_order.transmit = False  # No enviar aún la orden, hasta que estén listas las secundarias

    # 2. Crear la orden de Take Profit
    take_profit_order = Order()
    take_profit_order.orderId = 2  # Necesitas asignar dinámicamente el ID
    take_profit_order.action = "SELL" if action == "BUY" else "BUY"
    take_profit_order.orderType = "LMT"  # Orden límite
    take_profit_order.totalQuantity = quantity
    take_profit_order.lmtPrice = take_profit_price
    take_profit_order.parentId = parent_order.orderId  # Vincular al padre
    take_profit_order.transmit = False  # No enviar aún la orden

    # 3. Crear la orden de Stop Loss
    stop_loss_order = Order()
    stop_loss_order.orderId = 3  # Necesitas asignar dinámicamente el ID
    stop_loss_order.action = "SELL" if action == "BUY" else "BUY"
    stop_loss_order.orderType = "STP"  # Orden de stop
    stop_loss_order.totalQuantity = quantity
    stop_loss_order.auxPrice = stop_loss_price  # Precio de activación del stop loss
    stop_loss_order.parentId = parent_order.orderId  # Vincular al padre
    stop_loss_order.transmit = True  # Ahora sí transmitir las tres órdenes (al transmitir la última)

    # Devuelve las 3 órdenes como parte del bracket
    return [parent_order, take_profit_order, stop_loss_order]