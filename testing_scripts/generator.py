import zmq
import time
import random

context = zmq.Context()
socket = context.socket(zmq.PUSH)
socket.connect("tcp://172.16.11.194:5555")

print("Inviando dati multi-canale...")
while True:
    dati = {
        "canale": 1,
        "ADC": random.uniform(0, 4096),
        "ToT": random.uniform(10, 120)
    }
    socket.send_json(dati)
    time.sleep(0.5)
    print(f'Inviato: {dati}')