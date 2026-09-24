"""
run_all.py - single-command reproducible pipeline.

Runs the whole study in dependency order, from the raw TEP .RData files to the
results tables and the label-efficiency figure. One command, nothing to remember:

    python run_all.py              every step, roughly 2 h
    python run_all.py --tabla2     only what Table II needs, roughly 40 min

No step count is written here on purpose: the banner prints it from the lists
below, so it cannot drift from them. The times are wall-clock estimates for
planning, not measurements the paper rests on.

It stops at the first failing step and names it. Re-running is safe and, on the
same machine, yields the same metrics: fixed seeds, the partition saved to disk,
and the feature caches make them deterministic. Wall-clock timings (the cost
columns) are the exception: they are measured again on every run and change
with it. The test set stays SEALED throughout (no step opens the *_Testing
files for scoring).

Dependency order (the order of STEPS, and what each step reads from earlier ones):
  01 explore            standalone; understands the raw data
  02 make_partition     -> splits/ (read by 03, 07, checkpoint_datos)
  03 baselines          splits/
  04 classics_cv        -> results/dev_features.parquet, the feature cache read by
                           07, 08, 10, 11, 12, 14, 16, 17, 18, 20, 21
  05 domain_features    -> results/dev_domain_features.parquet (read by 06)
  06 domain_nonlinear   05's cache
  07 cv_audit           04's cache + splits/
  08 label_efficiency   04's cache
  10 inference_time     04's cache (auxiliary timing)
  11 train_dl           04's cache; -> results/models/*.pt, dev_windows.npy, dl_env.json
  12 agente_v1          04's cache, 11's models, kb/; -> logs/decisiones.jsonl,
                           agente_comparison.csv, agent_scores.npz, dev_windows_ext.npy
  13 plot_architecture  12's agente_env.json
  14 effect_sizes       04's cache, 11's models + windows, 12's log, kb/
  15 human_load         11's dl_comparison, 12's log + comparison, 14's per_fold_f1
  16 label_eff_agent    04's cache, 11's dl_env, 12's extended windows + env, kb/
  17 cost_table         04's cache, 11's windows + env, 12's env + comparison
  18 worst_errors       04's cache, 11's models, 12's log + windows + env, kb/
  19 tabla2_json        12's comparison, 14's per-fold files, 17's cost_table.csv
  20 case_separation    04's cache, 12's extended windows + log
  21 pr_auc             04's cache, 11's models + windows, 12's agent_scores.npz
  resultados            19's tabla2.json, 14's effect sizes, 15's human_load.csv
  09 plot               08's and 16's CSVs, so it runs after 16
  checkpoint_datos      splits/ (live data-checkpoint evidence)
"""
import os
import sys
import time
import subprocess

# HERE is where the step scripts live, BASE is the project. They are the same
# folder while the scripts sit at the root and differ once they move into code/,
# so this file works from either layout and so does every step it launches.
HERE = os.path.dirname(os.path.abspath(__file__))
BASE = HERE if os.path.isfile(os.path.join(HERE, "requirements.txt")) else os.path.dirname(HERE)

STEPS = [
    ("01_explore_data.py",             "Understand the raw data (schema, classes, quality)"),
    ("02_make_partition.py",           "Freeze the by-run partition (seed 42) to disk"),
    ("03_baselines.py",                "Trivial + Random Forest baselines on the frozen split"),
    ("04_classics_cv.py",              "Classic baselines with cross-validation (builds feature cache)"),
    ("05_domain_features.py",          "Domain-knowledge features + permutation importance"),
    ("06_domain_features_nonlinear.py", "Do domain features help nonlinear models? (RF/HistGB)"),
    ("07_cv_audit.py",                 "Cross-validation leakage audit (4 checks)"),
    ("08_label_efficiency.py",         "Label-efficiency curve (the measurable contribution)"),
    ("10_inference_time.py",           "Auxiliary timing of the classics (Table II cost is step 17)"),
    ("11_train_dl.py",                 "Deep learning v1: MLP + 1D-CNN under the pre-registered contract"),
    ("12_agente_v1.py",                "Copilot agent v1 + its ablation (Table II proposed row)"),
    ("13_plot_architecture.py",        "Render the architecture figure (Figure 1) from the run stamp"),
    ("14_effect_sizes.py",             "Paired fold-by-fold differences and effect sizes for every comparison"),
    ("15_human_load.py",               "Coverage, precision and what each arm costs the operator"),
    ("16_label_efficiency_agent.py",   "Label efficiency of the copilot and of the root-alarm rubric"),
    ("17_cost_table.py",               "Every cost cell of Table II, measured in one run"),
    ("18_worst_errors.py",             "The error that costs most: per class, and root-alarm recall at N"),
    ("19_tabla2_json.py",              "Consolidate every number of Table II into results/tabla2.json"),
    ("20_case_separation.py",          "How far apart the costly cases are, and the twin runs no window separates"),
    ("21_pr_auc.py",                   "PR-AUC for every row of Table II, as a check on the ranking"),
    ("resultados.py",                  "Generate Table II from that JSON and splice it into the paper"),
    # 09 draws both panels of the main figure, so it runs once 16 has produced the second one.
    ("09_plot_label_efficiency.py",    "Render the main figure, both panels (PDF/PNG)"),
    ("checkpoint_datos.py",            "Data checkpoint (live evidence)"),
]

RESULT_FILES = [
    "baseline_comparison.csv", "classics_cv_comparison.csv", "errors/best_model_confusion_matrix.csv",
    "domain_feature_importance.csv", "domain_nonlinear_comparison.csv", "cv_audit_single_vs_cv.csv",
    "label_efficiency_curve.csv", "label_efficiency_curve.pdf", "inference_time.csv",
    "dl_comparison.csv", "errors/dl_confusion_matrix.csv",
    "agente_comparison.csv", "logs/decisiones.jsonl", "architecture_loop.pdf",
    "per_fold_f1.csv", "effect_sizes.csv", "human_load.csv", "label_efficiency_agent.csv",
    "cost_table.csv", "errors/worst_errors.csv", "tabla2.json", "errors/case_separation.csv", "errors/twin_runs.csv",
    "pr_auc.csv",
]


NEEDS = {"numpy": "numpy", "pandas": "pandas", "sklearn": "scikit-learn",
         "pyreadr": "pyreadr", "pyarrow": "pyarrow", "matplotlib": "matplotlib"}


def torch_users():
    """Which steps import torch, read from the steps rather than remembered."""
    return sorted(s for s, _ in STEPS if "import torch" in
                  open(os.path.join(HERE, s), encoding="utf-8").read())


def preflight():
    """Actually import what the pipeline imports, before it starts.

    torch is deliberately absent from requirements.txt: its CPU build is served
    from PyTorch's own index rather than PyPI. But seven steps import it, and
    finding that out at step 11 costs the reader the hour that steps 01 to 10
    take.

    Every package here is IMPORTED, not merely located. This used to use
    importlib.util.find_spec, which answers a weaker question: whether the
    package can be found on disk. On 2026-09-19 a run on a Windows virtual
    machine passed that check and then died at step 11 with

        OSError: [WinError 1114] ... Error loading c10.dll

    torch was installed and findable; it could not load its own DLLs. The
    preflight exists precisely to catch that in the first second rather than the
    eighty-fourth minute, and find_spec cannot. Importing costs a few seconds,
    which is the right trade against an hour."""
    missing, broken = [], []
    for mod, pkg in NEEDS.items():
        try:
            __import__(mod)
        except ImportError:
            missing.append(pkg)
        except Exception as e:                    # installed, but cannot load
            broken.append((pkg, "%s: %s" % (type(e).__name__, e)))

    if missing:
        print("ABORT - missing package(s): " + ", ".join(missing))
        print("   python -m pip install -r requirements.txt")
        sys.exit(1)

    try:
        __import__("torch")
    except ImportError:
        users = torch_users()
        print("ABORT - torch is not installed, and %d of the %d steps import it:"
              % (len(users), len(STEPS)))
        for u in users:
            print("     " + u)
        print("")
        print("   It is not in requirements.txt because the CPU build comes from")
        print("   PyTorch's own index rather than PyPI:")
        print("")
        print("     python -m pip install torch==2.14.0 \\")
        print("       --index-url https://download.pytorch.org/whl/cpu")
        print("")
        print("   Checked here rather than at step 11, which is an hour in.")
        sys.exit(1)
    except Exception as e:
        broken.append(("torch", "%s: %s" % (type(e).__name__, e)))

    if broken:
        print("ABORT - installed but cannot be imported:")
        for pkg, err in broken:
            print("     %-14s %s" % (pkg, err))
        print("")
        if any(p == "torch" for p, _ in broken):
            print("   torch on Windows loads its own DLLs and needs the Microsoft")
            print("   Visual C++ Redistributable, which Python does not install:")
            print("     https://aka.ms/vs/17/release/vc_redist.x64.exe")
            print("   Both WinError 126 (the module could not be found) and 1114")
            print("   (its initialization failed), on any file under torch/lib,")
            print("   are almost always that: the DLL named in the message is")
            print("   there, the one it depends on is not. Two machines hit this")
            print("   on 2026-09-19, one with 1114 on c10.dll and one with 126 on")
            print("   shm.dll, and the redistributable fixed both. If it persists,")
            print("   the CPU may not expose the instruction set the wheel was")
            print("   built for, which a virtual machine can mask.")
            print("")
            print("   %d of the %d steps import torch, so the run stops here"
                  % (len(torch_users()), len(STEPS)))
            print("   rather than at step 11, an hour in.")
        sys.exit(1)


# The shortest path to the whole of Table II: every one of its eight rows, the
# cost column, and the rendered table, with nothing else. Derived from what the
# files actually read, not from taste, with one exception: 02. No later step of
# the subset reads splits/; 02 is there to rebuild the frozen partition and print
# its sha256 first, so a partition that moved shows before anything else runs.
#
#   02 rebuilds the split, prints its hash
#   04 classics + the feature cache 17 and 14 need
#   11 the two networks                    12 the agent and its ablation
#   14 per_fold_f1 / per_fold_recall3      15 human_load, which resultados reads
#   17 every cost cell                     19 collects it into tabla2.json
#   resultados.py renders and splices the table and the Results paragraph
#
# 15 is here because resultados.py reads results/human_load.csv for the last
# sentence of that paragraph. Without it the subset would regenerate the
# paragraph from a mix of this run and the committed one, which is exactly the
# kind of quiet mismatch the pipeline exists to prevent.
#
# What it leaves out is the auxiliary analysis, not part of the table: the data
# description, the domain features, the leakage audit, label efficiency, the
# figures, the error tables, PR-AUC and the data checkpoint. Roughly 40 min on
# the reference machine against roughly 2 h for everything, both wall-clock and
# both only as good as the processor they were measured on.
SOLO_TABLA2 = ["02_make_partition.py", "04_classics_cv.py", "11_train_dl.py",
               "12_agente_v1.py", "14_effect_sizes.py", "15_human_load.py",
               "17_cost_table.py", "19_tabla2_json.py", "resultados.py"]


def elegir_pasos(argv):
    """The steps to run, and a label for them. The subset cannot drift from STEPS."""
    if "--tabla2" not in argv:
        return STEPS, "ALL %d STEPS" % len(STEPS)
    porNombre = dict(STEPS)
    falta = [s for s in SOLO_TABLA2 if s not in porNombre]
    assert not falta, "SOLO_TABLA2 names steps the pipeline does not have: %s" % falta
    return ([(s, porNombre[s]) for s in SOLO_TABLA2],
            "TABLE II COMPLETE, %d of the %d steps" % (len(SOLO_TABLA2), len(STEPS)))


def main():
    pasos, etiqueta = elegir_pasos(sys.argv)
    print("=" * 80)
    print("REPRODUCIBLE PIPELINE  -  TEP root-cause identification")
    print(f"python {sys.version.split()[0]}   |   project: {BASE}")
    if HERE != BASE:
        print(f"steps: {HERE}")
    if len(pasos) != len(STEPS):
        print("--tabla2: only what Table II needs, %d of the %d steps"
              % (len(pasos), len(STEPS)))
    print("=" * 80)

    preflight()

    # fail early if a step file is missing
    missing = [s for s, _ in pasos if not os.path.exists(os.path.join(HERE, s))]
    if missing:
        print("ABORT - missing script(s):", ", ".join(missing))
        sys.exit(1)

    t0 = time.time()
    timings = []
    for i, (script, desc) in enumerate(pasos, 1):
        print(f"\n{'-' * 80}\n[{i}/{len(pasos)}] {script}\n    {desc}\n{'-' * 80}", flush=True)
        t = time.time()
        result = subprocess.run([sys.executable, os.path.join(HERE, script)], cwd=BASE)  # streams child output live
        dt = time.time() - t
        timings.append((script, dt))
        if result.returncode != 0:
            print(f"\n!! STEP FAILED: {script} (exit {result.returncode}) after {dt:.0f}s. Stopping.")
            print(f"   Fix the error shown above, then re-run:  "
                  f"python {os.path.relpath(__file__, BASE)}")
            sys.exit(result.returncode)
        print(f"    OK in {dt:.0f}s")

    total = time.time() - t0
    print("\n" + "=" * 80)
    print(f"{etiqueta} OK  in {total:.0f}s ({total/60:.1f} min)")
    print("per-step time:")
    for s, dt in timings:
        print(f"    {s:<34}{dt:6.0f}s")
    # with --tabla2 the auxiliary files are not produced and listing them as
    # missing would read like a failure, so the list follows what was asked for
    esperados = (["tabla2.json", "cost_table.csv", "agente_comparison.csv",
                  "per_fold_f1.csv", "dl_comparison.csv", "classics_cv_comparison.csv"]
                 if len(pasos) != len(STEPS) else RESULT_FILES)
    print("\nresults table / figure produced (in results/):")
    for f in esperados:
        ok = os.path.exists(os.path.join(BASE, "results", f))
        print(f"    [{'OK' if ok else '--'}] results/{f}")
    if len(pasos) != len(STEPS):
        print("\n    Table II is in paper/tabla2.tex. The auxiliary analyses, the")
        print("    figures and the error tables need the full run.")
    print("\nTest set: SEALED throughout (no *_Testing file opened for scoring).")
    print("=" * 80)


if __name__ == "__main__":
    main()
