let suspiciousIPs = {}
const selectedIPs = new Set()
const ToastManager = { success: console.log, error: console.error } // Declare ToastManager

document.addEventListener("DOMContentLoaded", () => {
  loadSuspiciousIPs()
  setInterval(loadSuspiciousIPs, 3000)

  document.getElementById("bulk-block-btn").addEventListener("click", bulkBlockIPs)
  document.getElementById("bulk-release-btn").addEventListener("click", bulkReleaseIPs)
})

async function loadSuspiciousIPs() {
  try {
    const response = await fetch("/api/flows?limit=100")
    const flows = await response.json()

    suspiciousIPs = {}
    flows.forEach((flow) => {
      if (flow.status === "suspicious") {
        suspiciousIPs[flow.src_ip] = flow
      }
    })

    renderVerificationList()
  } catch (error) {
    console.error("Error loading suspicious IPs:", error)
  }
}

function renderVerificationList() {
  const container = document.getElementById("verification-list")
  const noSuspiciousMsg = document.getElementById("no-suspicious")

  if (Object.keys(suspiciousIPs).length === 0) {
    container.innerHTML = ""
    noSuspiciousMsg.style.display = "block"
    return
  }

  noSuspiciousMsg.style.display = "none"

  container.innerHTML = Object.values(suspiciousIPs)
    .map(
      (ip) => `
        <div class="col-md-6">
            <div class="card bg-dark border-warning verification-card">
                <div class="card-header bg-darker border-warning d-flex justify-content-between align-items-center">
                    <div>
                        <h6 class="mb-0 text-light">${ip.src_ip}</h6>
                        <small class="text-warning">Suspicious</small>
                    </div>
                    <input type="checkbox" class="form-check-input" onclick="toggleIPSelection('${ip.src_ip}')">
                </div>
                <div class="card-body">
                    <div class="row g-2 mb-3">
                        <div class="col-6">
                            <label class="form-label text-muted small">Risk %</label>
                            <p class="text-light mb-0">${(ip.ddos_probability * 100).toFixed(1)}%</p>
                        </div>
                        <div class="col-6">
                            <label class="form-label text-muted small">Total Packets</label>
                            <p class="text-light mb-0">${ip.total_packets}</p>
                        </div>
                        <div class="col-6">
                            <label class="form-label text-muted small">Bytes/s</label>
                            <p class="text-light mb-0">${(ip.flow_bytes_s / 1024).toFixed(2)} KB/s</p>
                        </div>
                        <div class="col-6">
                            <label class="form-label text-muted small">Packets/s</label>
                            <p class="text-light mb-0">${(ip.flow_packets_s / 1000).toFixed(1)}K/s</p>
                        </div>
                    </div>
                    <textarea class="form-control bg-darker border-secondary text-light text-muted form-control-sm mb-3" placeholder="Add note (optional)..." data-ip="${ip.src_ip}"></textarea>
                    <div class="d-flex gap-2">
                        <button class="btn btn-danger btn-sm flex-grow-1" onclick="blockSuspicious('${ip.src_ip}')">Block</button>
                        <button class="btn btn-success btn-sm flex-grow-1" onclick="releaseSuspicious('${ip.src_ip}')">Release</button>
                    </div>
                </div>
            </div>
        </div>
    `,
    )
    .join("")
}

function toggleIPSelection(ip) {
  if (selectedIPs.has(ip)) {
    selectedIPs.delete(ip)
  } else {
    selectedIPs.add(ip)
  }
  updateBulkButtons()
}

function updateBulkButtons() {
  const hasSelection = selectedIPs.size > 0
  document.getElementById("bulk-block-btn").disabled = !hasSelection
  document.getElementById("bulk-release-btn").disabled = !hasSelection
}

async function blockSuspicious(ip) {
  try {
    const noteEl = document.querySelector(`textarea[data-ip="${ip}"]`)
    const note = noteEl ? noteEl.value : ""

    const response = await fetch("/api/block", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ip: ip,
        reason: "verification",
        operator: document.getElementById("operator-name").textContent,
      }),
    })

    if (response.ok && note) {
      await fetch("/api/notes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ip: ip,
          operator: document.getElementById("operator-name").textContent,
          note: note,
        }),
      })
    }

    if (response.ok) {
      delete suspiciousIPs[ip]
      renderVerificationList()
      ToastManager.success(`IP ${ip} blocked`)
    }
  } catch (error) {
    ToastManager.error("Failed to block IP")
  }
}

async function releaseSuspicious(ip) {
  try {
    const response = await fetch("/api/release", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ip: ip,
        operator: document.getElementById("operator-name").textContent,
        note: "Released from verification",
      }),
    })

    if (response.ok) {
      delete suspiciousIPs[ip]
      renderVerificationList()
      ToastManager.success(`IP ${ip} released`)
    }
  } catch (error) {
    ToastManager.error("Failed to release IP")
  }
}

async function bulkBlockIPs() {
  for (const ip of selectedIPs) {
    await blockSuspicious(ip)
  }
  selectedIPs.clear()
  updateBulkButtons()
}

async function bulkReleaseIPs() {
  for (const ip of selectedIPs) {
    await releaseSuspicious(ip)
  }
  selectedIPs.clear()
  updateBulkButtons()
}
