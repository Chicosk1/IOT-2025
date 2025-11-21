from flask import Blueprint, render_template, jsonify
from datetime import datetime, timedelta
import RPi.GPIO as GPIO
import time
import atexit

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

sensorPin = 22  # pino digital do sensor de gás (D0 do módulo, por exemplo)

monitorando = True
nivelGasAtual = 0
ultimaLeitura = 0
intervaloLeitura = 2  # segundos

minNivel = None
maxNivel = None
mediaNivel = 0.0
totalLeituras = 0

statusTexto = "Aguardando leitura"
statusNivel = "normal"  # normal | atencao | perigo
ultimaAtualizacaoStr = ""

logs = []

GPIO.setup(sensorPin, GPIO.IN)


def _agora_brasilia():
    offset = timedelta(hours=-3)
    return datetime.utcnow() + offset


def adicionar_log(mensagem):
    timestamp = _agora_brasilia().strftime("%d/%m/%Y %H:%M:%S")
    log_entry = f"[{timestamp}] {mensagem}"
    logs.append(log_entry)
    if len(logs) > 50:
        logs.pop(0)


def ler_sensor():
    leitura = GPIO.input(sensorPin)
    nivel = 0.0 if leitura == 1 else 100.0
    return nivel


def _classificar_nivel(nivel):
    if nivel < 40:
        return "Normal", "normal"
    elif nivel < 70:
        return "Atenção", "atencao"
    else:
        return "Perigo", "perigo"


def atualizar_monitoramento():
    global ultimaLeitura, nivelGasAtual, minNivel, maxNivel, mediaNivel
    global totalLeituras, statusTexto, statusNivel, ultimaAtualizacaoStr

    agora = time.time()
    if agora - ultimaLeitura < intervaloLeitura:
        return

    ultimaLeitura = agora

    if not monitorando:
        return

    nivel = ler_sensor()
    nivelGasAtual = float(nivel)

    texto, codigo = _classificar_nivel(nivel)
    if codigo != statusNivel:
        adicionar_log(f"Nível de gás mudou para {texto} ({nivel:.1f}%)")

    statusTexto = texto
    statusNivel = codigo
    ultimaAtualizacaoStr = _agora_brasilia().strftime("%d/%m/%Y %H:%M:%S")

    if totalLeituras == 0:
        minNivel = nivel
        maxNivel = nivel
        mediaNivel = nivel
    else:
        if nivel < minNivel:
            minNivel = nivel
        if nivel > maxNivel:
            maxNivel = nivel
        mediaNivel = ((mediaNivel * totalLeituras) + nivel) / (totalLeituras + 1)

    totalLeituras += 1


bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    return render_template("index.html")


@bp.route("/gas")
def gas():
    atualizar_monitoramento()
    return str(int(nivelGasAtual))


@bp.route("/toggle")
def toggle():
    global monitorando

    if monitorando:
        adicionar_log("Monitoramento de gás PAUSADO")
    else:
        adicionar_log("Monitoramento de gás RETOMADO")

    monitorando = not monitorando
    return "OK"


@bp.route("/status")
def status():
    atualizar_monitoramento()

    return jsonify({
        "monitorando": monitorando,
        "nivel_gas": nivelGasAtual,
        "status_texto": statusTexto,
        "status_nivel": statusNivel,
        "min_nivel": minNivel if minNivel is not None else 0.0,
        "max_nivel": maxNivel if maxNivel is not None else 0.0,
        "media_nivel": mediaNivel,
        "total_leituras": totalLeituras,
        "ultima_atualizacao": ultimaAtualizacaoStr,
        "thresholds": {
            "normal_max": 40,
            "atencao_max": 70
        }
    })


@bp.route("/logs")
def get_logs():
    return jsonify(logs)


@atexit.register
def cleanup():
    GPIO.cleanup()
    print("GPIO cleanup realizado")
