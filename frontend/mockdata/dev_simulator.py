"""
Development simulator for Socket.IO events and mock data injection.
Run this alongside app.py to simulate real DDoS traffic patterns.

Usage:
    python mock_data/dev_simulator.py
"""

import socketio
import time
import random
import json
from datetime import datetime, timedelta
import threading

# Connect to the Flask Socket.IO server
sio = socketio.Client()

BASE_IPS = [
    '192.168.1.100', '192.168.1.105', '10.0.0.50', '172.16.0.20',
    '203.0.113.45', '198.51.100.200', '192.0.2.75', '10.20.30.40'
]

def generate_flow(ip, force_status=None):
    """Generate a realistic flow object"""
    if force_status == 'high_risk':
        ddos_prob = random.uniform(0.90, 0.99)
    elif force_status == 'suspicious':
        ddos_prob = random.uniform(0.50, 0.89)
    elif force_status == 'normal':
        ddos_prob = random.uniform(0.0, 0.15)
    else:
        ddos_prob = random.uniform(0.0, 1.0)
    
    return {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'src_ip': ip,
        'dst_ip': '10.0.0.1',
        'dst_port': random.choice([22, 80, 443, 3306, 5432]),
        'flow_bytes_s': random.randint(10000, 500000),
        'flow_packets_s': random.randint(500, 15000),
        'total_packets': random.randint(1000, 100000),
        'avg_pkt_size': random.randint(200, 500),
        'ddos_probability': ddos_prob,
        'status': 'blocked' if ddos_prob >= 0.90 else ('suspicious' if ddos_prob > 0.0 else 'normal'),
        'note': ''
    }

@sio.event
def connect():
    print('[Simulator] Connected to Flask server')
    sio.emit('request_summary')

@sio.event
def disconnect():
    print('[Simulator] Disconnected from Flask server')

def simulate_traffic():
    """Simulate continuous traffic updates"""
    print('[Simulator] Starting traffic simulation...')
    
    iteration = 0
    while True:
        try:
            iteration += 1
            
            # Generate flows for different scenarios
            if iteration % 5 == 1:
                # High-risk flow
                ip = random.choice(BASE_IPS[:2])
                flow = generate_flow(ip, force_status='high_risk')
                print(f'[Simulator] HIGH RISK: {ip} ({flow["ddos_probability"]:.2%})')
                sio.emit('flow_update', flow)
            
            if iteration % 4 == 1:
                # Suspicious flow
                ip = random.choice(BASE_IPS[2:5])
                flow = generate_flow(ip, force_status='suspicious')
                print(f'[Simulator] SUSPICIOUS: {ip} ({flow["ddos_probability"]:.2%})')
                sio.emit('flow_update', flow)
            
            if iteration % 3 == 0:
                # Normal flow
                ip = random.choice(BASE_IPS[5:])
                flow = generate_flow(ip, force_status='normal')
                print(f'[Simulator] NORMAL: {ip} ({flow["ddos_probability"]:.2%})')
                sio.emit('flow_update', flow)
            
            time.sleep(2)
            
            # Every 10 iterations, request summary
            if iteration % 10 == 0:
                sio.emit('request_summary')
        
        except Exception as e:
            print(f'[Simulator] Error: {e}')
            time.sleep(1)

def run_simulator(server_url='http://localhost:5000'):
    """Run the simulator"""
    try:
        print(f'[Simulator] Connecting to {server_url}...')
        sio.connect(server_url)
        
        # Start traffic simulation in a thread
        sim_thread = threading.Thread(target=simulate_traffic, daemon=True)
        sim_thread.start()
        
        # Keep the connection alive
        sio.wait()
    except Exception as e:
        print(f'[Simulator] Connection failed: {e}')
        print('[Simulator] Make sure Flask app is running on http://localhost:5000')

if __name__ == '__main__':
    run_simulator()
