from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta, timezone
import joblib
import json
import os
import platform
import subprocess
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DB_URL", "postgresql://postgres:passforpostgresql@localhost/ddosdb")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")
db = SQLAlchemy(app)

# ----------------------------------------------------------
# LOAD MODELS
# ----------------------------------------------------------
model = joblib.load(os.getenv("MODEL_PATH", "rf_model.pkl"))
scaler = joblib.load(os.getenv("SCALER_PATH", "scaler.pkl"))
selector = joblib.load(os.getenv("SELECTOR_PATH", "selector.pkl"))

# Threshold config
THRESH_CFG_PATH = os.getenv("THRESH_PATH", "threshold.json")
if os.path.exists(THRESH_CFG_PATH):
    try:
        threshold_cfg = json.load(open(THRESH_CFG_PATH))
    except:
        threshold_cfg = {"threshold": 0.9}
else:
    threshold_cfg = {"threshold": 0.9}

MANUAL_THRESHOLD = float(os.getenv("MANUAL_THRESHOLD", 0.3))

# ----------------------------------------------------------
# DATABASE MODELS
# ----------------------------------------------------------
class PacketLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    agent_id = db.Column(db.String(128))
    src_ip = db.Column(db.String(64))
    dst_ip = db.Column(db.String(64))
    probability = db.Column(db.Float)
    status = db.Column(db.String(32))
    verified = db.Column(db.Boolean, default=False)

    flow_bytes_s = db.Column(db.Float)
    flow_packets_s = db.Column(db.Float)
    total_length_fwd = db.Column(db.Float)
    total_length_bwd = db.Column(db.Float)
    total_fwd_packets = db.Column(db.Float)
    total_bwd_packets = db.Column(db.Float)
    avg_packet_size = db.Column(db.Float)
    packet_length_mean = db.Column(db.Float)
    packet_length_var = db.Column(db.Float)
    max_packet_length = db.Column(db.Float)
    min_packet_length = db.Column(db.Float)
    fwd_packet_len_max = db.Column(db.Float)
    fwd_packet_len_min = db.Column(db.Float)
    fwd_packet_len_mean = db.Column(db.Float)
    fwd_packet_len_std = db.Column(db.Float)
    bwd_packet_len_mean = db.Column(db.Float)
    bwd_packet_len_std = db.Column(db.Float)
    flow_duration = db.Column(db.Float)
    flow_iat_mean = db.Column(db.Float)
    down_up_ratio = db.Column(db.Float)

    raw = db.Column(db.JSON)

class BlockedIP(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(64), nullable=False, index=True)
    blocked_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = db.Column(db.DateTime, nullable=False)
    reason = db.Column(db.String(128))
    target_agent = db.Column(db.String(128))


# ----------------------------------------------------------
# ML Prediction
# ----------------------------------------------------------
def ml_predict(data):
    cols = [
        "Flow Bytes/s", "Flow Packets/s", "Total Length of Fwd Packets",
        "Total Length of Bwd Packets", "Total Fwd Packets", "Total Backward Packets",
        "Average Packet Size", "Packet Length Mean", "Packet Length Variance",
        "Max Packet Length", "Min Packet Length", "Fwd Packet Length Max",
        "Fwd Packet Length Min", "Fwd Packet Length Mean", "Fwd Packet Length Std",
        "Bwd Packet Length Mean", "Bwd Packet Length Std", "Flow Duration",
        "Flow IAT Mean", "Down/Up Ratio"
    ]

    df = pd.DataFrame([[data.get(c, 0.0) for c in cols]], columns=cols)
    scaled = scaler.transform(df)
    selected = selector.transform(scaled)
    return float(model.predict_proba(selected)[0][1])


# ----------------------------------------------------------
# ROUTES
# ----------------------------------------------------------
@app.route("/")
def index():
    return redirect(url_for("dashboard"))


@app.route("/dashboard")
def dashboard():
    total = PacketLog.query.count()
    high = PacketLog.query.filter(PacketLog.status == "high_risk").count()
    suspicious = PacketLog.query.filter(PacketLog.status == "suspicious").count()
    recent = PacketLog.query.order_by(PacketLog.id.desc()).limit(10).all()

    return render_template(
        "dashboard.html",
        total=total,
        high=high,
        suspicious=suspicious,
        recent=recent,
        threshold_cfg=threshold_cfg
    )


@app.route("/logs")
def logs():
    page = int(request.args.get("page", 1))
    per = int(request.args.get("per", 50))
    q = PacketLog.query.order_by(PacketLog.id.desc())
    items = q.offset((page - 1) * per).limit(per).all()
    total = q.count()
    return render_template("logs.html", logs=items, page=page, per=per, total=total)


@app.route("/verification")
def verification():
    alerts = PacketLog.query.filter(
        PacketLog.status == "suspicious",
        PacketLog.verified == False
    ).order_by(PacketLog.id.asc()).limit(200).all()

    return render_template("verification.html", alerts=alerts)


@app.route("/blocked")
def blocked():
    now = datetime.now(timezone.utc)
    active = BlockedIP.query.filter(BlockedIP.expires_at > now).order_by(BlockedIP.expires_at.asc()).all()
    return render_template("blocked.html", blocked=active)


# ----------------------------------------------------------
# SETTINGS
# ----------------------------------------------------------
@app.route("/settings", methods=["GET", "POST"])
def settings():
    if request.method == "POST":
        try:
            threshold_cfg["threshold"] = float(request.form.get("auto_block_threshold"))
            with open(THRESH_CFG_PATH, "w") as f:
                json.dump(threshold_cfg, f)
        except:
            pass

        return redirect(url_for("settings"))

    return render_template("settings.html",
                           threshold_cfg=threshold_cfg,
                           manual_threshold=MANUAL_THRESHOLD)


# ----------------------------------------------------------
# RECEIVE PACKET FEATURES
# ----------------------------------------------------------
@app.route("/api/packet_features", methods=["POST"])
def receive_features():
    data = request.json

    try:
        prob = ml_predict(data)
    except Exception as e:
        return jsonify({"error": "invalid features", "detail": str(e)}), 400

    src_ip = data.get("src_ip")
    dst_ip = data.get("dst_ip")
    agent_id = data.get("agent_id")
    status = "normal"

    now = datetime.now(timezone.utc)

    # AUTO_T = float(threshold_cfg.get("threshold", 0.9))\
    AUTO_T = 0.4

    # AUTO BLOCK CASE
    if prob >= AUTO_T:
        status = "high_risk"
        duration_seconds = 5 * 60
        expires = now + timedelta(seconds=duration_seconds)

        blocked = BlockedIP(
            ip=src_ip,
            blocked_at=now,
            expires_at=expires,
            reason="auto",
            target_agent=agent_id
        )
        db.session.add(blocked)

        socketio.emit("block_ip", {
            "ip": src_ip,
            "duration": duration_seconds,
            "target_agent": agent_id,
            "target_ip": dst_ip
        })

    elif prob >= MANUAL_THRESHOLD and prob < AUTO_T:
        status = "suspicious"
        socketio.emit("suspicious", {
            "ip": src_ip,
            "prob": prob,
            "agent": agent_id,
            "dst": dst_ip
        })

    # Save packet log
    log = PacketLog(
        agent_id=agent_id,
        src_ip=src_ip,
        dst_ip=dst_ip,
        probability=prob,
        status=status,
        flow_bytes_s=data.get("Flow Bytes/s"),
        flow_packets_s=data.get("Flow Packets/s"),
        total_length_fwd=data.get("Total Length of Fwd Packets"),
        total_length_bwd=data.get("Total Length of Bwd Packets"),
        total_fwd_packets=data.get("Total Fwd Packets"),
        total_bwd_packets=data.get("Total Backward Packets"),
        avg_packet_size=data.get("Average Packet Size"),
        packet_length_mean=data.get("Packet Length Mean"),
        packet_length_var=data.get("Packet Length Variance"),
        max_packet_length=data.get("Max Packet Length"),
        min_packet_length=data.get("Min Packet Length"),
        fwd_packet_len_max=data.get("Fwd Packet Length Max"),
        fwd_packet_len_min=data.get("Fwd Packet Length Min"),
        fwd_packet_len_mean=data.get("Fwd Packet Length Mean"),
        fwd_packet_len_std=data.get("Fwd Packet Length Std"),
        bwd_packet_len_mean=data.get("Bwd Packet Length Mean"),
        bwd_packet_len_std=data.get("Bwd Packet Length Std"),
        flow_duration=data.get("Flow Duration"),
        flow_iat_mean=data.get("Flow IAT Mean"),
        down_up_ratio=data.get("Down/Up Ratio"),
        raw=data
    )

    db.session.add(log)
    db.session.commit()

    socketio.emit("new_log", {
        "id": log.id,
        "timestamp": log.timestamp.isoformat(),
        "agent": log.agent_id,
        "src_ip": log.src_ip,
        "dst_ip": log.dst_ip,
        "prob": log.probability,
        "status": log.status
    })

    return jsonify({"probability": prob, "status": status}), 200


# ----------------------------------------------------------
# VERIFICATION ACTIONS (DISCARD / BLOCK)
# ----------------------------------------------------------
@app.route("/api/verify", methods=["POST"])
def api_verify():
    data = request.json
    alert_id = int(data.get("id"))
    action = data.get("action")

    row = PacketLog.query.get(alert_id)
    if not row:
        return jsonify({"error": "not found"}), 404

    now = datetime.now(timezone.utc)

    if action == "discard":
        row.verified = True
        row.status = "normal"
        db.session.commit()
        return jsonify({"status": "discarded"})

    elif action == "block":
        row.verified = True
        row.status = "blocked"

        duration_seconds = 5 * 60
        expires = now + timedelta(seconds=duration_seconds)

        blocked = BlockedIP(
            ip=row.src_ip,
            blocked_at=now,
            expires_at=expires,
            reason="manual",
            target_agent=row.agent_id
        )
        db.session.add(blocked)
        db.session.commit()

        socketio.emit("manual_block", {
            "ip": row.src_ip,
            "duration": duration_seconds,
            "target_agent": row.agent_id,
            "target_ip": row.dst_ip
        })

        return jsonify({"status": "blocked"})

    return jsonify({"error": "invalid action"}), 400

@app.route("/packet/<int:pid>")
def packet_details(pid):
    row = PacketLog.query.get(pid)
    if not row:
        return "Packet not found", 404

    return render_template("packet_details.html", packet=row)

# ----------------------------------------------------------
# MANUAL BLOCK API
# ----------------------------------------------------------
@app.route("/api/block", methods=["POST"])
def api_block():
    ip = request.json.get("ip")
    target_agent = request.json.get("target_agent")

    if not ip:
        return jsonify({"error": "missing ip"}), 400

    now = datetime.now(timezone.utc)
    duration_seconds = int(request.json.get("duration", 300))
    expires = now + timedelta(seconds=duration_seconds)

    blocked = BlockedIP(
        ip=ip,
        blocked_at=now,
        expires_at=expires,
        reason="api",
        target_agent=target_agent
    )
    db.session.add(blocked)
    db.session.commit()

    socketio.emit("manual_block", {
        "ip": ip,
        "duration": duration_seconds,
        "target_agent": target_agent
    })

    return jsonify({"status": "blocked"})


# ----------------------------------------------------------
# START SERVER
# ----------------------------------------------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    socketio.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
