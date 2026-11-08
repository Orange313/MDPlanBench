"""Independent CPU reconstruction from only the new run's frozen portable inputs."""
import common as C
from pathlib import Path
import os
import shutil
import subprocess

dest=Path("${RUNTIME_DIR}")
dest.mkdir()
art="artifacts/"+C.RUN+"/"
report="reports/"+C.RUN+"/"
files=[art+"EX0/"+x.name for x in (C.ART/"EX0").glob("*.npz")]
files += [art+x for x in [
    "EX0/domains.json","EX1/predictions_and_allocations.json","EX3/frozen_mixtures.json",
    "GPU/process_03/partial.jsonl"]]
for proc in (6,8,9):
    files += [art+f"GPU/process_{proc:02d}/"+name for name in ("requests.csv","completed.json")]
files += [report+"EX0/fresh_CPU_feature_timings.csv",report+"EX1/CPU_inference_raw.csv"]
files += ["scripts/"+C.RUN+"/"+x for x in ["common.py","analyze.py","plot_results.py"]]
files += ["scripts/icde_eab_validation_005/frontier_math.py"]
for rel in files:
    target=dest/rel
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(C.ROOT/rel,target)
env=os.environ.copy()
env["MDROUTER_ROOT"]=str(dest)
env.pop("MDROUTER_REPORT_ROOT",None)
env["OPENBLAS_NUM_THREADS"]="1"
env["OMP_NUM_THREADS"]="1"
python="${RUNTIME_DIR}/bin/python"
for script in ("analyze.py","plot_results.py"):
    with (C.ART/("replay_003_"+script+".log")).open("x") as log:
        subprocess.run([python,str(dest/"scripts"/C.RUN/script)],cwd=dest,
                       env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
reference=C.ROOT/"reports"/C.RUN/"analysis_003"
replay=dest/"reports"/C.RUN
checks=[]
for stage in ("EX1","EX2","EX3","figures"):
    for p in (reference/stage).iterdir():
        if p.suffix not in (".csv",".pdf",".png"):
            continue
        candidate=replay/stage/p.name
        checks.append(dict(path=str(p.relative_to(reference)),expected=C.sha(p),
                           actual=C.sha(candidate),identical=C.sha(p)==C.sha(candidate)))
C.table(C.REPORT/"EX7/new_run_cpu_replay_002.csv",checks)
C.write(C.REPORT/"EX7/new_run_cpu_replay_002.json",dict(
    status="PASS" if all(r["identical"] for r in checks) else "MISMATCH",
    root=str(dest),fresh_environment="public lock Python3.11 EX7 independent environment",
    inputs={rel:C.sha(dest/rel) for rel in files},outputs=checks,GPU=0))
assert all(r["identical"] for r in checks)
print("NEW_REPLAY_ALL_EXACT",len(checks),flush=True)
