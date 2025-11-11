import pandas as pd

# Top 20 influential features
selected_features = [
    "Flow Bytes/s", "Flow Packets/s", "Total Length of Fwd Packets", "Total Length of Bwd Packets",
    "Total Fwd Packets", "Total Backward Packets", "Average Packet Size", "Packet Length Mean",
    "Packet Length Variance", "Max Packet Length", "Min Packet Length", "Fwd Packet Length Max",
    "Fwd Packet Length Min", "Fwd Packet Length Mean", "Fwd Packet Length Std",
    "Bwd Packet Length Mean", "Bwd Packet Length Std", "Flow Duration", "Flow IAT Mean",
    "Down/Up Ratio", "Label"
]

# Load full dataset
df = pd.read_csv("combined_dos_ddos_dataset.csv")

# Keep only selected features
df_reduced = df[selected_features].copy()

# Drop rows with any missing or infinite values
df_reduced.replace([float("inf"), float("-inf")], pd.NA, inplace=True)
df_reduced.dropna(inplace=True)

# Save reduced dataset
df_reduced.to_csv("reduced_dos_ddos_dataset.csv", index=False)
print("✅ Saved reduced dataset as: reduced_dos_ddos_dataset.csv")
