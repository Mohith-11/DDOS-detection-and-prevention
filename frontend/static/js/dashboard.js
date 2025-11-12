const currentFlows = {}
const pageSize = 50
const ToastManager = window.ToastManager // Declare ToastManager
const socketManager = window.socketManager // Declare socketManager
const bootstrap = window.bootstrap // Declare bootstrap

// Initialize on page load
document.addEventListener("DOMContentLoaded", () => {
  loadInitialData()
  setupEventListeners()
  setInterval(refreshFlows, 3000)
})

async function loadInitialData() {
  try {
    const response = await fetch(`/api/flows?limit=${pageSize}`)
    const flows = await response.json()

    flows.forEach((flow) => {
      currentFlows[flow.src_ip] = flow
    })

    renderTable()
    await updateSummary()
  } catch (error) {
    console.error("Error loading initial data:", error)
    ToastManager.error("Failed to load initial data")
  }
}

async function refreshFlows() {
  try {
    const response = await fetch(`/api/flows?limit=${pageSize}`)
    const flows = await response.json()

    flows.forEach((flow) => {
      const oldFlow = currentFlows[flow.src_ip]
      currentFlows[flow.src_ip] = flow

      // Animate if changed
      if (oldFlow && oldFlow.status !== flow.status) {
        handleIPStatusChange({
          ip: flow.src_ip,
          old_status: oldFlow.status,
          new_status: flow.status,
          by: "system",
        })
      }
    })

    renderTable()
  } catch (error) {
    console.error("Error refreshing flows:", error)
  }
}

async function updateSummary(data) {
  try {
    if (!data) {
      const response = await fetch("/api/summary")
      data = await response.json()
    }

    document.getElementById("card-total-flows").textContent = data.total_flows
    document.getElementById("card-active-ips").textContent = data.active_ips
    document.getElementById("card-high-risk").textContent = data.high_risk_count
    document.getElementById("card-suspicious").textContent = data.suspicious_count
    document.getElementById("card-blocked").textContent = data.blocked_count
  } catch (error) {
    console.error("Error updating summary:", error)
  }
}

function addOrUpdateFlow(flow) {
  currentFlows[flow.src_ip] = flow
  renderTable()
  updateSummary()
}

function handleIPStatusChange(data) {
  const row = document.querySelector(`tr[data-ip="${data.ip}"]`)
  if (row) {
    row.classList.remove("row-normal", "row-suspicious", "row-high-risk", "row-blocked")
    row.classList.add(`row-${data.new_status}`)

    if (data.new_status === "blocked" && data.by === "system") {
      ToastManager.warning(`IP ${data.ip} auto-blocked (90%+)`)
    }
  }
}

function renderTable() {
  const tbody = document.getElementById("traffic-tbody")
  const searchTerm = document.getElementById("search-ip").value.toLowerCase()
  const statusFilter = document.getElementById("filter-status").value

  const filteredFlows = Object.values(currentFlows).filter((flow) => {
    const matchesSearch = flow.src_ip.toLowerCase().includes(searchTerm)
    const matchesStatus = !statusFilter || flow.status === statusFilter
    return matchesSearch && matchesStatus
  })

  // Sort by timestamp (newest first)
  filteredFlows.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))

  tbody.innerHTML = filteredFlows
    .map((flow) => {
      const riskPercent = (flow.ddos_probability * 100).toFixed(1)
      const statusBadgeClass = `badge-${flow.status}`
      const rowClass = `row-${flow.status}`

      return `
            <tr class="${rowClass}" data-ip="${flow.src_ip}" onclick="showIPDetail('${flow.src_ip}')">
                <td><small>${new Date(flow.timestamp).toLocaleTimeString()}</small></td>
                <td><code>${flow.src_ip}</code></td>
                <td><small>${flow.dst_ip}:${flow.dst_port}</small></td>
                <td>${(flow.flow_bytes_s / 1024).toFixed(2)} KB/s</td>
                <td>${(flow.flow_packets_s / 1000).toFixed(1)}K/s</td>
                <td>${flow.total_packets}</td>
                <td><strong>${riskPercent}%</strong></td>
                <td><span class="badge ${statusBadgeClass}">${flow.status.replace("_", " ").toUpperCase()}</span></td>
                <td>
                    <button class="btn btn-sm btn-danger" onclick="blockIP('${flow.src_ip}', event)">Block</button>
                    <button class="btn btn-sm btn-success" onclick="releaseIP('${flow.src_ip}', event)">Release</button>
                </td>
            </tr>
        `
    })
    .join("")

  if (filteredFlows.length === 0) {
    tbody.innerHTML = `<tr><td colspan="9" class="text-center text-muted py-4">No flows found</td></tr>`
  }
}

function setupEventListeners() {
  document.getElementById("search-ip").addEventListener("input", renderTable)
  document.getElementById("filter-status").addEventListener("change", renderTable)
}

async function blockIP(ip, event) {
  event.stopPropagation()

  try {
    const response = await fetch("/api/block", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ip: ip,
        reason: "manual",
        operator: document.getElementById("operator-name").textContent,
      }),
    })

    if (response.ok) {
      currentFlows[ip].status = "blocked"
      renderTable()
      ToastManager.success(`IP ${ip} blocked`)
      socketManager.emit("request_summary")
    }
  } catch (error) {
    ToastManager.error("Failed to block IP")
  }
}

async function releaseIP(ip, event) {
  event.stopPropagation()

  try {
    const response = await fetch("/api/release", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ip: ip,
        operator: document.getElementById("operator-name").textContent,
        note: "Manual release",
      }),
    })

    if (response.ok) {
      currentFlows[ip].status = "normal"
      renderTable()
      ToastManager.success(`IP ${ip} released`)
      socketManager.emit("request_summary")
    }
  } catch (error) {
    ToastManager.error("Failed to release IP")
  }
}

async function showIPDetail(ip) {
  try {
    const response = await fetch(`/api/ip/${ip}`)
    const ipData = await response.json()

    const modal = new bootstrap.Modal(document.getElementById("ipDetailModal"))
    const body = document.getElementById("ipDetailBody")

    body.innerHTML = `
            <div class="row g-3">
                <div class="col-12">
                    <label class="form-label text-muted small">IP Address</label>
                    <p class="text-light font-monospace mb-0">${ip}</p>
                </div>
                <div class="col-md-6">
                    <label class="form-label text-muted small">Status</label>
                    <p class="text-light mb-0"><span class="badge badge-${ipData.status}">${ipData.status.toUpperCase()}</span></p>
                </div>
                <div class="col-md-6">
                    <label class="form-label text-muted small">Risk Probability</label>
                    <p class="text-light mb-0">${(ipData.ddos_probability * 100).toFixed(1)}%</p>
                </div>
                <div class="col-md-6">
                    <label class="form-label text-muted small">Bytes/s</label>
                    <p class="text-light mb-0">${(ipData.flow_bytes_s / 1024).toFixed(2)} KB/s</p>
                </div>
                <div class="col-md-6">
                    <label class="form-label text-muted small">Packets/s</label>
                    <p class="text-light mb-0">${(ipData.flow_packets_s / 1000).toFixed(1)}K/s</p>
                </div>
                <div class="col-12">
                    <label class="form-label text-muted small">Actions</label>
                    <div class="btn-group d-block" role="group">
                        <button type="button" class="btn btn-danger btn-sm" onclick="blockIP('${ip}')">Block IP</button>
                        <button type="button" class="btn btn-success btn-sm" onclick="releaseIP('${ip}')">Release IP</button>
                    </div>
                </div>
            </div>
        `

    modal.show()
  } catch (error) {
    ToastManager.error("Failed to load IP details")
  }
}
