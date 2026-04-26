from django.shortcuts import render
from .models import MessaggioDato
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from django.shortcuts import redirect
import threading
from .management.commands import ascolta_zmq # Importiamo il modulo del comando
import socket
import json
from django.contrib import messages

zmq_thread = None

custom_viridis = [
    [0, 'rgb(255, 255, 255)'],  # 0% è Bianco
    [0.01, 'rgb(68, 1, 84)'],   # 1% inizia il viola di Viridis
    [1, 'rgb(253, 231, 37)']    # 100% è il giallo di Viridis
]

def toggle_zmq(request):
    global zmq_thread
    azione = request.GET.get('azione')

    if azione == "start":
        if zmq_thread is None or not zmq_thread.is_alive():
            zmq_thread = threading.Thread(target=ascolta_zmq.start_listening, daemon=True)
            zmq_thread.start()

    elif azione == "stop":
        ascolta_zmq.running = False

        zmq_thread = None

    return redirect('home')

def reset_db(request):
    MessaggioDato.objects.all().delete()
    return redirect('home') # Torna alla pagina principale

def home_plot(request):
    canale = int(request.GET.get('canale', 1))

    queryset = MessaggioDato.objects.filter(canale=canale).order_by('id')
    x = [d.ADC for d in queryset]
    y = [d.ToT*0.4 for d in queryset]

    plot_html = None
    if x:
        fig = make_subplots(rows=1, cols=2, subplot_titles=("Charge spectrum", "Matrix ToT vs Charge"))

        fig.add_trace(
            go.Histogram(x=x, nbinsx=2000, name="Spettro", marker_color='#3498db'),
            row=1, col=1
        )
        fig.update_xaxes(range=[0, 4096], row=1, col=1)
        fig.update_yaxes(row=1, col=1, type="log")

        fig.add_trace(
            go.Histogram2d(x=x, y=y, nbinsx=150, nbinsy=150, colorscale=custom_viridis, name="Densità"),
            row=1, col=2
        )
        fig.update_layout(
            height=500,
            showlegend=False,
            template="plotly_white",
            margin=dict(l=20, r=20, t=50, b=20),
        )

        # Convertiamo il grafico in un div HTML
        plot_html = fig.to_html(full_html=False, include_plotlyjs='cdn',config={'responsive': True, 'displaylogo': False})

    # Determina stato worker (come prima)
    stato_attuale = "Attivo" if (zmq_thread and zmq_thread.is_alive()) else "Spento"

    return render(request, 'monitor/home.html', {
        'plot_html': plot_html,
        'canale_attuale': canale,
        'canali': range(1, 20),
        'stato_worker': stato_attuale
    })

def send_command(request):
    if request.method == "POST":
        ip_scheda = request.POST.get('device_ip')
        action = request.POST.get('action')
        address = int(request.POST.get('address'))
        valore_raw = int(request.POST.get('valore'))
        request.session['saved_ip'] = ip_scheda

        try:
            payload = {
                "command": "write" if action == 'send' else "read",
                "args": {
                    "address": address,
                    "value": valore_raw
                }
            }

            with socket.create_connection((ip_scheda, 9000), timeout=5) as sock:
                with sock.makefile('rwb') as file:
                    file.write((json.dumps(payload) + '\n').encode('utf-8'))
                    file.flush()

                    line = file.readline().decode('utf-8').strip()

            messages.success(request, f"Register value: {line}")

        except (socket.timeout, socket.error) as e:
            messages.error(request, f"Connection error: {e}")
            return redirect('/')

        except ValueError:
            messages.error(request, "Value or address not valid.")
            return redirect('/')

        except Exception as e:
            messages.error(request, f"Errore inatteso: {e}")
            return redirect('/')

    return redirect('/')