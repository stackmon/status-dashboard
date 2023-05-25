import websocket

def on_open(ws):
    print('WebSocket connected')

def on_message(ws, message):
    print('Received message:', message)

def on_close(ws):
    print('WebSocket disconnected')

if __name__ == '__main__':
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp('ws://localhost:5000/', on_open=on_open, on_message=on_message, on_close=on_close)
    ws.run_forever()
