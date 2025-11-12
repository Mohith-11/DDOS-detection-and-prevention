// Import the io function from socket.io-client
import { io } from "socket.io-client"

class SocketManager {
  constructor() {
    this.socket = null
    this.isConnected = false
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 5
    this.reconnectDelay = 3000
    this.init()
  }

  init() {
    this.socket = io({
      reconnection: true,
      reconnectionDelay: this.reconnectDelay,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: this.maxReconnectAttempts,
    })

    this.setupListeners()
  }

  setupListeners() {
    this.socket.on("connect", () => {
      this.isConnected = true
      this.updateConnectionStatus(true)
      console.log("[Socket.IO] Connected to server")
      this.socket.emit("request_summary")
    })

    this.socket.on("disconnect", () => {
      this.isConnected = false
      this.updateConnectionStatus(false)
      console.log("[Socket.IO] Disconnected from server")
    })

    this.socket.on("connect_error", (error) => {
      console.error("[Socket.IO] Connection error:", error)
    })

    this.socket.on("summary_update", (data) => {
      if (window.updateSummary) window.updateSummary(data)
    })

    this.socket.on("flow_update", (data) => {
      if (window.addOrUpdateFlow) window.addOrUpdateFlow(data)
    })

    this.socket.on("ip_status_change", (data) => {
      if (window.handleIPStatusChange) window.handleIPStatusChange(data)
    })

    this.socket.on("settings_updated", (data) => {
      if (window.updateSettings) window.updateSettings(data)
    })
  }

  updateConnectionStatus(connected) {
    const statusEl = document.getElementById("connection-status")
    if (statusEl) {
      statusEl.textContent = connected ? "● Connected" : "● Disconnected"
      statusEl.classList.toggle("connected", connected)
      statusEl.classList.toggle("disconnected", !connected)
    }
  }

  emit(event, data) {
    if (this.isConnected) {
      this.socket.emit(event, data)
    }
  }

  on(event, callback) {
    this.socket.on(event, callback)
  }

  off(event, callback) {
    this.socket.off(event, callback)
  }
}

const socketManager = new SocketManager()
