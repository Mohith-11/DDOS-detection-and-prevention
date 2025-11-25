import psycopg2
import pandas as pd
import joblib
import json
from sklearn.preprocessing import RobustScaler
from sklearn.feature_selection import VarianceThreshold
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import precision_recall_curve
from imblearn.over_sampling import SMOTE
from datetime import datetime

# -------------------------
# 1. Load logs from PostgreSQL
# -------------------------
def load_logs():
    conn = psycopg2.connect(
        dbname="ddos_logs",
        user="postgres",
        password="your_password",
        host="localhost",
        port="5432"
    )
    query = """
        SELECT flow_bytes, flow_packets, total_fwd_len, total_bwd_len,
               total_fwd_pkts, total_bwd_pkts, avg_pkt_size,
               pkt_len_mean, pkt_len_var, max_pkt_len, min_pkt_len,
               fwd_pkt_len_max, fwd_pkt_len_min, fwd_pkt_len_mean,
               fwd_pkt_len_std, bwd_pkt_len_mean, bwd_pkt_len_std,
               flow_duration, flow_iat_mean, down_up_ratio,
               prediction AS label
        FROM flow_logs
        ORDER BY timestamp DESC
        LIMIT 50000;
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# -------------------------
# 2. Load old base dataset
# -------------------------
def load_base_data():
    return pd.read_csv("reduced_dos_ddos_dataset.csv")

# -------------------------
# 3. Merge + preprocess
# -------------------------
def preprocess(df):
    X = df.drop("label", axis=1)
    y = df["label"]

    X.replace([float("inf"), -float("inf")], pd.NA, inplace=True)
    X.fillna(X.median(), inplace=True)

    scaler = RobustScaler()
    X_scaled = scaler.fit_transform(X)

    selector = VarianceThreshold(0.01)
    X_sel = selector.fit_transform(X_scaled)

    return X_sel, y, scaler, selector

# -------------------------
# 4. Train Random Forest
# -------------------------
def train_model(X, y):
    sm = SMOTE(sampling_strategy=0.6, random_state=42)
    X_res, y_res = sm.fit_resample(X, y)

    model = RandomForestClassifier(
        n_estimators=150,
        max_depth=20,
        min_samples_leaf=2,
        max_features='log2',
        class_weight={0:1, 1:3},
        n_jobs=-1,
        random_state=42
    )
    model.fit(X_res, y_res)
    return model

# -------------------------
# 5. Tune threshold
# -------------------------
def tune_threshold(model, X, y):
    probs = model.predict_proba(X)[:,1]
    prec, rec, thresh = precision_recall_curve(y, probs)
    f1s = (2 * prec * rec) / (prec + rec + 1e-9)
    best_idx = f1s.argmax()
    return float(thresh[best_idx])

# -------------------------
# 6. Save new model + backup old
# -------------------------
def save_model(model, scaler, selector, threshold):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")

    # Backup
    joblib.dump(model, f"models_backup/model_{timestamp}.pkl")

    # Replace main
    joblib.dump(model, "model.pkl")
    joblib.dump(scaler, "scaler.pkl")
    joblib.dump(selector, "selector.pkl")
    json.dump({"threshold": threshold}, open("threshold.json", "w"))

# -------------------------
# MAIN PIPELINE
# -------------------------
def main():
    print("\n🔄 Loading logs from PostgreSQL...")
    new_logs = load_logs()

    print("📂 Loading base dataset...")
    base = load_base_data()

    df = pd.concat([base, new_logs]).sample(frac=1, random_state=42)

    print("⚙️ Preprocessing...")
    X, y, scaler, selector = preprocess(df)

    print("🌲 Training Random Forest...")
    model = train_model(X, y)

    print("🎯 Tuning threshold...")
    threshold = tune_threshold(model, X, y)

    print("💾 Saving model...")
    save_model(model, scaler, selector, threshold)

    print("\n✅ Retraining completed successfully!")
    print(f"New threshold: {threshold:.3f}")

if __name__ == "__main__":
    main()
