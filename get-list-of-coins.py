import http.client
import json
import os

conn = http.client.HTTPSConnection("api.exchange.coinbase.com")
payload = ''
headers = {
  'Content-Type': 'application/json'
}
conn.request("GET", "/currencies", payload, headers)
res = conn.getresponse()
data = res.read()
print(data.decode("utf-8"))

parsed_data = json.loads(data)

with open("list.txt", "a") as f:
    f.write(json.dumps(parsed_data, indent=4) + "\n") 