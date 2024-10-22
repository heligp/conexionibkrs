def cancelar_ordenes_pendientes(self):
    print("Cancelando todas las órdenes activas al iniciar.")
    self.reqGlobalCancel()