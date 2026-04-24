import socket
import json

REGISTRY_MAP = {
    "turn_on":        0,
    "enable":         1,
}

channel = 1
ip_scheda = '192.168.1.8'
comando_id = 'turn_on'
valore_raw = 1

sock = socket.create_connection((ip_scheda, 9000), timeout=5)
file = sock.makefile('rwb')

if comando_id in REGISTRY_MAP:
    address = REGISTRY_MAP[comando_id]

    try:
        final_value = int(valore_raw) * (2**(channel-1))

        payload = {
            "command": "write",
            "args": {
                "address": address,
                "value": final_value
            }
        }

        file.write((json.dumps(payload) + '\n').encode('utf-8'))
        file.flush()
        line = file.readline()
        resp = json.loads(line.decode('utf-8'))
        print(resp)
    except ValueError:
        print('errore')