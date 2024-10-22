import joblib

SCALER_PATH_BTC = 'scaler_activo.pkl'
MODEL_PATH_BTC = 'modelo_activo.pkl'

scaler_btc = joblib.load(SCALER_PATH_BTC)
model_btc = joblib.load(MODEL_PATH_BTC)