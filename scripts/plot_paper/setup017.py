"""Validate same-process setup/warm accounting and expose plotting inputs."""
import csv
import hashlib
import math
import statistics
from pathlib import Path
import json

BASE = Path(__file__).resolve().parent
G2 = BASE / "data" / "017"
MODELS = ("ColQwen2", "ColPali")
SCENARIOS = {
    "OCR_EXCLUSIVE_NEW_INDEX": (1, 1, False),
    "OCR_SHARED_HALF_NEW_INDEX": (.5, 1, False),
    "OCR_PREPAID_NEW_INDEX": (0, 1, False),
    "EXISTING_INDEX_OCR_NEW": (1, 0, False),
    "EXISTING_INDEX_OCR_PREPAID": (0, 0, False),
    "ALREADY_RESIDENT_ALL_PREPAID": (0, 0, True),
}
VOLUMES = (100, 1000, 10000, 100000)
OCR = 407.725


def read(name):
    path = G2 / name
    checks = json.loads((BASE.parent / "INPUT_SHA256.json").read_text(encoding="utf8"))
    rel = "verification_001/receipt.json" if name == "receipt.json" else name
    expected = checks[f"reports/icde_eab_g2_setup_017/{rel}"]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, path
    with path.open(encoding="utf8", newline="") as stream:
        return list(csv.DictReader(stream))


def keyed(rows, *columns):
    result = {tuple(row[column] for column in columns): row for row in rows}
    assert len(result) == len(rows), columns
    return result


SETUP = keyed(read("G2_setup_repeats.csv"), "model", "repeat")
WARM = keyed(read("G2_same_cohort_warm.csv"), "model", "repeat", "plan")
COST = keyed(read("G2_reuse_sensitivity.csv"), "model", "repeat", "scenario", "N")
CROSS = keyed(read("G2_break_even_ranges.csv"), "model", "repeat", "scenario")
GPU = keyed(read("G2_GPU_profiles.csv"), "model")


def run_values(model, repeat, scenario):
    setup = SETUP[model, str(repeat)]
    fraction, index_charge, resident = SCENARIOS[scenario]
    full, rerank = [float(WARM[model, str(repeat), plan]["warm_E2E_s"])
                    for plan in ("Full-Visual", "BM25-R100")]
    fixed_full = 0 if resident else (float(setup["base_process_startup_wall_s"]) +
                                     index_charge * float(setup["index_wall_s"]))
    extra = 0 if resident else float(setup["BM25_build_wall_s"]) + fraction * OCR
    return fixed_full, extra, full, rerank


def ratio(model, repeat, scenario, n):
    base, extra, full, rerank = run_values(model, repeat, scenario)
    return (base + extra + n * rerank) / (base + n * full)


def crossing(model, scenario):
    values = [int(CROSS[model, str(r), scenario]["conditional_break_even_N"])
              for r in (1, 2, 3)]
    return min(values), max(values)


def observed(values):
    return statistics.mean(values), min(values), max(values)


def validate():
    assert len(SETUP) == 6 and len(WARM) == 24 and len(COST) == 144 and len(CROSS) == 36
    for (model, repeat), setup in SETUP.items():
        assert setup["status"] == "PASS" and float(setup["max_embedding_error"]) == 0
        for plan, field in [("Full-Visual", "warm_FullV_s"), ("BM25-R100", "warm_R100_s")]:
            assert float(setup[field]) == float(WARM[model, repeat, plan]["warm_E2E_s"])
        for scenario in SCENARIOS:
            base, extra, full, rerank = run_values(model, repeat, scenario)
            assert math.ceil(extra / (full - rerank)) == int(CROSS[model, repeat, scenario]["conditional_break_even_N"])
            for n in VOLUMES:
                row = COST[model, repeat, scenario, str(n)]
                checks = {
                    "FullV_setup_s": base, "R100_setup_s": base + extra,
                    "FullV_total_wall_s": base + n * full,
                    "R100_total_wall_s": base + extra + n * rerank,
                    "R100_over_FullV_ratio": ratio(model, repeat, scenario, n),
                }
                assert all(math.isclose(float(row[k]), v, rel_tol=1e-12, abs_tol=1e-12)
                           for k, v in checks.items()), (model, repeat, scenario, n)


def csv_write(path, rows):
    rows = list(rows)
    with path.open("x", encoding="utf8", newline="") as stream:
        writer = csv.DictWriter(stream, list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


validate()
