# Development Guide

## Running with Mock Data

### Option 1: Frontend Dev Tools (Easiest)

When Flask is running in DEBUG mode, a dev tools panel appears in the bottom-left:

\`\`\`bash
python app.py
\`\`\`

Then in the browser at `http://localhost:5000`:
- Click "Start Simulation" to generate continuous traffic
- Click "Add High Risk" to inject a high-risk flow
- Click "Add Suspicious" to inject a suspicious flow
- Click "Clear Data" to reset the dashboard

### Option 2: Python Simulator (Production-like)

For more realistic Socket.IO simulation:

\`\`\`bash
# Terminal 1: Start Flask app
python app.py

# Terminal 2: Run simulator
python mock_data/dev_simulator.py
\`\`\`

The simulator will connect to the Flask server and emit realistic traffic patterns every 2 seconds.

### Option 3: Seed Script (Initial Data)

Populate the database with sample flows:

\`\`\`bash
python mock_data/seed_database.py
\`\`\`

## Sample Data Structure

All flows follow this structure:

\`\`\`json
{
  "timestamp": "2025-11-12T08:12:34Z",
  "src_ip": "192.168.1.105",
  "dst_ip": "10.0.0.1",
  "dst_port": 80,
  "flow_bytes_s": 250000,
  "flow_packets_s": 8000,
  "total_packets": 12000,
  "avg_pkt_size": 300,
  "ddos_probability": 0.95,
  "status": "high_risk",
  "note": ""
}
\`\`\`

## Risk Categories

- **High Risk** (ddos_probability ≥ 0.90): Auto-blocked if enabled
- **Suspicious** (0 < ddos_probability < 0.90): Requires human review
- **Normal** (ddos_probability = 0 or low): Allowed traffic
- **Blocked**: Manually or automatically blocked

## Testing Workflows

### Test 1: High-Risk Auto-Block

1. Ensure "Auto-blocking" is enabled in Settings
2. Use Dev Tools → "Add High Risk" or run simulator
3. Verify IP appears in red, status shows "BLOCKED"
4. Check Audit Logs for auto-block entry

### Test 2: Suspicious Verification

1. Use Dev Tools → "Add Suspicious" multiple times
2. Go to Verification Queue
3. Select suspicious IPs with checkboxes
4. Click "Block Selected" or "Release Selected"
5. Verify action appears in Audit Logs

### Test 3: Settings Changes

1. Toggle "Auto-blocking" ON/OFF
2. Adjust "Risk Threshold" slider
3. Verify settings persist and emit to frontend
4. Add new flows and confirm behavior matches settings

### Test 4: Real-time Updates

1. Start simulation in Dev Tools
2. Watch Dashboard update in real-time (<2s latency)
3. Verify Summary Cards update immediately
4. Check that rows change color based on status

### Test 5: Responsive Design

1. Open dashboard in browser DevTools
2. Toggle device toolbar (mobile view)
3. Verify table collapses to readable format
4. Verify all buttons are clickable on mobile

## Debugging

### No flows appearing?

1. Check browser console (F12) for errors
2. Verify Socket.IO is connected (green "● Connected" indicator)
3. Check if Dev Tools are working: Start Simulation
4. Run `curl http://localhost:5000/api/flows` to check backend

### Socket.IO connection issues?

1. Ensure Flask app is running: `python app.py`
2. Check if port 5000 is in use: `lsof -i :5000`
3. Verify CORS settings in app.py allow your URL
4. Check browser DevTools Network tab for WebSocket

### Simulator not connecting?

1. Start Flask app first: `python app.py`
2. Verify dependencies: `pip install python-socketio`
3. Run simulator: `python mock_data/dev_simulator.py`
4. Check if simulator connects (look for "[Simulator] Connected to Flask server")

## Production Deployment

Before deploying:

1. Disable DEBUG mode: Set `app.config['DEBUG'] = False`
2. Implement proper authentication in `@require_auth` decorator
3. Replace in-memory `ip_database` with persistent storage (SQL database)
4. Add rate limiting and input validation
5. Configure appropriate CORS policies
6. Use production WSGI server (Gunicorn, uWSGI)
7. Set up TLS/HTTPS
8. Implement log rotation and archival
9. Set up monitoring and alerting for the dashboard itself

## Example Production Setup

\`\`\`bash
# Install production dependencies
pip install gunicorn gevent gevent-websocket

# Run with Gunicorn
gunicorn --worker-class gevent -w 4 -b 0.0.0.0:5000 app:app
