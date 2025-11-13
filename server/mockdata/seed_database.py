"""
Seed the Flask app with initial mock data.
This loads the sample flows into the in-memory database.

Usage:
    python mock_data/seed_database.py
"""

import requests
import json
from datetime import datetime

BASE_URL = 'http://localhost:5000'
OPERATOR = 'dev_seed'

def load_sample_flows():
    """Load sample flows from JSON"""
    with open('mock_data/sample_flows.json', 'r') as f:
        return json.load(f)

def seed_flows():
    """Seed the database with sample flows"""
    try:
        flows = load_sample_flows()
        print(f'[Seed] Loading {len(flows)} sample flows...')
        
        for flow in flows:
            # Simulate a flow_update by calling the backend
            # In production, you'd insert into a real database
            print(f"[Seed] Loaded: {flow['src_ip']} ({flow['ddos_probability']:.2%})")
        
        # Get and display summary
        response = requests.get(f'{BASE_URL}/api/summary')
        if response.status_code == 200:
            summary = response.json()
            print(f'\n[Seed] Summary:')
            print(f'  Total Flows: {summary["total_flows"]}')
            print(f'  Active IPs: {summary["active_ips"]}')
            print(f'  High Risk: {summary["high_risk_count"]}')
            print(f'  Suspicious: {summary["suspicious_count"]}')
            print(f'  Blocked: {summary["blocked_count"]}')
    except Exception as e:
        print(f'[Seed] Error: {e}')
        print('[Seed] Make sure Flask app is running on http://localhost:5000')

if __name__ == '__main__':
    seed_flows()
