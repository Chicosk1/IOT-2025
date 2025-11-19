from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime    import datetime
import threading
import json
import os
import RPi.GPIO as gpio
import time     as delay

# -----------------------------
# CONFIGURAÇÕES DE HARDWARE
# -----------------------------

gpio.setmode(gpio.BOARD)
gpio.setwarnings(False)

pin_sensor_gas = 7      # Ajustar conforme ligação
ledVermelho    = 11     # Ajustar conforme ligação
ledVerde       = 12     # Ajustar conforme ligação

gpio.setup(pin_sensor_gas, gpio.IN)
gpio.setup(ledVermelho   , gpio.OUT)
gpio.setup(ledVerde      , gpio.OUT)

# -----------------------------
# VARIÁVEIS GLOBAIS DO DASHBOARD
# -----------------------------

gas_level    = 0.0
status_text  = "Aguardando leitura"
status_level = "normal"
last_update  = ""

min_level     = None
max_level     = None
avg_level     = 0.0
samples_count = 0

lock = threading.Lock()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def ler_sensor_gas():
    valor_digital = gpio.input(pin_sensor_gas)
    if valor_digital == 1:
        nivel = 0.0
    else:
        nivel = 100.0
    return nivel


def atualiza_leds(nivel):
    if nivel < 40:
        gpio.output(ledVerde   , True)
        gpio.output(ledVermelho, False)
    elif nivel < 70:
        gpio.output(ledVerde   , False)
        gpio.output(ledVermelho, False)
    else:
        gpio.output(ledVerde   , False)
        gpio.output(ledVermelho, True)


def loop_sensor():
    global gas_level, status_text, status_level, last_update
    global min_level, max_level  , avg_level   , samples_count

    try:
        while True:
            nivel = ler_sensor_gas()
            agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

            if nivel < 40:
                st_text  = "Normal"
                st_level = "normal"
            elif nivel < 70:
                st_text  = "Atenção"
                st_level = "atencao"
            else:
                st_text  = "Perigo"
                st_level = "perigo"

            atualiza_leds(nivel)

            with lock:
                gas_level    = float(nivel)
                status_text  = st_text
                status_level = st_level
                last_update  = agora

                if samples_count == 0:
                    min_level = nivel
                    max_level = nivel
                    avg_level = nivel
                    samples_count = 1
                else:
                    samples_count += 1
                    if nivel < min_level:
                        min_level = nivel
                    if nivel > max_level:
                        max_level = nivel
                    avg_level = ((avg_level * (samples_count - 1)) + nivel) / samples_count

            print(f"[{agora}] Nível de gás: {nivel:.1f} | Status: {st_text}")
            delay.sleep(2)
    except KeyboardInterrupt:
        pass


class DashboardHandler(BaseHTTPRequestHandler):
    def _set_headers(self, content_type="text/html; charset=utf-8"):
        self.send_response(200)
        self.send_header("Content-type", content_type)
        self.end_headers()

    def do_GET(self):
        if self.path in ["/", "/index.html"]:
            try:
                file_path = os.path.join(BASE_DIR, "dashboard.html")
                with open(file_path, "rb") as f:
                    conteudo = f.read()
                self._set_headers("text/html; charset=utf-8")
                self.wfile.write(conteudo)
            except FileNotFoundError:
                self.send_error(404, "dashboard.html não encontrado")

        elif self.path == "/data":
            with lock:
                dados = {
                    "gas_level": gas_level,
                    "status": status_text,
                    "status_level": status_level,
                    "last_update": last_update,
                    "min_level": min_level if min_level is not None else 0.0,
                    "max_level": max_level if max_level is not None else 0.0,
                    "avg_level": avg_level,
                    "samples_count": samples_count,
                    "thresholds": {
                        "normal_max": 40,
                        "atencao_max": 70
                    }
                }

            resposta = json.dumps(dados).encode("utf-8")
            self._set_headers("application/json; charset=utf-8")
            self.wfile.write(resposta)

        elif self.path == "/style.css":
            file_path = os.path.join(BASE_DIR, "style.css")
            if os.path.isfile(file_path):
                try:
                    with open(file_path, "rb") as f:
                        conteudo = f.read()
                    self._set_headers("text/css; charset=utf-8")
                    self.wfile.write(conteudo)
                except FileNotFoundError:
                    self.send_error(404, "style.css não encontrado")
            else:
                self.send_error(404, "style.css não encontrado")

        else:
            self.send_error(404, "Recurso não encontrado")


def iniciar_servidor_http(host="", port=8000):
    servidor = HTTPServer((host, port), DashboardHandler)
    print(f"Servidor HTTP iniciado em http://{host or 'localhost'}:{port}/")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("Encerrando servidor HTTP...")
    finally:
        servidor.server_close()


if __name__ == "__main__":
    try:
        t_sensor = threading.Thread(target=loop_sensor, daemon=True)
        t_sensor.start()
        iniciar_servidor_http(host="", port=8000)
    finally:
        gpio.cleanup()
        print("GPIO liberado.")
