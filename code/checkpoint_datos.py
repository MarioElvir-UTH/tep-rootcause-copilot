"""
Data checkpoint: raw files to screen, in one command.

Shows, live:
  1. that the data loads
  2. how many samples and how many classes there are
  3. five example rows with their ground truth (faultNumber)
  4. that the frozen partition exists in the repository, as a file on disk with
     its integrity hash

The simulator is not run here. These are the pre-generated Tennessee Eastman runs
of Rieth et al. (2017), which ship with their ground truth.
"""
import os, gc, json, hashlib, sys
import pyreadr
import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
if not os.path.isfile(os.path.join(BASE, "requirements.txt")):
    BASE = os.path.dirname(BASE)      # the scripts live in code/, the project one level up
DATA = os.path.join(BASE, "dataverse_files")
SPLITS = os.path.join(BASE, "splits")
FILES = ["TEP_FaultFree_Training.RData", "TEP_FaultFree_Testing.RData",
         "TEP_Faulty_Training.RData", "TEP_Faulty_Testing.RData"]

print("=" * 90)
print("DATA CHECKPOINT  -  Tennessee Eastman Process (Rieth et al., 2017)")
print("=" * 90)

# ---------- (1) data loads + (2) samples and classes ----------
print("\n[1] THE DATA LOADS  +  [2] HOW MANY SAMPLES / CLASSES")
print("-" * 90)
total_rows, classes_seen, total_runs = 0, set(), 0
per_file = []
for f in FILES:
    path = os.path.join(DATA, f)
    res = pyreadr.read_r(path)
    df = res[list(res.keys())[0]]
    del res
    rows = len(df)
    cls = sorted(df["faultNumber"].astype(int).unique().tolist())
    runs = df[["faultNumber", "simulationRun"]].drop_duplicates().shape[0]
    total_rows += rows
    classes_seen |= set(cls)
    total_runs += runs
    per_file.append((f, rows, len(cls), runs))
    print(f"  loaded OK: {f:<32} rows={rows:>10,}  classes={len(cls):>2}  runs={runs:>5,}")
    del df
    gc.collect()

print("-" * 90)
print(f"  TOTAL samples (rows)         : {total_rows:,}")
print(f"  TOTAL classes (faultNumber)  : {len(classes_seen)}  -> {sorted(classes_seen)}  (0=normal, 1-20=faults)")
print(f"  TOTAL simulation runs        : {total_runs:,}")

# ---------- (3) five example rows with ground truth ----------
print("\n[3] FIVE EXAMPLE ROWS (with ground truth = faultNumber)")
print("-" * 90)
res = pyreadr.read_r(os.path.join(DATA, "TEP_Faulty_Training.RData"))
df = res[list(res.keys())[0]]; del res
ex = df[(df["faultNumber"] == 1) & (df["simulationRun"] == 1) & (df["sample"].between(19, 23))]
cols = ["faultNumber", "simulationRun", "sample", "xmeas_1", "xmeas_7", "xmeas_9", "xmv_10"]
print("  (fault 1, run 1, around the documented onset at sample 21; fault is active for sample >= 21)")
print(ex[cols].to_string(index=False))
print("  ground truth: faultNumber is the root-cause label, constant within a run; here = 1.")
del df, ex; gc.collect()

# ---------- (4) frozen partition exists in the repo ----------
print("\n[4] THE FROZEN PARTITION EXISTS IN THE REPOSITORY")
print("-" * 90)
man_path = os.path.join(SPLITS, "partition_manifest.csv")
meta_path = os.path.join(SPLITS, "partition_meta.json")
print(f"  file exists: {man_path}  -> {os.path.exists(man_path)}")
print(f"  file exists: {meta_path}  -> {os.path.exists(meta_path)}")
integrity = False
if os.path.exists(man_path) and os.path.exists(meta_path):
    sha = hashlib.sha256(open(man_path, "rb").read()).hexdigest()[:16]
    meta = json.load(open(meta_path, encoding="utf-8"))
    integrity = sha == meta["manifest_sha256_16"]
    man = pd.read_csv(man_path)
    print(f"  manifest sha256[:16] recomputed = {sha}  |  stored in meta = {meta['manifest_sha256_16']}  "
          f"-> integrity {'MATCH' if integrity else 'MISMATCH'}")
    print(f"  seed = {meta['seed']}  |  split by run (grouping) = {meta['grouping'][:60]}...")
    counts = man.groupby('split').size()
    print(f"  run assignments: total={len(man):,}  train={counts.get('train',0):,}  "
          f"val={counts.get('val',0):,}  test={counts.get('test',0):,}  (test SEALED: counted above, never scored)")

print("\n" + "=" * 90)
if not integrity:
    print("CHECKPOINT STATUS: FAILED  -  the frozen partition is missing or its hash does not")
    print("match partition_meta.json. Rebuild it with code/02_make_partition.py.")
    print("=" * 90)
    sys.exit(1)
print("CHECKPOINT STATUS: PASSED  -  data loads, samples/classes counted, 5 examples shown,")
print("frozen partition present and integrity-checked.")
print("=" * 90)
