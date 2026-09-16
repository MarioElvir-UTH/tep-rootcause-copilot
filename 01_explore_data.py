"""
S1 - Step 1: Understand the data before modeling (no training).
TEP dataset (Rieth et al., 2017, DOI 10.7910/DVN/6C3JR1), .RData format.
Reports, per file: rows, classes (faultNumber), per-run and per-sample balance,
samples per run, missing/duplicate/corrupt checks, and representative examples.
Every number comes from the data; nothing is estimated.
"""
import os, gc
import pyreadr
import pandas as pd
import numpy as np

_ROOT = os.path.dirname(os.path.abspath(__file__))
if not os.path.isfile(os.path.join(_ROOT, "requirements.txt")):
    _ROOT = os.path.dirname(_ROOT)      # the scripts live in code/, the project one level up
DATA = os.path.join(_ROOT, "dataverse_files")
FILES = [
    "TEP_FaultFree_Training.RData",
    "TEP_FaultFree_Testing.RData",
    "TEP_Faulty_Training.RData",
    "TEP_Faulty_Testing.RData",
]
KEYCOLS = ["faultNumber", "simulationRun", "sample"]
# Documented fault onset (Rieth): 1 h into training, 8 h into testing; sampling every 3 min.
ONSET = {"Training": 20, "Testing": 160}  # normal samples before the fault (metadata, not a column)


def report(fname):
    path = os.path.join(DATA, fname)
    size_mb = os.path.getsize(path) / 1e6
    print("=" * 80)
    print(f"FILE: {fname}   ({size_mb:.0f} MB)")
    print("=" * 80)

    res = pyreadr.read_r(path)
    key = list(res.keys())[0]
    df = res[key]
    del res
    print(f"R object: {key!r}   shape: {df.shape[0]:,} rows x {df.shape[1]} cols")

    fn = df["faultNumber"].astype("int64")
    faults = sorted(fn.unique().tolist())
    print(f"faultNumber classes present: {faults}  (n_classes = {len(faults)})")

    vc = fn.value_counts().sort_index()
    print("\n-- rows (samples) per faultNumber [per-sample balance] --")
    print(vc.to_string())

    ids = pd.DataFrame({"f": fn.values, "r": df["simulationRun"].astype("int64").values})
    runs_per_fault = ids.groupby("f")["r"].nunique()
    print("\n-- runs (simulationRun) per faultNumber [per-run balance] --")
    print(runs_per_fault.to_string())
    total_runs = ids.drop_duplicates(["f", "r"]).shape[0]
    print(f"total runs = {total_runs:,}")

    spr = ids.groupby(["f", "r"]).size()
    distinct_spr = sorted(pd.unique(spr).tolist())
    print(f"\nsamples per run: min={spr.min()}, max={spr.max()}, distinct={distinct_spr}")

    # normal vs fault within faulty runs (derived from documented onset, not from a column)
    if "Faulty" in fname:
        onset = ONSET["Training"] if "Training" in fname else ONSET["Testing"]
        n = int(spr.max())
        print(f"normal-vs-fault WITHIN a faulty run (from documented onset, sample>{onset} = fault):")
        print(f"   normal samples/run = {onset} ({onset/n:.1%}), fault samples/run = {n-onset} ({(n-onset)/n:.1%})")
        print("   NOTE: faultNumber is constant within a run; the data has no onset marker.")
    del ids, spr

    miss = {c: int(df[c].isnull().sum()) for c in df.columns}
    nmiss = sum(miss.values())
    print(f"\nmissing (NaN) total: {nmiss}")
    if nmiss:
        print("   ", {c: v for c, v in miss.items() if v > 0})

    dup_key = int(df.duplicated(subset=KEYCOLS).sum())
    print(f"duplicated rows on key {KEYCOLS}: {dup_key}")

    numcols = [c for c in df.columns if np.issubdtype(df[c].dtype, np.floating)]
    ninf = 0
    for c in numcols:
        ninf += int(np.isinf(df[c].to_numpy()).sum())
    print(f"non-finite (inf) across {len(numcols)} float columns: {ninf}")

    # 5 representative rows around the fault onset (only for faulty training)
    if fname == "TEP_Faulty_Training.RData":
        onset = ONSET["Training"]
        ex = df[(df["faultNumber"] == 1) & (df["simulationRun"] == 1)
                & (df["sample"].between(onset - 1, onset + 3))]
        print("\n5 representative rows (fault 1, run 1, around onset):")
        print(ex[["faultNumber", "simulationRun", "sample", "xmeas_1", "xmeas_9", "xmv_1"]].to_string(index=False))

    del df, fn, vc, runs_per_fault
    gc.collect()
    print()


if __name__ == "__main__":
    for f in FILES:
        try:
            report(f)
        except MemoryError:
            print(f"!! MemoryError on {f}: too large to load fully in RAM; process fault-by-fault or use R.\n")
        except Exception as e:
            print(f"!! Error on {f}: {type(e).__name__}: {e}\n")
    print("DONE.")
