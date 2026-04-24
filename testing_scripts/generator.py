import zmq
import time
import random

context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://*:5555")

print("Inviando dati multi-canale...")
while True:
    dati = {
        "canale": 1,
        "ADC": random.uniform(0, 4096),
        "ToT": random.uniform(10, 500)
    }
    socket.send_json(dati)
    time.sleep(0.1) # Invio più rapido per popolare i vari canali