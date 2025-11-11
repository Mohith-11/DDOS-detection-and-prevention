import pandas as pd
import os
import glob
import sys

# List of your CICIDS2017 CSVs
file_paths = {
    "Wednesday": "Wednesday-workingHours.pcap_ISCX.csv",
    "Friday Morning": "Friday-WorkingHours-Morning.pcap_ISCX.csv",
    "Friday DDoS": "Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv"
}

cleaned_dfs = {}

for name, path in file_paths.items():
    try:
        # If path is a directory, try to find a CSV file inside it
        real_path = path
        if os.path.isdir(path):
            candidates = glob.glob(os.path.join(path, "*.csv"))
            if candidates:
                real_path = candidates[0]
            else:
                raise FileNotFoundError(f"No CSV found inside directory '{path}'")

        if not os.path.exists(real_path):
            raise FileNotFoundError(f"File not found: {real_path}")
        if not os.path.isfile(real_path):
            raise IsADirectoryError(f"Not a file: {real_path}")
        if not os.access(real_path, os.R_OK):
            raise PermissionError(f"Permission denied: {real_path}")

        # Load with low_memory=False to prevent type warning
        df = pd.read_csv(real_path, low_memory=False)

        # Clean: strip whitespace & remove duplicate columns
        df.columns = df.columns.str.strip()
        df = df.loc[:, ~df.columns.duplicated()]  # drop dupes

        cleaned_dfs[name] = df
        print(f"✅ Loaded and cleaned: {name} ({real_path})")

    except Exception as e:
        print(f"❌ Failed to load {name}: {e}")
        print(f"   path='{os.path.abspath(path)}', is_dir={os.path.isdir(path)}, exists={os.path.exists(path)}, readable={os.access(path, os.R_OK)}")

# Guard: stop if no files loaded to avoid IndexError
if not cleaned_dfs:
    print("\nNo datasets were loaded. Fix file locations/permissions and retry.")
    print(f"Current working directory: {os.getcwd()}")
    for n, p in file_paths.items():
        print(f" - {n}: {p} -> exists={os.path.exists(p)}, is_dir={os.path.isdir(p)}, readable={os.access(p, os.R_OK)}")
    sys.exit(1)

# Compare columns between datasets
names = list(cleaned_dfs.keys())
base_cols = cleaned_dfs[names[0]].columns

all_match = True
for name in names[1:]:
    cols = cleaned_dfs[name].columns
    diff = set(base_cols).symmetric_difference(set(cols))
    if len(diff) > 0:
        print(f"\n❌ Mismatch between {names[0]} and {name}:")
        print(list(diff))
        all_match = False
    else:
        print(f"✅ Columns match: {names[0]} and {name}")

if all_match:
    print("\n🎉 All datasets have matching columns and are safe to combine!")
else:
    print("\n⚠️ One or more datasets have column mismatches. Please resolve before combining.")
