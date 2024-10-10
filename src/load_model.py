import joblib

SCALER_PATH_BTC = 'scaler.pkl'
MODEL_PATH_BTC = 'modelo.pkl'

scaler_btc = joblib.load(SCALER_PATH_BTC)
model_btc = joblib.load(MODEL_PATH_BTC)