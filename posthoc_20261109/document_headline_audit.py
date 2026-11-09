"""Annotate exported results without changing scientific numbers."""
from pathlib import Path
import csv,json,re
R=Path(__file__).resolve().parent
rows=list(csv.DictReader((R/'screening_001/E2_main_b005.csv').open(encoding='utf8')))
neg=sum(int(z['negative_query_process_costs'])>0 for z in rows)
over=sum(float(z['OOF_r'])>.05 for z in rows)
p=R/'E2_HEADLINE.md';text=p.read_text(encoding='utf8')
text+='\nStatus: PARTIAL — the computation completed, but '+str(neg)+' main cells contain negative query/process accounting estimates from transferring signed archived execution-context differences. These are retained without clipping and are not physical times. '+str(over)+' OOF mean risks exceed the nominal training budget .05; this diagnostic does not certify a risk contract.\n'
p.write_text(text,encoding='utf8',newline='\n')
h=R/'screening_001/input_hashes.json';d=json.loads(h.read_text(encoding='utf8'))
h.write_text(json.dumps({re.sub(r'/home/[^/]+/work1/mdrouter_v5_20261009','${PROJECT_ROOT}',k):v for k,v in d.items()},indent=2)+'\n',encoding='utf8')
(R/'ENGINEERING_LOG.md').write_text('''# Engineering log

The first local headline-annotation command used the Windows default GBK text
decoder and failed before changing the report or exported hash inventory. The
scientific computation was unaffected. This explicit UTF-8 follow-up records
the limitations. A verbose Git whitespace check also treated standard CSV CRLF
as trailing whitespace; future checks recognize CR-at-EOL instead of rewriting
scientific CSV bytes. No prior commit was amended or forced.
''',encoding='utf8')
print(json.dumps(dict(negative_accounting_cells=neg,OOF_risk_over_005_cells=over,scientific_values_changed=0)))
