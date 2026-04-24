import struct
import zmq
from monitor.models import MessaggioDato


def start_listening():

    global running
    running = True
    context = zmq.Context()

    frontend = context.socket(zmq.ROUTER)
    frontend.bind("tcp://*:5555")

    while running:
        try:
            message = frontend.recv_multipart()
            oggetti_da_salvare = []

            tmp_canale = tmp_tot = None

            for part in message:
                if len(part) < 4: continue

                num_words = len(part) // 4
                words = struct.unpack(f'>{num_words}I', part[:num_words * 4])

                for word in words:
                    header = word & 0xC0000000

                    if header == 0x80000000:  # HEAD
                        tmp_canale = ((word >> 22) & 0x1F) + 1

                    elif header == 0x00000000:  # PAYL
                        start, coarse, stop = (word >> 11) & 0xF, (word >> 4) & 0x7F, word & 0xF
                        tmp_tot = (coarse << 4) + start - stop

                    elif header == 0x40000000:
                        continue

                    elif header == 0xC0000000:  # TAIL
                        if tmp_canale is not None:
                            adc = (word >> 4) & 0xFFF
                            oggetti_da_salvare.append(
                                MessaggioDato(canale=tmp_canale, ToT=tmp_tot, ADC=adc)
                            )
                            tmp_canale = tmp_tot = None  # Reset

            if oggetti_da_salvare:
                MessaggioDato.objects.bulk_create(oggetti_da_salvare)

        except zmq.Again:
            continue