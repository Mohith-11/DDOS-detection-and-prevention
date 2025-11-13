# DDoS Detection & Prevention Dashboard

A Flask-based real-time monitoring dashboard for detecting and preventing DDoS attacks with human verification workflows.

## Features

- **Real-time Traffic Monitoring**: Live updates via Socket.IO
- **Automated Threat Detection**: Auto-blocking for high-risk IPs (≥90% probability)
- **Verification Queue**: Human review for suspicious IPs (0-90% probability)
- **Audit Logging**: Complete action history with operator tracking
- **Responsive Design**: Mobile-friendly dark-mode interface
- **Settings Management**: Configurable auto-blocking and risk thresholds

## Quick Start

### Installation

\`\`\`bash
# Install dependencies
pip install flask flask-socketio python-socketio python-engineio

# Clone or download this project
cd ddos-dashboard

# Run the app
python app.py
\`\`\`

The dashboard will be available at `http://localhost:5000`

### Development with Mock Data

To test with mock data, modify `app.py` to load sample flows:

\`\`\`python
# In app.py, after creating the app:
with open('mock_data/sample_flows.json') as f:
    sample_flows = json.load(f)
    for flow in sample_flows:
        ip = flow['src_ip']
        ip_database[ip] = flow
\`\`\`

### Configuration

**Settings** (accessible at `/settings`):
- `auto_block`: Enable/disable automatic blocking of high-risk IPs
- `threshold`: Risk probability threshold (default: 0.90)

## API Endpoints

### Summary
\`\`\`
GET /api/summary
\`\`\`

### Flows
\`\`\`
GET /api/flows?limit=100
\`\`\`

### IP Details
\`\`\`
GET /api/ip/<ip_address>
\`\`\`

### Block/Release/Notes
\`\`\`
POST /api/block
POST /api/release
POST /api/notes
\`\`\`

### Settings
\`\`\`
GET /api/settings
POST /api/settings
\`\`\`

## WebSocket Events

### From Server
- `summary_update`: Summary statistics changed
- `flow_update`: New or updated flow
- `ip_status_change`: IP status (normal/suspicious/high_risk/blocked) changed
- `settings_updated`: Settings changed

### From Client
- `request_summary`: Request current summary data

## Risk Classification

- **High Risk** (≥90%): Auto-blocked if enabled, shown in red
- **Suspicious** (0-90%): Requires human verification, shown in orange
- **Normal** (0%): Allowed traffic, shown in neutral color
- **Blocked**: Manually or automatically blocked, shown in grey

## Architecture

\`\`\`
app.py                      # Flask server + Socket.IO
├── /templates/             # Jinja2 templates
│   ├── base.html          # Base layout
│   ├── dashboard.html     # Main monitoring page
│   ├── verification.html  # Verification queue
│   ├── logs.html          # Audit logs
│   └── settings.html      # Settings page
├── /static/               # Static assets
│   ├── /js/
│   │   ├── socket-manager.js      # Socket.IO connection
│   │   ├── toast-manager.js       # Notifications
│   │   ├── dashboard.js           # Dashboard logic
│   │   ├── verification.js        # Verification queue
│   │   ├── logs.js                # Logs page
│   │   └── settings.js            # Settings page
│   └── /css/
│       └── style.css              # Dark-mode styling
└── /mock_data/            # Sample data for testing
    └── sample_flows.json
\`\`\`

## Accessibility & Responsive Design

- Keyboard navigation support
- ARIA labels and semantic HTML
- Dark mode optimized for SOC environments
- Mobile-responsive table (cards on mobile)
- Visible focus states on all interactive elements

## Security Notes

- This is a **frontend demo** - implement proper authentication in production
- Replace placeholder auth middleware with real JWT/OAuth
- Use HTTPS in production
- Validate all inputs server-side
- Implement rate limiting on endpoints
- Add CORS policies appropriate to your environment

## Future Enhancements

- User authentication & role-based access control
- Persistent database backend
- Advanced filtering & search
- Export audit logs to CSV/JSON
- Integration with external threat intelligence feeds
- Mobile app
- Machine learning model deployment

## Support

For issues or questions, check the logs and ensure:
1. Flask and flask-socketio are properly installed
2. Port 5000 is available
3. Browser supports WebSockets
4. JavaScript console shows no errors
