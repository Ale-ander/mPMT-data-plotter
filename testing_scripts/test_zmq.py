import zmq
import struct

# Costanti per il parsing
MASK_HEADER = 0xC0000000  # Primi 2 bit (1100...)
HEAD = 0x80000000  # 10
PAYL = 0x00000000  # 00
EXTR = 0x40000000  # 01
TAIL = 0xC0000000  # 11

MessaggioDato = {}

running = True
context = zmq.Context()

frontend = context.socket(zmq.ROUTER)
frontend.bind("tcp://*:5555")

oggetti_da_salvare = []
while running:
    try:
        message = frontend.recv_multipart()

        for part in message:
            # Saltiamo i frame di controllo (tipo b'1')
            if len(part) < 4:
                continue

            # Calcoliamo quante parole da 4 byte ci sono
            num_words = len(part) // 4

            # OTTIMIZZAZIONE: 'I' è unsigned int 32 bit, '>' è Big Endian
            # Questa singola riga sostituisce il tuo loop 'for b in part'
            words = struct.unpack(f'>{num_words}I', part[:num_words*4])

            # Ora hai una lista di interi (words) e puoi processarli
            for word in words:
                header_type = word & MASK_HEADER

                if header_type == HEAD:
                    channel = (word >> 22) & 0x1F

                elif header_type == PAYL:
                    tdc_start = (word >> 11) & 0xF
                    tdc_coarse = (word >> 4) & 0x7F
                    tdc_stop = word & 0xF
                    ToT = (tdc_coarse << 4) + tdc_start - tdc_stop

                elif header_type == EXTR:
                    continue

                elif header_type == TAIL:
                    adc = (word >> 4) & 0xFFF
                    MessaggioDato = {'canale':channel+1,
                        'ToT':ToT,  # Salviamo il ToT qui
                        'ADC':adc  # Salviamo l'ADC qui
                    }
                    oggetti_da_salvare.append(MessaggioDato)

                print(oggetti_da_salvare)

    except zmq.Again:
        continue