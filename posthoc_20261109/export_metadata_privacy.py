"""Remove private root prefixes from exported review metadata, never raw records."""
from pathlib import Path
import re

root=Path(__file__).resolve().parent
count=0
for folder in ['E8_storage_001','portable_inputs_001','gates_001','fit_trace_002','independent_001','E5_analysis_001','E7_HR_001','E7_reference_gate_001']:
    for p in (root/folder).rglob('*'):
        if not p.is_file() or p.suffix not in ['.json','.csv','.jsonl']:continue
        text=p.read_text(encoding='utf8')
        new=re.sub(r'/home/[^/\s"\',]+/work1/mdrouter_v5_20261009','${PROJECT_ROOT}',text)
        new=re.sub(r'/backup01/[^/\s"\',]+/mdrouter_v5_20261009','${ASSET_ROOT}',new)
        if new!=text:
            with p.open('w',encoding='utf8',newline='') as f:f.write(new)
            count+=1
print(f'Sanitized metadata files: {count}; original experiment inputs untouched.')
