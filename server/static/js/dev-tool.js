/**
 * Development tools for testing the dashboard
 * Usage: Include in base.html when DEV_MODE is enabled
 */

class DevTools {
  constructor() {
    this.simulationRunning = false
    this.init()
  }

  init() {
    this.createDevPanel()
  }

  createDevPanel() {
    const panel = document.createElement("div")
    panel.id = "dev-panel"
    panel.innerHTML = `
            <div style="position: fixed; bottom: 20px; left: 20px; z-index: 9999; background: #1a1a1a; border: 1px solid #444; border-radius: 8px; padding: 12px; font-size: 12px; font-family: monospace; color: #0f0; max-width: 300px;">
                <div style="margin-bottom: 10px; font-weight: bold; border-bottom: 1px solid #444; padding-bottom: 8px;">
                    ⚙️ Dev Tools
                </div>
                <button id="dev-toggle-sim" style="width: 100%; padding: 6px; margin-bottom: 6px; background: #28a745; color: #fff; border: none; border-radius: 4px; cursor: pointer; font-family: monospace;">
                    Start Simulation
                </button>
                <button id="dev-clear-data" style="width: 100%; padding: 6px; margin-bottom: 6px; background: #dc3545; color: #fff; border: none; border-radius: 4px; cursor: pointer; font-family: monospace;">
                    Clear Data
                </button>
                <button id="dev-add-high-risk" style="width: 100%; padding: 6px; margin-bottom: 6px; background: #ffc107; color: #000; border: none; border-radius: 4px; cursor: pointer; font-family: monospace;">
                    Add High Risk
                </button>
                <button id="dev-add-suspicious" style="width: 100%; padding: 6px; margin-bottom: 6px; background: #ff9800; color: #fff; border: none; border-radius: 4px; cursor: pointer; font-family: monospace;">
                    Add Suspicious
                </button>
                <div id="dev-status" style="margin-top: 10px; padding: 6px; background: #222; border-radius: 4px; border-left: 2px solid #0f0;">
                    Status: Ready
                </div>
            </div>
        `
    document.body.appendChild(panel)

    this.setupEventListeners()
  }

  setupEventListeners() {
    document.getElementById("dev-toggle-sim").addEventListener("click", () => this.toggleSimulation())
    document.getElementById("dev-clear-data").addEventListener("click", () => this.clearData())
    document.getElementById("dev-add-high-risk").addEventListener("click", () => this.addHighRiskFlow())
    document.getElementById("dev-add-suspicious").addEventListener("click", () => this.addSuspiciousFlow())
  }

  updateStatus(message) {
    const statusEl = document.getElementById("dev-status")
    if (statusEl) {
      statusEl.textContent = `Status: ${message}`
    }
  }

  toggleSimulation() {
    const btn = document.getElementById("dev-toggle-sim")
    if (this.simulationRunning) {
      this.simulationRunning = false
      btn.textContent = "Start Simulation"
      btn.style.background = "#28a745"
      this.updateStatus("Simulation stopped")
    } else {
      this.simulationRunning = true
      btn.textContent = "Stop Simulation"
      btn.style.background = "#dc3545"
      this.updateStatus("Simulation running...")
      this.runSimulation()
    }
  }

  async runSimulation() {
    const baseIPs = [
      "192.168.1.100",
      "192.168.1.105",
      "10.0.0.50",
      "172.16.0.20",
      "203.0.113.45",
      "198.51.100.200",
      "192.0.2.75",
      "10.20.30.40",
    ]

    let iteration = 0
    while (this.simulationRunning) {
      iteration++

      if (iteration % 5 === 1) {
        this.addFlow(baseIPs[0], 0.95, "High Risk")
      }
      if (iteration % 4 === 1) {
        this.addFlow(baseIPs[2], 0.72, "Suspicious")
      }
      if (iteration % 3 === 0) {
        this.addFlow(baseIPs[5], 0.1, "Normal")
      }

      await new Promise((resolve) => setTimeout(resolve, 2000))
    }
  }

  addFlow(ip, probability, type) {
    const flow = {
      timestamp: new Date().toISOString(),
      src_ip: ip,
      dst_ip: "10.0.0.1",
      dst_port: [22, 80, 443, 3306, 5432][Math.floor(Math.random() * 5)],
      flow_bytes_s: Math.random() * 500000,
      flow_packets_s: Math.random() * 15000,
      total_packets: Math.random() * 100000,
      avg_pkt_size: 256 + Math.random() * 256,
      ddos_probability: probability,
      status: probability >= 0.9 ? "high_risk" : probability > 0 ? "suspicious" : "normal",
      note: "",
    }

    if (window.socketManager) {
      window.socketManager.emit("flow_update", flow)
    } else {
      console.log("[DevTools] Flow:", flow)
    }

    this.updateStatus(`Added: ${ip} (${type})`)
  }

  addHighRiskFlow() {
    const randomIP = `${192 + Math.floor(Math.random() * 64)}.${Math.floor(Math.random() * 256)}.${Math.floor(Math.random() * 256)}.${100 + Math.floor(Math.random() * 155)}`
    this.addFlow(randomIP, 0.95, "High Risk")
  }

  addSuspiciousFlow() {
    const randomIP = `${192 + Math.floor(Math.random() * 64)}.${Math.floor(Math.random() * 256)}.${Math.floor(Math.random() * 256)}.${100 + Math.floor(Math.random() * 155)}`
    this.addFlow(randomIP, 0.72, "Suspicious")
  }

  clearData() {
    if (window.currentFlows) {
      window.currentFlows = {}
      if (window.renderTable) window.renderTable()
      this.updateStatus("Data cleared")
    }
  }
}

// Initialize dev tools
document.addEventListener("DOMContentLoaded", () => {
  const devTools = new DevTools()
})
