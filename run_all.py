"""
run_all.py - single-command reproducible pipeline (reproducibility rule, point 5).

Runs the whole study in dependency order, from the raw TEP .RData files to the
results tables and the label-efficiency figure. One command, nothing to remember:

    python run_all.py

It stops at the first failing step and names it. Re-running is safe and yields the
same numbers: fixed seeds, the partition saved to disk, and the feature caches make
every step deterministic. The test set stays SEALED throughout (no step opens the
*_Testing files for scoring).

Dependency order (why this order):
  01 explore            (standalone; understands the raw data)
  02 make_partition     -> writes splits/ (needed by 03, 07, checkpoint)
  03 baselines          (needs the frozen partition)
  04 classics_cv        -> builds results/dev_features.parquet (needed by 07, 08)
  05 domain_features    -> builds results/dev_domain_features.parquet (needed by 06)
  06 domain_nonlinear   (needs 05's cache)
  07 cv_audit           (needs 04's cache + 02's partition)
  08 label_efficiency   (needs 04's cache)
  09 plot               (needs 08's CSV)
  11 train_dl           (needs 04's cache; extracts + caches the raw windows)
  12 agente_v1          (needs 11's saved models + kb/; runs the loop and its ablation)
  checkpoint_datos      (needs 02's partition; live data-checkpoint evidence)
"""
import os
import sys
import time
import subprocess

BASE = os.path.dirname(os.path.abspath(__file__))

STEPS = [
    ("01_explore_data.py",             "Understand the raw data (schema, classes, quality)"),
    ("02_make_partition.py",           "Freeze the by-run partition (seed 42) to disk"),
    ("03_baselines.py",                "Trivial + Random Forest baselines on the frozen split"),
    ("04_classics_cv.py",              "Classic baselines with cross-validation (builds feature cache)"),
    ("05_domain_features.py",          "Domain-knowledge features + permutation importance"),
    ("06_domain_features_nonlinear.py", "Do domain features help nonlinear models? (RF/HistGB)"),
    ("07_cv_audit.py",                 "Cross-validation leakage audit (4 checks)"),
    ("08_label_efficiency.py",         "Label-efficiency curve (the measurable contribution)"),
    ("09_plot_label_efficiency.py",    "Render the label-efficiency figure (PDF/PNG)"),
    ("10_inference_time.py",           "Training time + inference latency (Table II cost)"),
    ("11_train_dl.py",                 "Deep learning v1: MLP + 1D-CNN under the Week-2 contract"),
    ("12_agente_v1.py",                "Copilot agent v1 + its ablation (Table II proposed row)"),
    ("13_plot_architecture.py",        "Render the architecture figure (Figure 1) from the run stamp"),
    ("14_effect_sizes.py",             "Paired fold-by-fold differences and effect sizes for every comparison"),
    ("15_human_load.py",               "Coverage, precision and what each arm costs the operator"),
    ("checkpoint_datos.py",            "Data checkpoint (live evidence)"),
]

RESULT_FILES = [
    "baseline_comparison.csv", "classics_cv_comparison.csv", "best_model_confusion_matrix.csv",
    "domain_feature_importance.csv", "domain_nonlinear_comparison.csv", "cv_audit_single_vs_cv.csv",
    "label_efficiency_curve.csv", "label_efficiency_curve.pdf", "inference_time.csv",
    "dl_comparison.csv", "dl_confusion_matrix.csv",
    "agente_comparison.csv", "logs/decisiones.jsonl",
]


def main():
    print("=" * 80)
    print("REPRODUCIBLE PIPELINE  -  TEP root-cause identification")
    print(f"python {sys.version.split()[0]}   |   base: {BASE}")
    print("=" * 80)

    # fail early if a step file is missing
    missing = [s for s, _ in STEPS if not os.path.exists(os.path.join(BASE, s))]
    if missing:
        print("ABORT - missing script(s):", ", ".join(missing))
        sys.exit(1)

    t0 = time.time()
    timings = []
    for i, (script, desc) in enumerate(STEPS, 1):
        print(f"\n{'-' * 80}\n[{i}/{len(STEPS)}] {script}\n    {desc}\n{'-' * 80}", flush=True)
        t = time.time()
        result = subprocess.run([sys.executable, script], cwd=BASE)  # streams child output live
        dt = time.time() - t
        timings.append((script, dt))
        if result.returncode != 0:
            print(f"\n!! STEP FAILED: {script} (exit {result.returncode}) after {dt:.0f}s. Stopping.")
            print("   Fix the error shown above, then re-run:  python run_all.py")
            sys.exit(result.returncode)
        print(f"    OK in {dt:.0f}s")

    total = time.time() - t0
    print("\n" + "=" * 80)
    print(f"ALL {len(STEPS)} STEPS OK  in {total:.0f}s ({total/60:.1f} min)")
    print("per-step time:")
    for s, dt in timings:
        print(f"    {s:<34}{dt:6.0f}s")
    print("\nresults table / figure produced (in results/):")
    for f in RESULT_FILES:
        ok = os.path.exists(os.path.join(BASE, "results", f))
        print(f"    [{'OK' if ok else '--'}] results/{f}")
    print("\nTest set: SEALED throughout (no *_Testing file opened for scoring).")
    print("=" * 80)


if __name__ == "__main__":
    main()
