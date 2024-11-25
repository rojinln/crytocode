# Python Example for subscribing to a channel
import time
import json
import jwt
import hashlib
import os
import websocket
import threading
import http.client
from datetime import datetime, timedelta

# Derived from your Coinbase CDP API Key
# SIGNING_KEY: the signing key provided as a part of your API key. Also called the "SECRET KEY"
# API_KEY: the api key provided as a part of your API key. also called the "API KEY NAME"
API_KEY = "organizations/c9be9b6b-0caa-49c6-bda6-c0ee987b3b86/apiKeys/9641f55c-1e66-4224-ab27-13800a705502"
SIGNING_KEY = """-----BEGIN EC PRIVATE KEY-----
MHcCAQEEIA54arcFBPjPkDTCRZeeHiUQB2wpgTS4jVsGJ/Banl37oAoGCCqGSM49
AwEHoUQDQgAEeQoP6c1HlHv0ysydcDhxEyYW4ODG3RvIpR3rrevhu7FG1CMK0Hxx
59um/jAJpYG+1d+9mktCnLXn29tWhc425Q==
-----END EC PRIVATE KEY-----
"""


ALGORITHM = "ES256"

if not SIGNING_KEY or not API_KEY:
    raise ValueError("Missing mandatory environment variable(s)")

CHANNEL_NAMES = {
    "level2": "level2",
    "user": "user",
    "tickers": "ticker",
    "ticker_batch": "ticker_batch",
    "status": "status",
    "market_trades": "market_trades",
    "candles": "candles",
}

WS_API_URL = "wss://advanced-trade-ws.coinbase.com"

def sign_with_jwt(message, channel, products=[]):
    payload = {
        "iss": "coinbase-cloud",
        "nbf": int(time.time()),
        "exp": int(time.time()) + 120,
        "sub": API_KEY,
    }
    headers = {
        "kid": API_KEY,
        "nonce": hashlib.sha256(os.urandom(16)).hexdigest()
    }
    token = jwt.encode(payload, SIGNING_KEY, algorithm=ALGORITHM, headers=headers)
    message['jwt'] = token
    return message

def on_message(ws, message ):
    data = json.loads(message)
    with open("Output_USD-2.txt", "a") as f:
        f.write(json.dumps(data) + "\n")

def subscribe_to_products(ws, products, channel_name):
    message = {
        "type": "subscribe",
        "channel": channel_name,
        "product_ids": products
    }
    signed_message = sign_with_jwt(message, channel_name, products)
    ws.send(json.dumps(signed_message))

def unsubscribe_to_products(ws, products, channel_name):
    message = {
        "type": "unsubscribe",
        "channel": channel_name,
        "product_ids": products
    }
    signed_message = sign_with_jwt(message, channel_name, products)
    ws.send(json.dumps(signed_message))

def on_open(ws):
    conn = http.client.HTTPSConnection("api.exchange.coinbase.com")
    payload = ''
    headers = {
    'Content-Type': 'application/json'
    }
    conn.request("GET", "/currencies", payload, headers)
    res = conn.getresponse()
    data = res.read()
    parsed_data = json.loads(data)

    ids = [str(item['id'] + '-USD') for item in parsed_data] 

    with open('names-usd.txt', 'r') as f:
        products2 = [
            line.strip().replace('"', '').replace(',', '') for line in f.readlines() if line.strip()
        ]
    #print(products2)
    #products = str(products)
    #products = ids[0]
    #products = ["00-USD"]
    products = list(set(products2[0:10]))
    print(products)
    print(products[0])
    subscribe_to_products(ws, [products[0]], CHANNEL_NAMES["level2"])

def start_websocket():
    ws = websocket.WebSocketApp(WS_API_URL, on_open=on_open, on_message=on_message)
    ws.run_forever()

def main():
    ws_thread = threading.Thread(target=start_websocket)
    ws_thread.start()

    sent_unsub = False
    start_time = datetime.utcnow()

    try:
        while True:
            if (datetime.utcnow() - start_time).total_seconds() > 5 and not sent_unsub:
                # Unsubscribe after 5 seconds
                ws = websocket.create_connection(WS_API_URL)
                unsubscribe_to_products(ws, ["BTC-USD"], CHANNEL_NAMES["level2"])
                ws.close()
                sent_unsub = True
            time.sleep(1)
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    main()
