class ToastManager {
  static show(message, type = "info", duration = 3000) {
    const toastId = `toast-${Date.now()}`
    const container = document.getElementById("toast-container")

    if (!container) return

    const toast = document.createElement("div")
    toast.id = toastId
    toast.className = `toast`
    toast.role = "alert"
    toast.innerHTML = `
            <div class="toast-body d-flex gap-2">
                <span>${this.getIcon(type)}</span>
                <span>${message}</span>
            </div>
        `

    container.appendChild(toast)

    const bsToast = new window.bootstrap.Toast(toast, { delay: duration })
    bsToast.show()

    toast.addEventListener("hidden.bs.toast", () => {
      toast.remove()
    })
  }

  static getIcon(type) {
    switch (type) {
      case "danger":
        return "❌"
      case "success":
        return "✅"
      case "warning":
        return "⚠️"
      case "info":
      default:
        return "ℹ️"
    }
  }

  static success(message, duration = 3000) {
    this.show(message, "success", duration)
  }

  static error(message, duration = 3000) {
    this.show(message, "danger", duration)
  }

  static warning(message, duration = 3000) {
    this.show(message, "warning", duration)
  }

  static info(message, duration = 3000) {
    this.show(message, "info", duration)
  }
}
