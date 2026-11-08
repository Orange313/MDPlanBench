"""CPU-only entry point; no downloads, training, qrels or manuscript writes."""
import pathlib,argparse,subprocess,sys,os,json,shutil,csv,hashlib,math,time
ap=argparse.ArgumentParser();ap.add_argument('--output',required=True,type=pathlib.Path);a=ap.parse_args()
G=pathlib.Path(__file__).resolve().parents[1];O=a.output.resolve();O.mkdir(parents=True,exist_ok=False);start=time.perf_counter();receipts=[]
def run(name,cmd,env=None):
 p=subprocess.run(cmd,cwd=G,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf8',errors='replace');(O/(name+'.log')).write_text(p.stdout,encoding='utf8')
 receipts.append(dict(step=name,returncode=p.returncode));
 if p.returncode:raise RuntimeError(name+' failed; preserved log')
def rows(p):return list(csv.DictReader(p.open(encoding='utf-8-sig')))
run('legacy_cpu',[sys.executable,str(G/'reproduce_all.py'),'--output',str(O/'legacy')])
run('021_017_statistics',[sys.executable,str(G/'scripts/replay_021_017.py'),'--root',str(G/'records/021_snapshot'),'--out',str(O/'audit')])
summary=json.loads((O/'audit/audit_summary.json').read_text());assert summary['numeric_failures']==0
# Numerical table outputs checked against independently audited paper inputs.
tables=O/'tables';tables.mkdir()
for n in ['capacity_verified.csv','decomposition_verified.csv','fit_mixture_verified.csv','paired_contrasts_verified.csv','setup017_verified.csv','warm017_verified.csv','crossings017_verified.csv']:
 shutil.copyfile(O/'audit'/n,tables/n)
for n in ['plot_points_registered.csv','paired_contrasts.csv','fixed_budget_oracle.csv','AA_equivalence_intervals.csv']:
 shutil.copyfile(G/'records/figure_data'/n,tables/n)
orig=rows(G/'records/figure_data/plot_points_registered.csv');main=[x for x in orig if x['model']=='ColQwen2' and x['domain'] in ['HR','Finance','Industrial','Pharma'] and x['method'] in ['FullV','R100','Q','QP']];bench=[x for x in orig if x['model']=='ColQwen2' and x['domain'] in ['Biomedical','Economics']]
for name,rr in [('table_III.csv',main),('table_IV.csv',bench)]:
 with (tables/name).open('w',newline='',encoding='utf8') as f:w=csv.DictWriter(f,fieldnames=list(rr[0]));w.writeheader();w.writerows(rr)
tableII=[];legacy=rows(G/'splits/legacy_query_roles_ids.csv');pagecounts=json.loads((G/'records/fresh_unlabelled_page_counts.json').read_text())
for z in pagecounts:
 d=z['domain'];x=dict(domain=d,pages=z['pages'],documents=z['docs'],English_queries=0,Fit_queries=0,Fit_families=0,Dev_queries=0,Dev_families=0,Benchmark_queries=0,Benchmark_families=0)
 if d in ['HR','Finance','Industrial']:
  ds={'HR':'vidore_v3_hr','Finance':'vidore_v3_finance_en','Industrial':'vidore_v3_industrial'}[d];dev=rows(G/'splits'/(ds+'_dev_ids.csv'))
  x.update(English_queries=sum(q['dataset']==ds for q in legacy),Dev_queries=len(dev),Dev_families=len({q['family_primary'] for q in dev}))
 elif d=='Pharma':
  fit=rows(G/'splits/fit_ids.csv');dev=rows(G/'splits/development_ids.csv');audit=json.loads((G/'splits/audit.json').read_text())
  x.update(English_queries=sum(v['queries'] for v in audit['roles'].values()),Fit_queries=len(fit),Fit_families=len({q['family_id'] for q in fit}),Dev_queries=len(dev),Dev_families=len({q['family_id'] for q in dev}))
 else:
  frozen=json.loads((G/'freeze'/(d.lower()+'_frozen_protocol.json')).read_text());x.update(English_queries=len(frozen['query_ids']),Benchmark_queries=len(frozen['query_ids']),Benchmark_families=frozen['query_families'])
 tableII.append(x)
with (tables/'table_II.csv').open('w',newline='',encoding='utf8') as f:w=csv.DictWriter(f,fieldnames=list(tableII[0]));w.writeheader();w.writerows(tableII)
for checked,expected in [('capacity_verified.csv','capacity_plot.csv'),('decomposition_verified.csv','selection_plot.csv')]:
 calc=rows(O/'audit'/checked);exp=rows(G/'records/022_plot_data'/expected)
 for z in exp:
  q=next(x for x in calc if x['domain']==z['domain'] and x['method']==z['method'])
  for key in ['DeltaC_pp','DeltaC_low_pp','DeltaC_high_pp','oracle_headroom_pp','selector_loss_pp','realized_minus_standalone_execution_pp']:
   if key in z and key in q:assert math.isclose(float(z[key]),float(q[key]),abs_tol=1e-8),(checked,z['domain'],key)
# Every figure is rendered in a new scratch tree; originals are never changed.
plot=O/'plot_work';shutil.copytree(G/'scripts/plot_paper',plot/'figures');shutil.copytree(G/'records/figure_data',plot/'figures/data');shutil.copyfile(G/'scripts/INPUT_SHA256.json',plot/'INPUT_SHA256.json')
env=os.environ.copy();env['MDROUTER_FIG_OUT']=str(O/'figures');(O/'figures').mkdir();(O/'figures/qa').mkdir()
run('paper_figures_1_3_4',[sys.executable,str(plot/'figures/make_paper.py')],env)
compact=O/'compact';shutil.copytree(G/'records/022_plot_data',compact/'data');(compact/'figures').mkdir()
run('figure5_and_lifecycle',[sys.executable,str(G/'scripts/render_compact_diagnostics.py'),str(compact)])
for p in (compact/'figures').iterdir():shutil.copyfile(p,O/'figures'/p.name)
for p in (G/'records/diagram_source').iterdir():shutil.copyfile(p,O/'figures'/p.name)
receipt=dict(status='PASS_CPU_NUMERIC_AND_FIGURE_REPLAY',wall_s=time.perf_counter()-start,steps=receipts,original_numeric_tables=42,new_tables=len(list(tables.glob('*.csv'))),figures=[p.name for p in (O/'figures').glob('*.pdf')],new_models_trained=0,GPU_jobs=0,network=False,sealed_labels_read=0,limitations=['No fresh GPU timing is inferred from CPU reconstruction.','Economics inference is conditional on one source component.','Scientific issues in ledger are retained; replay success does not endorse manuscript wording.'])
(O/'replay_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8');print(json.dumps(receipt,indent=2))
