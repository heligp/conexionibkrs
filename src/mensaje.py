import requests

def send_message(stock, cantidad, direccion, dif): ###Mensaje de Telegram --- No importante
    bot_token = "7610026985:AAFvckS8dd2WqkxbxlBoWSbQpWKd8MQupHw"
    chat_ID = "-1002279952392"
    message = f'Señal para {stock}, {direccion} {cantidad} acciones con ventana de {dif}'
    send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + chat_ID + '&text=' + message
    response = requests.get(send_text)
    return [response, message]