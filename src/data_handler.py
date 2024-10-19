from features import calcular_features
import pandas as pd

class DataHandler:
    def __init__(self, 
                 ticker,
                 threshold_bar,
                 threshold_features,
                 connection,
                 model,
                 scaler):
        self.ticker = ticker  # Ticker (símbolo) asociado
        self.ticks = []
        self.volumen_acumulado = 0
        self.barras = []
        self.threshold_bar = threshold_bar
        self.threshold_features = threshold_features
        self.connection = connection
        self.model = model
        self.scaler = scaler

    def add_tick(self, price):
        self.ticks.append(price)
        self.check_if_bar_can_be_generated()

    def add_volume(self, volume):
        self.volumen_acumulado += (volume)
        self.check_if_bar_can_be_generated()

    def check_if_bar_can_be_generated(self):
        # Si el volumen acumulado es mayor o igual a "threshold_bar", generar una barra OHLC
        if self.volumen_acumulado >= self.threshold_bar:
            self.generar_barra_ohlc()


    def generar_barra_ohlc(self):
        if self.ticks:
            open_price = self.ticks[0]
            high_price = max(self.ticks)
            low_price = min(self.ticks)
            close_price = self.ticks[-1]

            # Crear una barra OHLC
            barra = {
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': self.volumen_acumulado
            }
            self.barras.append(barra)
            self.ticks.clear()  # Reiniciar los ticks
            self.volumen_acumulado = 0  # Reiniciar el volumen

            print(f"Barra generada para {self.ticker['ticker']}: {barra}")

            # Si ya tienes "threshold_features" barras, podrías generar los features y hacer predicciones
            if len(self.barras) > self.threshold_features:
                self.crear_features_y_predecir()

    
    def crear_features_y_predecir(self):

        # Aquí puedes calcular los features basados en las barras OHLC
        df_barras = pd.DataFrame(self.barras[-self.threshold_features:])  # Seleccionar las últimas "threshold_features" barras
        features = calcular_features(df_barras, self.threshold_features)
        df_barras = pd.DataFrame(features).iloc[:,-1]

        # Aquí haces el escalado y predicciones con el modelo cargado
        features_scaled = self.scaler.transform([df_barras])
        prediccion = self.model.predict(features_scaled)

        print(f"Features creados para {self.ticker['ticker']}: {features_scaled}")
        print("PREDICCION:", prediccion)

        # CAMBIAR CON LA PREDICCIÓN DEL MODELO DE SIZE!!!
        cantidad = 1

        # Aquí decides si enviar una orden en función de los features
        self.evaluar_y_enviar_orden(prediccion, cantidad)

    def evaluar_y_enviar_orden(self, prediccion, cantidad):
        # Implementa tu lógica para decidir si enviar una orden
        # Ejemplo simple: si el primer feature es positivo, compra "cantidad" acciones, si es negativo, vende "cantidad" acciones
        if prediccion == 1:
            self.connection.enviar_orden(self.ticker, cantidad, 'BUY', 500)
        elif prediccion == -1:
            self.connection.enviar_orden(self.ticker, cantidad, 'SELL', 500)
        else:
            return

        
