"""Exclusive run outputs and explicit allowed-input registration."""
import csv
import datetime
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import numpy as np

ROOT = Path(os.environ.get("MDROUTER_ROOT", "${PROJECT_ROOT}"))
RUN = "icde_eab_review_strengthening_021"
ART = ROOT / "artifacts" / RUN
REPORT = Path(os.environ.get("MDROUTER_REPORT_ROOT", str(ROOT / "reports" / RUN)))
SEED = 20261105
PLANS = ["Full-Visual", "BM25-R50", "BM25-R100", "BM25"]
CAT = np.array([0, 2, 3])
DOM = ["vidore_v3_hr", "vidore_v3_finance_en", "vidore_v3_industrial", "Pharmaceuticals"]
READS = {}
INPUT = READS
A = ART


def stamp():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def clean(value):
    if isinstance(value, np.ndarray):
        return clean(value.tolist())
    if isinstance(value, np.generic):
        return clean(value.item())
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(v) for v in value]
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf8") as stream:
        stream.write(json.dumps(clean(value), ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def prose(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf8") as stream:
        stream.write(value)


def table(path, rows):
    rows = list(rows)
    fields = list(dict.fromkeys(key for row in rows for key in row))
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", newline="", encoding="utf8") as stream:
        out = csv.DictWriter(stream, fieldnames=fields)
        out.writeheader()
        for row in rows:
            out.writerow({k: json.dumps(clean(v)) if isinstance(v, (list, dict, np.ndarray)) else clean(v)
                          for k, v in row.items()})


def denied(path):
    text = str(path).replace("\\", "/").lower()
    return any(x in text for x in ["/sealed/", "b-l_qrels", "b_l_outcomes",
        "pharma_qrels.parquet", "final_test_queries", "computer_science",
        "eval_outcomes", "eval_qrels", "cal_outcomes", "cal_qrels"])


def protect(event, args):
    if event == "open" and args and isinstance(args[0], str) and denied(args[0]):
        raise PermissionError("SEALED READ DENIED")


sys.addaudithook(protect)


def load(relative, role="AUTHORIZED_FROZEN_INPUT"):
    path = Path(relative)
    if not path.is_absolute():
        path = ROOT / path
    if denied(path):
        raise PermissionError(path)
    data = path.read_bytes()
    READS[str(path)] = {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
    with (ART / "reads.jsonl").open("a") as stream:
        stream.write(json.dumps({"time": stamp(), "path": str(path), **READS[str(path)]}) + "\n")
    if path.suffix == ".json":
        return json.loads(data)
    if path.suffix == ".csv":
        return list(csv.DictReader(io.StringIO(data.decode("utf-8-sig"))))
    if path.suffix == ".npz":
        with np.load(io.BytesIO(data), allow_pickle=False) as z:
            return {name: z[name].copy() for name in z.files}
    return data.decode("utf8")


def seal(stage):
    outputs = {}
    for base in (ART / stage, REPORT / stage):
        if base.exists():
            outputs.update({str(p.relative_to(ROOT)): {"sha256": sha(p), "bytes": p.stat().st_size}
                            for p in base.rglob("*") if p.is_file()})
    write(REPORT / stage / "manifest.json", {
        "run": RUN, "stage": stage, "time": stamp(), "inputs": READS, "outputs": outputs,
        "sealed_reads": 0, "paper_modified": False,
    })
