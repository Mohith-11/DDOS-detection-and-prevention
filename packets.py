#!/usr/bin/env python3
from scapy.all import sniff, IP, TCP, UDP
import time
import numpy as np

flows = {}

def flow_key(pkt):
    if IP not in pkt:
        return None
    ip = pkt[IP]
    sport = getattr(pkt, "sport", 0)
    dport = getattr(pkt, "dport", 0)
    return (ip.src, sport, ip.dst, dport, ip.proto)

def safe_array(x):
    return np.array(x) if len(x) > 0 else np.array([0.0])

def compute_features(flow):
    fwd = safe_array(flow["fwd_lens"])
    bwd = safe_array(flow["bwd_lens"])
    allp = np.concatenate((fwd, bwd)) if (fwd.size + bwd.size) > 0 else np.array([0.0])

    duration = flow["last"] - flow["start"]
    if duration <= 0: duration = 1e-6

    timestamps = np.array(flow["timestamps"])
    flow_iat_mean = np.mean(np.diff(timestamps)) if len(timestamps) > 1 else 0.0

    total_fwd_pkts = len(fwd)
    total_bwd_pkts = len(bwd)
    total_fwd_bytes = np.sum(fwd)
    total_bwd_bytes = np.sum(bwd)
    total_bytes = np.sum(allp)

    return {
        "Flow Bytes/s": total_bytes / duration,
        "Flow Packets/s": len(allp) / duration,
        "Total Length of Fwd Packets": total_fwd_bytes,
        "Total Length of Bwd Packets": total_bwd_bytes,
        "Total Fwd Packets": total_fwd_pkts,
        "Total Backward Packets": total_bwd_pkts,
        "Average Packet Size": np.mean(allp),
        "Packet Length Mean": np.mean(allp),
        "Packet Length Variance": np.var(allp),
        "Max Packet Length": np.max(allp),
        "Min Packet Length": np.min(allp),
        "Fwd Packet Length Max": np.max(fwd),
        "Fwd Packet Length Min": np.min(fwd),
        "Fwd Packet Length Mean": np.mean(fwd),
        "Fwd Packet Length Std": np.std(fwd),
        "Bwd Packet Length Mean": np.mean(bwd),
        "Bwd Packet Length Std": np.std(bwd),
        "Flow Duration": duration,
        "Flow IAT Mean": flow_iat_mean,
        "Down/Up Ratio": (total_bwd_pkts / total_fwd_pkts) if total_fwd_pkts > 0 else 0.0
    }

def process_packet(pkt):
    now = time.time()
    key = flow_key(pkt)
    if key is None:
        return

    rev = (key[2], key[3], key[0], key[1], key[4])
    direction = "fwd"
    if rev in flows:
        key = rev
        direction = "bwd"

    if key not in flows:
        flows[key] = {"start": now, "last": now, "fwd_lens": [], "bwd_lens": [], "timestamps": []}

    flow = flows[key]
    flow["timestamps"].append(now)
    flow["last"] = now

    pkt_len = len(pkt)
    if direction == "fwd":
        flow["fwd_lens"].append(pkt_len)
    else:
        flow["bwd_lens"].append(pkt_len)

    features = compute_features(flow)

    print(f"\nFlow: {key[0]}:{key[1]} → {key[2]}:{key[3]} (proto={key[4]})")
    for k, v in features.items():
        print(f"  {k}: {v:.6f}")
    return features

def main():
    print("Starting real-time flow feature sniffer... (Ctrl+C to stop)")
    sniff(prn=process_packet, store=False)

if __name__ == "__main__":
    main()
