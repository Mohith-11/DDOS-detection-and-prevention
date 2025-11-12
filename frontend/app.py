from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from datetime import datetime, timedelta
import json
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
socketio = SocketIO(app, cors_allowed_origins="*")

# Store for active IPs and their states
ip_database = {}
audit_log = []
settings = {
    'auto_block': True,
    'threshold': 0.90
}

def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # In production, implement proper auth here
        return f(*args, **kwargs)
    return decorated_function

# ============ ROUTES ============

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/verification')
def verification():
    """Verification queue page"""
    return render_template('verification.html')

@app.route('/logs')
def logs():
    """Audit logs page"""
    return render_template('logs.html')

@app.route('/settings')
def settings_page():
    """Settings/operations page"""
    return render_template('settings.html')

# ============ API ENDPOINTS ============

@app.route('/api/summary')
@require_auth
def get_summary():
    """Get summary statistics"""
    high_risk = sum(1 for ip in ip_database.values() if ip.get('ddos_probability', 0) >= 0.90)
    suspicious = sum(1 for ip in ip_database.values() if 0 < ip.get('ddos_probability', 0) < 0.90)
    blocked = sum(1 for ip in ip_database.values() if ip.get('status') == 'blocked')
    
    return jsonify({
        'total_flows': len(ip_database),
        'active_ips': len(ip_database),
        'high_risk_count': high_risk,
        'suspicious_count': suspicious,
        'blocked_count': blocked
    })

@app.route('/api/flows')
@require_auth
def get_flows():
    """Get list of flows (converted from IP database for display)"""
    limit = request.args.get('limit', 100, type=int)
    
    flows = [
        {
            'timestamp': ip_data.get('timestamp', datetime.utcnow().isoformat() + 'Z'),
            'src_ip': ip,
            'dst_ip': ip_data.get('dst_ip', '192.168.1.1'),
            'dst_port': ip_data.get('dst_port', 80),
            'flow_bytes_s': ip_data.get('flow_bytes_s', 0),
            'flow_packets_s': ip_data.get('flow_packets_s', 0),
            'total_packets': ip_data.get('total_packets', 0),
            'avg_pkt_size': ip_data.get('avg_pkt_size', 0),
            'ddos_probability': ip_data.get('ddos_probability', 0),
            'status': ip_data.get('status', 'normal'),
            'note': ip_data.get('note', '')
        }
        for ip, ip_data in list(ip_database.items())[:limit]
    ]
    
    return jsonify(flows)

@app.route('/api/ip/<ip>')
@require_auth
def get_ip_detail(ip):
    """Get detailed information for an IP"""
    if ip not in ip_database:
        return jsonify({'error': 'IP not found'}), 404
    
    ip_data = ip_database[ip]
    return jsonify({
        **ip_data,
        'ip': ip,
        'history': ip_data.get('history', [])
    })

@app.route('/api/block', methods=['POST'])
@require_auth
def block_ip():
    """Block an IP"""
    data = request.json
    ip = data.get('ip')
    reason = data.get('reason', 'manual')
    operator = data.get('operator', 'system')
    
    if ip not in ip_database:
        ip_database[ip] = {}
    
    ip_database[ip]['status'] = 'blocked'
    ip_database[ip]['blocked_at'] = datetime.utcnow().isoformat() + 'Z'
    ip_database[ip]['blocked_by'] = operator
    ip_database[ip]['block_reason'] = reason
    
    # Log the action
    audit_log.append({
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'action': 'block',
        'ip': ip,
        'operator': operator,
        'reason': reason
    })
    
    # Broadcast update
    socketio.emit('ip_status_change', {
        'ip': ip,
        'old_status': ip_database[ip].get('status'),
        'new_status': 'blocked',
        'by': operator
    }, broadcast=True)
    
    return jsonify(ip_database[ip])

@app.route('/api/release', methods=['POST'])
@require_auth
def release_ip():
    """Release a blocked IP"""
    data = request.json
    ip = data.get('ip')
    operator = data.get('operator', 'system')
    note = data.get('note', '')
    
    if ip not in ip_database:
        return jsonify({'error': 'IP not found'}), 404
    
    old_status = ip_database[ip].get('status')
    ip_database[ip]['status'] = 'normal'
    ip_database[ip]['released_at'] = datetime.utcnow().isoformat() + 'Z'
    ip_database[ip]['released_by'] = operator
    
    # Log the action
    audit_log.append({
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'action': 'release',
        'ip': ip,
        'operator': operator,
        'note': note
    })
    
    # Broadcast update
    socketio.emit('ip_status_change', {
        'ip': ip,
        'old_status': old_status,
        'new_status': 'normal',
        'by': operator
    }, broadcast=True)
    
    return jsonify(ip_database[ip])

@app.route('/api/notes', methods=['POST'])
@require_auth
def add_note():
    """Add a note to an IP"""
    data = request.json
    ip = data.get('ip')
    operator = data.get('operator', 'system')
    note = data.get('note', '')
    
    if ip not in ip_database:
        ip_database[ip] = {}
    
    if 'notes' not in ip_database[ip]:
        ip_database[ip]['notes'] = []
    
    ip_database[ip]['notes'].append({
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'operator': operator,
        'text': note
    })
    
    return jsonify(ip_database[ip])

@app.route('/api/settings', methods=['GET', 'POST'])
@require_auth
def get_or_update_settings():
    """Get or update settings"""
    global settings
    
    if request.method == 'POST':
        data = request.json
        settings.update(data)
        socketio.emit('settings_updated', settings, broadcast=True)
        return jsonify(settings)
    
    return jsonify(settings)

@app.route('/api/logs')
@require_auth
def get_logs():
    """Get audit logs"""
    limit = request.args.get('limit', 100, type=int)
    return jsonify(audit_log[-limit:])

# ============ WEBSOCKET HANDLERS ============

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    emit('connected', {'data': 'Connected to DDoS Dashboard'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    pass

@socketio.on('request_summary')
def handle_summary_request():
    """Handle summary request"""
    high_risk = sum(1 for ip in ip_database.values() if ip.get('ddos_probability', 0) >= 0.90)
    suspicious = sum(1 for ip in ip_database.values() if 0 < ip.get('ddos_probability', 0) < 0.90)
    blocked = sum(1 for ip in ip_database.values() if ip.get('status') == 'blocked')
    
    emit('summary_update', {
        'total_flows': len(ip_database),
        'active_ips': len(ip_database),
        'high_risk_count': high_risk,
        'suspicious_count': suspicious,
        'blocked_count': blocked
    })

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
