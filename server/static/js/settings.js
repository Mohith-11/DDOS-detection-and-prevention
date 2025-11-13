document.addEventListener("DOMContentLoaded", async () => {
  await loadSettings()

  document.getElementById("auto-block-toggle").addEventListener("change", updateAutoBlock)
  document.getElementById("threshold-slider").addEventListener("input", updateThreshold)
})

const ToastManager = {
  success: (message) => {
    console.log("Success:", message)
  },
  error: (message) => {
    console.error("Error:", message)
  },
  info: (message) => {
    console.info("Info:", message)
  },
}

async function loadSettings() {
  try {
    const response = await fetch("/api/settings")
    const settings = await response.json()

    document.getElementById("auto-block-toggle").checked = settings.auto_block
    document.getElementById("threshold-slider").value = settings.threshold
    document.getElementById("threshold-value").textContent = settings.threshold.toFixed(2)
  } catch (error) {
    console.error("Error loading settings:", error)
  }
}

async function updateAutoBlock(event) {
  try {
    const response = await fetch("/api/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        auto_block: event.target.checked,
      }),
    })

    if (response.ok) {
      ToastManager.success(`Auto-blocking ${event.target.checked ? "enabled" : "disabled"}`)
    }
  } catch (error) {
    ToastManager.error("Failed to update settings")
  }
}

async function updateThreshold(event) {
  const threshold = Number.parseFloat(event.target.value)
  document.getElementById("threshold-value").textContent = threshold.toFixed(2)

  try {
    const response = await fetch("/api/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        threshold: threshold,
      }),
    })

    if (response.ok) {
      ToastManager.info(`Threshold set to ${threshold.toFixed(2)}`)
    }
  } catch (error) {
    ToastManager.error("Failed to update threshold")
  }
}
