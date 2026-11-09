"""Fixed 2,000-family/process paired descriptive analysis; no policy fitting or selection."""
import common as C
import numpy as np,json,sys,collections,math
attempt=sys.argv[1];C.start(attempt+'/summary');C.SOUT=[]
protocol=C.load(C.ART/'setup_005/execution_protocol.json','PRE_OUTCOME_FIXED_DESIGN');ids=protocol['query_ids'];methods=C.PLANS+['Q_regret','QP_regret','RandomMix','RR_hard','RR_soft'];n=len(ids);assert n==58
mi={m:i for i,m in enumerate(methods)};qi={int(q):i for i,q in enumerate(ids)};U=np.full((n,9),np.nan);R=U.copy();RB=U.copy();actions={};reference=[];T=np.full((3,n,9,3),np.nan);CPU=T.copy();gpu=np.full((n,9),np.nan)
for proc in range(3):
 folder=C.REPORT/attempt/f'process_{proc:02d}' # Archived numeric cohort; hardware receipts separate, no new guard asserted.
 quality=C.load(folder/'quality.csv','NEW_FROZEN_ECONOMICS_METHOD_RESULTS');assert len(quality)==58*9
 if proc==0:
  reference=quality
  for r in quality:
   i,j=qi[int(r['query_id'])],mi[r['method']];U[i,j]=float(r['nDCG10']);R[i,j]=float(r['r']);RB[i,j]=float(r['r_bar']);actions[i,j]=r['action']
 else:
  for r in quality:
   i,j=qi[int(r['query_id'])],mi[r['method']];assert abs(U[i,j]-float(r['nDCG10']))<1e-10 and abs(R[i,j]-float(r['r']))<1e-10
 req=C.load(folder/'requests.csv','ACTUAL_UNPROFILED_COMPLETE_WARM_REQUESTS');assert len(req)==58*9*3
 for row in req:
  i,j,k=qi[int(row['query_id'])],mi[row['method']],int(row['repeat']);assert np.isnan(T[proc,i,j,k]);T[proc,i,j,k]=float(row['E2E_s'])*1000;CPU[proc,i,j,k]=float(row['CPU_process_s'])*1000
prof=C.load(C.REPORT/attempt/'process_00/GPU_profiles.csv','SEPARATE_INSTRUMENTED_GPU_COHORT')
for row in prof:
 if row['component']=='complete_route':gpu[qi[int(row['query_id'])],mi[row['method']]]=float(row['gpu_active_union_seconds'])
assert all(np.isfinite(x).all() for x in [U,R,RB,T,CPU,gpu])
groups=C.load(C.ROOT/protocol['query_family_map'],'FROZEN53_QUERY_FAMILIES_AND_SOURCE_MAP');g={int(x['query_id']):x['query_family'] for x in groups};docsets={int(x['query_id']):set(json.loads(x['source_docs'])) for x in groups};families=sorted(set(g.values()));assert len(families)==53
family_ix=[np.array([qi[q] for q in ids if g[q]==name],int) for name in families];B=2000;rng=np.random.default_rng(C.SEED);br=[];bu=[];bt=[]
for b in range(B):
 ix=np.concatenate([family_ix[i] for i in rng.integers(0,len(family_ix),len(family_ix))]);pr=rng.integers(0,3,3);br.append(R[ix].mean(0));bu.append(U[ix].mean(0));bt.append(T[pr][:,ix].mean((0,1,3)))
br,bu,bt=map(np.array,[br,bu,bt]);meanT=T.mean((0,1,3));meanR=R.mean(0);meanU=U.mean(0)
def ci(x):return [float(z) for z in np.quantile(x,[.025,.975])]
main=[]
for m,j in mi.items():
 rlo,rhi=ci(br[:,j]);ulo,uhi=ci(bu[:,j]);tlo,thi=ci(bt[:,j]);main.append({'dataset':'Economics English V2','method':m,'n_queries':58,'n_query_families':53,'source_PDFs':5,'source_components':1,'nDCG10':meanU[j],'mean_r':meanR[j],'r_bar':RB[:,j].mean(),'harm_rate':(R[:,j]>1e-10).mean(),'FalseSafe_rate':np.mean([actions[i,j]!='Full-Visual' and R[i,j]>.05 for i in range(n)]),'E2E_mean_ms':meanT[j],'E2E_P50_ms':float(np.quantile(T[:,:,j,:],.5)),'E2E_P95_ms':float(np.quantile(T[:,:,j,:],.95)),'CPU_process_mean_ms':float(CPU[:,:,j,:].mean()),'GPU_active_s':float(gpu[:,j].mean()),'mean_r_family95_low':rlo,'mean_r_family95_high':rhi,'nDCG_family95_low':ulo,'nDCG_family95_high':uhi,'E2E_family_process95_low_ms':tlo,'E2E_family_process95_high_ms':thi,'source_cluster95':'NA_INSUFFICIENT_ONE_CONNECTED_COMPONENT','evidence':'FROZEN_TRANSFER_DESCRIPTIVE_NOT_CERTIFIED','status':'PASS_ACTUAL_ECONOMICS_EXECUTION','cost_scope':'actual complete warm paths; separate instrumentedGPU, not Serving/businessnetbenefit','baseline_fidelity':'RR_ADAPTED_NOT_FAITHFUL_OFFICIAL' if m.startswith('RR_') else 'FIXED_LOCAL'})
C.table(C.R/'economics_main_table.csv',main);C.table(C.R/'economics_per_query.csv',reference);paired=[]
for a,b in [('QP_regret','Q_regret'),('QP_regret','BM25-R100'),('BM25-R100','Full-Visual')]:
 x,y=mi[a],mi[b];paired.append({'contrast':a+' minus '+b,'delta_r':meanR[x]-meanR[y],'r_family95_low':ci(br[:,x]-br[:,y])[0],'r_family95_high':ci(br[:,x]-br[:,y])[1],'delta_nDCG10':meanU[x]-meanU[y],'nDCG_family95_low':ci(bu[:,x]-bu[:,y])[0],'nDCG_family95_high':ci(bu[:,x]-bu[:,y])[1],'delta_E2E_ms':meanT[x]-meanT[y],'E2E_family_process95_low_ms':ci(bt[:,x]-bt[:,y])[0],'E2E_family_process95_high_ms':ci(bt[:,x]-bt[:,y])[1],'source_cluster95':'NA_ONE_COMPONENT','CI_scope':'pointwise95 conditionaldescriptive; source dependence not corrected; not simultaneous/PAC'})
C.table(C.R/'economics_paired_contrasts.csv',paired)
loo=[]
for doc in sorted(set().union(*docsets.values())):
 ix=[qi[q] for q in ids if doc not in docsets[q]]
 for m,j in mi.items():loo.append({'leftout_doc':doc,'method':m,'queries_remaining':len(ix),'mean_r':float(R[ix,j].mean()) if ix else None,'nDCG10':float(U[ix,j].mean()) if ix else None,'E2E_mean_ms':float(T[:,ix,j,:].mean()) if ix else None,'status':'DESCRIPTIVE_OVERLAPPING_LOO_NOT_INDEPENDENT' if ix else 'INSUFFICIENT_EMPTY_AFTER_SOURCE_EXCLUSION'})
C.table(C.R/'economics_source_leave_one_out.csv',loo)
def envelope(r,c,budget):
 opts=[float(c[j]) for j in range(4) if r[j]<=budget+1e-12]
 for i in range(4):
  for j in range(i+1,4):
   if abs(r[i]-r[j])<1e-15:continue
   w=(budget-r[j])/(r[i]-r[j])
   if -1e-12<=w<=1+1e-12:opts.append(float(w*c[i]+(1-w)*c[j]))
 return min(opts) if opts else float('nan')
env=[]
for m,j in mi.items():
 val=envelope(meanR[:4],meanT[:4],meanR[j]);dist=np.array([envelope(br[b,:4],bt[b,:4],br[b,j])-bt[b,j] for b in range(B)]);lo,hi=ci(dist);env.append({'method':m,'observed_r':meanR[j],'actual_cost_ms':meanT[j],'posthoc_best_static_mix_ms':val,'posthoc_gain_ms':val-meanT[j],'gain_family_process95_low_ms':lo,'gain_family_process95_high_ms':hi,'scope':'POSTHOC_ENVELOPE_FITTED_TO_TEST_RESULTS_NOT_DEPLOYED_RANDOMMIX','FrozenRandomMix_is_separate':True})
C.table(C.R/'economics_posthoc_static_envelope.csv',env)
failure=[r for r in reference if float(r['r'])>.05];C.table(C.R/'all_high_harm_and_false_safe_cases.csv',failure,list(reference[0]))
C.table(C.R/'allocation_counts.csv',[{'method':m,'action':a,'queries':sum(actions[i,j]==a for i in range(n))} for m,j in mi.items() for a in C.PLANS])
try:
 import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
 fig,ax=plt.subplots(figsize=(8,5))
 for m,j in mi.items():ax.scatter(meanT[j],meanR[j]);ax.annotate(m,(meanT[j],meanR[j]),fontsize=7)
 ax.set(xlabel='Actual warm complete path (ms)',ylabel='Mean FullV-relative positive regret',title='Economics frozen transfer — descriptive, not certified');fig.tight_layout();fig.savefig(C.R/'economics_risk_cost.png',dpi=180);fig.savefig(C.R/'economics_risk_cost.pdf');plt.close(fig)
except Exception as e:C.write(C.R/'figure_failure.json',{'status':'FAIL_PLOT_ONLY_NO_METRIC_CHANGE','error':str(e)})
C.prose(C.R/'economics_report.md','# PASS actual Economics main experiment, not a positive-result gate\n\n58queries/53families/5PDFs→1connectedsourcecomponent;907grade2qrels; threeprocesses×three repeats give4698timedrequests, not4698independentqueries. All9methods/allqueriesretained, no refit/threshold/model/actionchanges. Officialsourceqrels and frozenpolicycodebound by hashes. Paired CI arepointwise family/processconditionaldescriptive only; source95CI NA because1component. FivePDFLOO overlap anddo notcreate5independentreplications. NewK1 NOT_CERTIFIED, strictServingnotestablished.\n\n'+json.dumps({'main_table':main,'primary_paired':paired},ensure_ascii=False,indent=2)+'\n\nFrozenRandomMix is actualfixed allocation; outcome-fittedstaticenvelope isPOSTHOC, not deployed independentbaseline. Negative findings/highharms/failures retained. GPUactive andCPU/wall separate, allstartup/index/OCR costs separate. No Paper/native/GitHub/CMT update is automatic.\n')
C.write(C.R/'final_numbers.json',{'status':'PASS_ACTUAL_ECONOMICS_MAIN','queries':58,'timed_requests':4698,'methods':9,'primary_paired':paired,'main_table':main,'source_components':1,'new_K1':'NOT_CERTIFIED'})
C.finish(attempt+'_summary','PASS_ACTUAL_FROZEN_ECONOMICS_MAIN_DESCRIPTIVE','58queries/53families/1sourcecomponent;9methods;4698warmtimings;754profilecalls;2000pairedfamily/processbootstrap;allnegativecasesretained','写入待Orange回报队列；不得声称新K1、可靠sourceCI或Serving/业务净收益，不改模型或论文。')
