"""G2-only cost cohort; immutable inputs, exclusive outputs, no qrels."""
from pathlib import Path
import csv, datetime, hashlib, json, os, shutil, sys, traceback

ROOT = Path('${PROJECT_ROOT}')
RUN = 'icde_eab_g2_setup_017'
ART = ROOT / 'artifacts' / RUN
REPORT = ROOT / 'reports' / RUN
INDEX = ROOT / 'cache/indexes' / RUN
SEED = 202610282110  # unchanged model/timing seed from 009
PLANS = ['Full-Visual', 'BM25-R50', 'BM25-R100', 'BM25']
A = R = None

def stamp():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def write(path, data):
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('x', encoding='utf8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')

def prose(path, text):
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('x', encoding='utf8') as f: f.write(text)

def table(path, rows):
    rows = list(rows)
    keys = list(dict.fromkeys(k for row in rows for k in row))
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('x', encoding='utf8', newline='') as f:
        w = csv.DictWriter(f, keys); w.writeheader()
        w.writerows(rows)

def event(name, **data):
    if A is None: return
    with (A / 'events.jsonl').open('a', encoding='utf8') as f:
        f.write(json.dumps(dict(time_bj=stamp(), event=name, **data), ensure_ascii=False) + '\n')

def denied(path):
    s = str(path).replace('\\', '/').lower()
    return any(x in s for x in ['qrels', '/sealed/', '/prereg_v2_round_005/',
        'b-l_pool', 'b_l_outcomes', 'final_test_queries', 'cal_outcomes',
        'eval_outcomes', 'cal_queries', 'eval_queries', 'computer_science', '/vidore_v3_cs/'])

def protected(event_name, args):
    if event_name != 'open' or not args or not isinstance(args[0], str): return
    mode = args[1] if len(args) > 1 else ''
    if isinstance(mode, str) and any(x in mode for x in ['w', 'a', 'x']): return
    if denied(args[0]): raise PermissionError('FORBIDDEN_LABEL_OR_SEALED_INPUT_REFUSED')

def load(path, role='FROZEN_UNLABELED_OR_METADATA'):
    p = Path(path); p = p if p.is_absolute() else ROOT / p
    if denied(p): raise PermissionError('FORBIDDEN_INPUT_REFUSED')
    data = p.read_bytes()
    event('input_read', path=str(p), sha256=hashlib.sha256(data).hexdigest(), role=role)
    if p.suffix == '.csv': return list(csv.DictReader(data.decode('utf-8-sig').splitlines()))
    if p.suffix == '.json': return json.loads(data)
    return data.decode('utf8')

def start(stage):
    global A, R
    A = ART / stage; R = REPORT / stage
    A.mkdir(parents=True, exist_ok=False); R.mkdir(parents=True, exist_ok=False)
    sys.addaudithook(protected)
    write(A / 'start.json', dict(time_bj=stamp(), stage=stage, pid=os.getpid(), sealed_reads=0))
    def fail(t, v, tb):
        if not (A / 'failure.json').exists():
            write(A / 'failure.json', dict(time_bj=stamp(), exception=str(v), traceback=''.join(traceback.format_exception(t, v, tb))))
        traceback.print_exception(t, v, tb)
    sys.excepthook = fail

def cache_state():
    mem = Path('/proc/meminfo').read_text()
    return dict(time_bj=stamp(), loadavg=os.getloadavg(), cpu_threads=os.cpu_count(),
        memory={line.split(':')[0]: line.split(':', 1)[1].strip() for line in mem.splitlines()
                if line.split(':')[0] in ['MemAvailable', 'Cached', 'Buffers', 'Dirty', 'Writeback']},
        OS_cache_flushed=False, scope='process-cold; OS page cache not isolated; asset verification reads warm cache')

def output_bytes(paths):
    return sum(p.stat().st_size for base in paths if base.exists() for p in base.rglob('*')
               if p.is_file() and not p.is_symlink())

def auxiliary_bytes():
    return output_bytes([ART, REPORT, INDEX / 'smoke', INDEX / 'profile'])

def disk_check():
    free = shutil.disk_usage(ROOT).free
    if free < 5 * 2**30: raise RuntimeError('DISK_GUARD_BELOW_5GiB_STOP_OWN_JOB')
    return free

def verify_sources(protocol):
    for rel, expected in protocol['code_SHA256'].items():
        if sha(ROOT / rel) != expected: raise RuntimeError('FROZEN_CODE_HASH_MISMATCH ' + rel)
