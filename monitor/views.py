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
from django.db.models import Count, F, IntegerField
from django.db.models.functions import Cast

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

    adc_counts = MessaggioDato.objects.filter(canale=canale).values("ADC").annotate(count=Count("id")).order_by("ADC")
    x_hist = [row["ADC"] for row in adc_counts]
    y_hist = [row["count"] for row in adc_counts]

    adc_bin_size = 4096 / 150
    tot_bin_size = 4

    density_counts = (
        MessaggioDato.objects
        .filter(canale=canale)
        .annotate(
            adc_bin=Cast(F("ADC") / adc_bin_size, IntegerField()),
            tot_bin=Cast(F("ToT") / tot_bin_size, IntegerField()),
        )
        .values("adc_bin", "tot_bin")
        .annotate(count=Count("id"))
        .order_by("adc_bin", "tot_bin")
    )

    x_2d = []
    y_2d = []
    z_2d = []

    for row in density_counts:
        x_2d.append((row["adc_bin"] + 0.5) * adc_bin_size)
        y_2d.append((row["tot_bin"] + 0.5) * tot_bin_size * 0.25)
        z_2d.append(row["count"])

    plot_html = None
    if x_hist:
        fig = make_subplots(rows=1, cols=2, subplot_titles=("Charge spectrum", "Matrix ToT vs Charge"))

        fig.add_trace(
            go.Scatter(
                x=x_hist,
                y=y_hist,
                mode="lines",
                line=dict(color="#1f77b4", width=1.5),
                line_shape="hv",
                fill="tozeroy",
                fillcolor="rgb(31, 119, 180)",
                name="Spettro"
            ),
            row=1, col=1
        )
        fig.update_xaxes(title_text="ADC", range=[0, 4096], row=1, col=1)
        fig.update_yaxes(row=1, col=1, type="log")

        fig.add_trace(
            go.Scatter(
                x=x_2d,
                y=y_2d,
                mode="markers",
                marker=dict(
                    size=6,
                    color=z_2d,
                    colorscale=custom_viridis,
                    colorbar=dict(title="Counts"),
                    showscale=True
                ),
                name="Densità"
            ),
            row=1, col=2
        )
        fig.update_xaxes(title_text="ADC", row=1, col=2)
        fig.update_yaxes(title_text="ToT", row=1, col=2)
        fig.update_layout(
            height=500,
            showlegend=False,
            template="plotly_white",
            margin=dict(l=20, r=20, t=50, b=20)
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
        request.session['saved_ip'] = ip_scheda

        try:
            args = {
                "address": address
            }

            if action == 'send':
                valore_raw = request.POST.get('valore')

                if valore_raw is None or valore_raw == "":
                    messages.error(request, "Value is required for write.")
                    return redirect('/')

                args["value"] = int(valore_raw)

            payload = {
                "command": "write" if action == 'send' else "read",
                "args": args
            }

            with socket.create_connection((ip_scheda, 9000), timeout=5) as sock:
                with sock.makefile('rwb') as file:
                    file.write((json.dumps(payload) + '\n').encode('utf-8'))
                    file.flush()

                    line = file.readline().decode('utf-8').strip()

            response = json.loads(line)
            value = int(response["value"])
            messages.success(request, f"Register value: 0x{value:08X}")

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
