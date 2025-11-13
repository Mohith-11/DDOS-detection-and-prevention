let auditLogs = []

document.addEventListener("DOMContentLoaded", () => {
  loadLogs()
  setInterval(loadLogs, 5000)

  document.getElementById("filter-ip").addEventListener("input", renderLogsTable)
  document.getElementById("filter-action").addEventListener("change", renderLogsTable)
})

async function loadLogs() {
  try {
    const response = await fetch("/api/logs?limit=100")
    auditLogs = await response.json()
    renderLogsTable()
  } catch (error) {
    console.error("Error loading logs:", error)
  }
}

function renderLogsTable() {
  const tbody = document.getElementById("logs-tbody")
  const filterIP = document.getElementById("filter-ip").value.toLowerCase()
  const filterAction = document.getElementById("filter-action").value

  const filteredLogs = auditLogs.filter((log) => {
    const matchesIP = !filterIP || log.ip.toLowerCase().includes(filterIP)
    const matchesAction = !filterAction || log.action === filterAction
    return matchesIP && matchesAction
  })

  // Sort by timestamp (newest first)
  filteredLogs.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))

  tbody.innerHTML = filteredLogs
    .map((log) => {
      const actionBadge = log.action === "block" ? "danger" : "success"
      return `
            <tr>
                <td><small>${new Date(log.timestamp).toLocaleString()}</small></td>
                <td><span class="badge bg-${actionBadge}">${log.action.toUpperCase()}</span></td>
                <td><code>${log.ip}</code></td>
                <td><small>${log.operator}</small></td>
                <td><small class="text-muted">${log.reason || log.note || "—"}</small></td>
            </tr>
        `
    })
    .join("")

  if (filteredLogs.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" class="text-center text-muted py-4">No logs found</td></tr>`
  }
}
