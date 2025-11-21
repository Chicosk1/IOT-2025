let nivelGasAtual = 0;

function atualizarLeituras() {
  fetch("/status")
    .then(r => r.json())
    .then(data => {
      nivelGasAtual = data.nivel_gas || 0;

      const valorFormatado = nivelGasAtual.toFixed
        ? nivelGasAtual.toFixed(1)
        : nivelGasAtual;

      const gasLevelElement = document.getElementById("gasLevel");
      if (gasLevelElement) {
        gasLevelElement.textContent = valorFormatado + "%";
      }

      const barra = document.getElementById("progressFill");
      if (barra) {
        barra.style.width = Math.max(0, Math.min(100, nivelGasAtual)) + "%";
      }

      const statusElement = document.getElementById("gasStatus");
      if (statusElement) {
        if (data.status_nivel === "perigo") {
          statusElement.textContent = "Nível de gás PERIGOSO";
          statusElement.style.color = "#f44336";
        } else if (data.status_nivel === "atencao") {
          statusElement.textContent = "Nível de gás em ATENÇÃO";
          statusElement.style.color = "#ff9800";
        } else {
          statusElement.textContent = "Nível de gás NORMAL";
          statusElement.style.color = "#4caf50";
        }
      }

      const minEl = document.getElementById("gasMin");
      if (minEl) {
        const v = data.min_nivel || 0;
        minEl.textContent = (v.toFixed ? v.toFixed(1) : v) + "%";
      }

      const maxEl = document.getElementById("gasMax");
      if (maxEl) {
        const v = data.max_nivel || 0;
        maxEl.textContent = (v.toFixed ? v.toFixed(1) : v) + "%";
      }

      const avgEl = document.getElementById("gasAvg");
      if (avgEl) {
        const v = data.media_nivel || 0;
        avgEl.textContent = (v.toFixed ? v.toFixed(1) : v) + "%";
      }

      const samplesEl = document.getElementById("gasSamples");
      if (samplesEl) {
        samplesEl.textContent = data.total_leituras || 0;
      }

      const lastUpdateEl = document.getElementById("gasLastUpdate");
      if (lastUpdateEl) {
        lastUpdateEl.textContent = data.ultima_atualizacao || "--";
      }

      atualizarStatusMonitoramento(data.monitorando);
    });
}

function atualizarStatusMonitoramento(monitorando) {
  const monitorElement = document.getElementById("statusMonitoramento");
  const btnMonitor = document.getElementById("btnMonitoramento");

  if (!monitorElement || !btnMonitor) return;

  if (monitorando) {
    monitorElement.textContent = "ATIVADO";
    monitorElement.className = "status-indicator status-monitorando";
    btnMonitor.innerHTML = "Pausar Monitoramento";
    btnMonitor.className = "btn btn-primary";
  } else {
    monitorElement.textContent = "PAUSADO";
    monitorElement.className = "status-indicator status-parado";
    btnMonitor.innerHTML = "Retomar Monitoramento";
    btnMonitor.className = "btn btn-primary";
  }
}

function atualizarStatus() {
  fetch("/status")
    .then(r => r.json())
    .then(data => {
      atualizarStatusMonitoramento(data.monitorando);
    });
}

function atualizarLogs() {
  fetch("/logs")
    .then(r => r.json())
    .then(listaLogs => {
      const logsContainer = document.getElementById("logsContainer");
      if (!logsContainer) return;

      logsContainer.innerHTML = "";

      listaLogs.slice().reverse().forEach(log => {
        const logElement = document.createElement("div");
        logElement.className = "log-entry";
        logElement.textContent = log;
        logsContainer.appendChild(logElement);
      });
    });
}

function alternarMonitoramento() {
  fetch("/toggle").then(() => {
    atualizarStatus();
    atualizarLogs();
  });
}

setInterval(() => {
  atualizarLeituras();
  atualizarLogs();
}, 2000);

document.addEventListener("DOMContentLoaded", function () {
  atualizarLeituras();
  atualizarStatus();
  atualizarLogs();
});
