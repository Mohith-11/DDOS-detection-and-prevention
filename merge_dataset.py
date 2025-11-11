import os
import glob
import sys
import pandas as pd

def resolve_csv(path):
    if os.path.isdir(path):
        candidates = glob.glob(os.path.join(path, "*.csv"))
        if not candidates:
            raise FileNotFoundError(f"No CSV found inside directory: {path}")
        return candidates[0]
    return path

def ensure_readable(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    if not os.path.isfile(path):
        raise IsADirectoryError(f"Not a file: {path}")
    if not os.access(path, os.R_OK):
        raise PermissionError(f"Permission denied: {path}")
    return True

paths = {
    "wednesday": "Wednesday-workingHours.pcap_ISCX.csv",
    "friday_morning": "Friday-WorkingHours-Morning.pcap_ISCX.csv",
    "friday_ddos": "Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv",
}

loaded = {}
for key, p in paths.items():
    try:
        real = resolve_csv(p)
        ensure_readable(real)
        loaded[key] = pd.read_csv(real, low_memory=False)
        print(f"✅ Loaded: {real}")
    except Exception as e:
        print(f"❌ Cannot load {p}: {e}")
        print(f"   path='{os.path.abspath(p)}', exists={os.path.exists(p)}, is_dir={os.path.isdir(p)}, readable={os.access(p, os.R_OK)}")
        sys.exit(1)

wednesday = loaded["wednesday"]
friday_morning = loaded["friday_morning"]
friday_ddos = loaded["friday_ddos"]

# Strip column names and remove duplicate columns
for df in [wednesday, friday_morning, friday_ddos]:
    df.columns = df.columns.str.strip()
    df.drop(columns=df.columns[df.columns.duplicated()], inplace=True)
    df.dropna(inplace=True)

# Combine datasets
combined_df = pd.concat([wednesday, friday_morning, friday_ddos], ignore_index=True)

# Label: 1 for DoS/DDoS, 0 for others
if "Label" in combined_df.columns:
    combined_df["Label"] = combined_df["Label"].apply(
        lambda x: 1 if isinstance(x, str) and ("DoS" in x or "DDoS" in x) else 0
    )
else:
    print("⚠️ 'Label' column not found in combined dataframe.")

# Remove duplicate rows
before = combined_df.shape[0]
combined_df.drop_duplicates(inplace=True)
after = combined_df.shape[0]
print(f"🧹 Removed {before - after} duplicate rows.")

# Shuffle
combined_df = combined_df.sample(frac=1, random_state=42).reset_index(drop=True)

# Save
out = "combined_dos_ddos_dataset.csv"
combined_df.to_csv(out, index=False)
print(f"✅ Final dataset saved as: {out}")
