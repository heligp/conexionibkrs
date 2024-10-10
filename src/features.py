# Cálculo de features
def calcular_sma(df, periodo, barRef = 'close'):
    sma = df[barRef].rolling(window=periodo).mean()
    return sma

def calcular_rsi(df, periodo, barRef = 'close'):
    delta = df[barRef].diff(1)
    gain = delta.apply(lambda x: x if x > 0 else 0)
    loss = -delta.apply(lambda x: x if x < 0 else 0)

    avg_gain = gain.rolling(window=periodo).mean()
    avg_loss = loss.rolling(window=periodo).mean()

    rs = avg_gain / abs(avg_loss)
    rsi = 100 - (100/(1 + rs))

    return rsi

def calcular_stochastic(df, periodo, barRef = 'close'):
    low = df[barRef].rolling(window=periodo).min()
    high = df[barRef].rolling(window=periodo).max()

    stochastic = 100 * ((df[barRef] - low) / (high - low))
    return stochastic


# Función para calcular los features (ajusta según tu lógica)
def calcular_features(df_barras, periodo):
    sma = calcular_sma(df_barras, periodo)
    rsi = calcular_rsi(df_barras, periodo)
    stochastic = calcular_stochastic(df_barras, periodo)
    return [sma, rsi, stochastic]