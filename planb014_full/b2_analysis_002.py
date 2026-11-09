"""Post-hoc mechanism analysis; no models loaded, no new retrieval or fitting."""
import common as C
import numpy as np,json,collections,math,sys
from scipy.optimize import linprog
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
C.start(sys.argv[1] if len(sys.argv)>1 else 'B2_analysis_002')
packs=C.load('reports/icde_eab_planb_014/B2_prepare_002/allowed_query_diagnostics.json')
METHODS=['Full-Visual','BM25-R50','BM25-R100','BM25','Q_regret','QP_regret','RandomMix','RR_hard','RR_soft'];STATIC=METHODS[:4]
main=[];candidate=[];matrices=[];repairs=[];actions=[];overhead=[];paired=[];iv=[];cases=[];dep=[];riskcurves=[];true_sources=[];method_summary=[]
def ci(x):return np.quantile(x,[.025,.975]).tolist()
def envelope(r,c,b):
 out=[float(c[i]) for i in range(len(r)) if r[i]<=b+1e-12]
 for i in range(len(r)):
  for j in range(i):
   if abs(r[i]-r[j])<1e-14:continue
   w=(b-r[j])/(r[i]-r[j])
   if 0<=w<=1:out.append(float(w*c[i]+(1-w)*c[j]))
 return min(out)
def oracle(r,c,b):
 n,k=r.shape
 # Fractional, per-query label-dependent actions: an information bound, not a policy.
 from scipy.sparse import kron,eye,csr_matrix
 eq=kron(eye(n),np.ones((1,k)),format='csr')
 ans=linprog(c.ravel()/n,A_ub=csr_matrix(r.reshape(1,-1)/n),b_ub=[b],A_eq=eq,b_eq=np.ones(n),bounds=(0,1),method='highs')
 assert ans.success,ans.message
 return float(ans.fun)
bioP=C.load('reports/icde_eab_lastmile_008/L0/paired_all_comparisons.csv')
ecoP=C.load('reports/icde_eab_external_validation_013/monitor_001/auto2_attempt_001/summary/economics_paired_contrasts.csv')
for d in packs:
 name=d['domain'];diag={int(q['query_id']):q for q in d['queries']};ids=sorted(diag);N=len(ids)
 quality=C.load(d['quality_path']);qm={(int(x['query_id']),x['method']):x for x in quality};R=np.array([[float(qm[q,m]['r']) for m in METHODS] for q in ids]);U=np.array([[float(qm[q,m]['nDCG10']) for m in METHODS] for q in ids]);cost=np.full((3,N,9,3),np.nan);raw=[];groups=[diag[q]['source_group'] for q in ids]
 base=C.ROOT/('reports/icde_eab_independent_007/T2' if name=='Biomedical' else 'reports/icde_eab_external_validation_013/monitor_001/auto2_attempt_001')
 for proc in range(3):
  folder=base/(f'process_{proc}_001' if name=='Biomedical' else f'process_{proc:02d}');rr=C.load(folder/'requests.csv');raw+=rr
  for row in rr:cost[proc,ids.index(int(row['query_id'])),METHODS.index(row['method']),int(row['repeat'])]=float(row['E2E_s'])*1000
 assert np.isfinite(cost).all()
 cm=cost.mean((0,3));mr=R.mean(0);mu=U.mean(0);mc=cm.mean(0)
 source=C.load('reports/icde_eab_independent_007/T2/summary_001/biomedical_main_table.csv' if name=='Biomedical' else 'reports/icde_eab_external_validation_013/monitor_001/auto2_attempt_001/summary/economics_main_table.csv')
 for row in source:
  m=row['method'];j=METHODS.index(m);assert abs(float(row['mean_r'])-mr[j])<1e-12 and abs(float(row['E2E_mean_ms'])-mc[j])<1e-8
  main.append({'domain':name,'method':m,'queries':N,'families':157 if name=='Biomedical' else 53,'source_PDFs':27 if name=='Biomedical' else 5,'source_components':27 if name=='Biomedical' else 1,'nDCG10':mu[j],'mean_r':mr[j],'harm_rate':float((R[:,j]>1e-10).mean()),'E2E_mean_ms':mc[j],'P50_ms':float(np.quantile(cost[:,:,j,:],.5)),'P95_ms':float(np.quantile(cost[:,:,j,:],.95)),'CPU_ms':row.get('CPU_process_ms',row.get('CPU_process_mean_ms')),'GPU_active_s':row.get('GPU_active_s'),'evidence':'FROZEN_EXTERNAL_DESCRIPTIVE','cost_scope':'ACTUAL_COMPLETE_WARM_PATH__GPU_SEPARATE_PROFILE','status':'PASS','CI_scope':'SOURCE27_PAIRED_DESCRIPTIVE' if name=='Biomedical' else 'FAMILY53_PROCESS_CONDITIONAL_ONLY_SOURCE_CI_NA'})
 for control in ['Q_regret','BM25-R100']:
  j=METHODS.index(control);qp=METHODS.index('QP_regret')
  if name=='Biomedical':
   rows=[x for x in bioP if x['control']==control and x['grouping']=='source_group'];lookup={x['metric']:x for x in rows};a=lookup['positive_regret_delta'];b=lookup['complete_E2E_ms_delta'];dr=[float(a[k]) for k in ['estimate','low95','high95']];dt=[float(b[k]) for k in ['estimate','low95','high95']]
  else:
   a=next(x for x in ecoP if x['contrast']=='QP_regret minus '+control);dr=[float(a[k]) for k in ['delta_r','r_family95_low','r_family95_high']];dt=[float(a[k]) for k in ['delta_E2E_ms','E2E_family_process95_low_ms','E2E_family_process95_high_ms']]
  assert abs(dr[0]-(mr[qp]-mr[j]))<1e-10 and abs(dt[0]-(mc[qp]-mc[j]))<1e-8
  paired.append({'domain':name,'contrast':'QP minus '+control,'delta_r':dr[0],'r95_low':dr[1],'r95_high':dr[2],'delta_E2E_ms':dt[0],'E2E95_low_ms':dt[1],'E2E95_high_ms':dt[2],'source_components':27 if name=='Biomedical' else 1,'CI_scope':'source27/process conditional descriptive' if name=='Biomedical' else 'family53/process conditional descriptive;sourceCI_NA','r_and_cost_intervals_both_favorable':dr[2]<0 and dt[2]<0,'extra_ms_per_0p01_risk_reduction':dt[0]/(-dr[0])*.01 if dr[0]<0 else None,'status':'POSTHOC_DESCRIPTIVE'})
 for q in ids:
  i=ids.index(q);dd=diag[q];labels={int(p):v for p,v in dd['qrels'].items()};ref=dd['reference_top10'];rs={m:float(qm[q,m]['r']) for m in METHODS};p50=set(dd['BM25_candidates100'][:50]);p100=set(dd['BM25_candidates100']);Q=qm[q,'Q_regret'];QP=qm[q,'QP_regret'];rp={}
  for k,cand in [(50,p50),(100,p100)]:
   m='BM25-R'+str(k);x=qm[q,m];r=rs[m];contained=set(ref)<=cand;rank=json.loads(x['ranking']);assert not contained or (rank==ref and r<1e-10),(name,q,k)
   # Recheck official linear-gain metric using existing rankings, not a new retrieval.
   ideal=sum(v/math.log2(t+2) for t,v in enumerate(sorted(labels.values(),reverse=True)[:10]));nd=sum(labels.get(p,0)/math.log2(t+2) for t,p in enumerate(rank[:10]))/ideal if ideal else 0.;assert abs(nd-float(x['nDCG10']))<1e-10
   row={'domain':name,'query_id':q,'family':dd['family'],'source_group':dd['source_group'],'plan':m,'candidate_K':k,'ref_top10_contained':contained,'mean_r':r,'harm':r>1e-10,'severe_r_gt_0p05':r>.05,'nDCG10':nd,'recall_judged_pages':len(cand&set(labels))/len(labels),'reference_judged_positive_misses':sum(p in labels and p not in cand for p in ref),'known_relevant_pages':len(labels),'empty_OCR_relevant_pages':len(dd['empty_OCR_relevant']),'QP_action':QP['action'],'QP_r':rs['QP_regret'],'Q_action':Q['action'],'Q_r':rs['Q_regret'],'R50_to_R100_full_repair':rs['BM25-R50']>1e-10 and rs['BM25-R100']<=1e-10,'R50_to_R100_improved':rs['BM25-R100']<rs['BM25-R50']-1e-10,'R50_to_R100_worsened':rs['BM25-R100']>rs['BM25-R50']+1e-10,'QP_correct_reference_fallback':QP['action']=='Full-Visual' and rs['BM25-R100']>1e-10,'QP_false_safe_fast_r_gt_0p05':QP['action']!='Full-Visual' and rs['QP_regret']>.05,'status':'POSTHOC_DIAGNOSTIC_NOT_ONLINE_FEATURE'};candidate.append(row);rp[m]=row
  repairs.append({'domain':name,'query_id':q,'R50_r':rs['BM25-R50'],'R100_r':rs['BM25-R100'],'fully_repaired':rp['BM25-R100']['R50_to_R100_full_repair'],'improved':rp['BM25-R100']['R50_to_R100_improved'],'worsened':rp['BM25-R100']['R50_to_R100_worsened'],'QP_action':QP['action'],'QP_r':rs['QP_regret'],'correct_reference_fallback':rp['BM25-R100']['QP_correct_reference_fallback'],'false_safe':rp['BM25-R100']['QP_false_safe_fast_r_gt_0p05']})
  actions.append({'domain':name,'query_id':q,'family':dd['family'],'source_group':dd['source_group'],'Q_action':Q['action'],'QP_action':QP['action'],'Q_r':rs['Q_regret'],'QP_r':rs['QP_regret'],'QP_minus_Q_r':rs['QP_regret']-rs['Q_regret'],'QP_minus_Q_actual_ms':cm[i,5]-cm[i,4],'empty_OCR_relevant':bool(dd['empty_OCR_relevant'])})
  for p in labels:dep.append({'domain':name,'query_id':q,'family':dd['family'],'corpus_page_id':p,'doc_id':dd['page_doc_map'].get(str(p)),'source_component':dd['source_group'] if name=='Biomedical' else 'Economics_connected_component_0','relevance_grade':labels[p],'scope':'ORIGINAL_ALREADY_OBSERVED_EXTERNAL_QRELS_MAP__NOT_FOR_PUBLIC_UPLOAD'})
 for m in ['Q_regret','QP_regret','RandomMix']:
  for action in STATIC:
   rr=[r for r in raw if r['method']==m and r['action']==action]
   if not rr:continue
   get=lambda k:np.mean([float(r[k])*1000 for r in rr]);fields=['Q_wall_s','Probe_extra_wall_s','Probe_statistics_wall_s','planner_wall_s','selected_path_wall_s'];parts={k[:-2]+'_ms':get(k) for k in fields}
   overhead.append({'domain':name,'method':m,'action':action,'unique_queries':len(set(r['query_id'] for r in rr)),'timings':len(rr),'actual_complete_E2E_ms':get('E2E_s'),**parts,'measured_scope_residual_ms':get('E2E_s')-sum(parts.values()),'probe_reused_fraction':sum(r['Probe_reused']=='True' for r in rr)/len(rr),'probe_paid_before_FullV_fraction':sum(r['Probe_paid_before_FullV']=='True' for r in rr)/len(rr),'accounting':'WALL_COMPONENTS_FROM_SAME_REQUEST; CPU_GPU_NOT_ADDED; residual includes orchestration','status':'MEASURED_COMPONENT_SCOPE'})
 for k in [50,100]:
  rr=[x for x in candidate if x['domain']==name and x['candidate_K']==k]
  for contained in [True,False]:
   for harm in [False,True]:
    zz=[x for x in rr if x['ref_top10_contained']==contained and x['harm']==harm];matrices.append({'domain':name,'plan':'BM25-R'+str(k),'contained':contained,'harm':harm,'queries':len(zz),'all_queries':N,'severe_r_gt_0p05':sum(x['severe_r_gt_0p05'] for x in zz),'regret_mass':sum(x['mean_r'] for x in zz),'status':'POSTHOC_DESCRIPTIVE'})
    if zz:
     picked=sorted(zz,key=lambda x:(-x['mean_r'],x['query_id']))[0];case={**picked,'selection_rule':'max regret then ascendingqueryID within every nonempty containment×harm×domain×K stratum','query':diag[picked['query_id']]['query'],'FullV_top10':diag[picked['query_id']]['reference_top10'],'reranked_top10':json.loads(qm[picked['query_id'],'BM25-R'+str(k)]['ranking'])};cases.append(case)
 # Fixed retrospective opportunity slices: every frozen policy's observed risk.
 for catalog,js in [('LEARNED_3_ACTION',[0,2,3]),('STATIC_4_ACTION',[0,1,2,3])]:
  for m in ['Q_regret','QP_regret','RandomMix']:
   j=METHODS.index(m);b=mr[j];ev=envelope(mr[js],mc[js],b);ov=oracle(R[:,js],cm[:,js],b)
   iv.append({'domain':name,'policy':m,'catalog':catalog,'risk_budget_observed':b,'actual_policy_complete_ms':mc[j],'posthoc_static_envelope_ms':ev,'same_catalog_fractional_oracle_ms':ov,'catalog_opportunity_ms':ev-ov,'realization_gap_ms':mc[j]-ov,'actual_increment_vs_static_ms':ev-mc[j],'fixed_random_actual_r':mr[6],'fixed_random_actual_ms':mc[6],'control_caveat':'actual FrozenMix NOT riskmatched; envelope/oracle fitted to outcomes and counterfactual static timings','oracle_scope':'POSTHOC_UPPER_BOUND with labels; static standalone timings exclude router overhead, optimistic bound','status':'POSTHOC_DESCRIPTIVE'})
 for j,m in enumerate(METHODS):riskcurves.append({'domain':name,'method':m,'risk':mr[j],'actual_ms':mc[j],'status':'MEASURED'})
# Four domains are exposed Dev, not independent confirmation. RR costs are assembled.
dev=C.load('reports/icde_eab_main_006/X2/rebuild_002/eab_main_table_dev.csv')
for row in dev:
 main.append({'domain':row['dataset'],'method':row.get('action_policy'),'queries':row.get('N_queries'),'nDCG10':row.get('nDCG@10'),'mean_r':row.get('r_pos_mean'),'harm_rate':row.get('harm_rate'),'families':row.get('N_families'),'E2E_mean_ms':row.get('wall_E2E_mean_ms'),'P95_ms':row.get('wall_P95_ms'),'GPU_active_s':row.get('GPU_active_s'),'CPU_ms':row.get('CPU_ms'),'cost_scope':row.get('cost_scope'),'evidence':'EXPOSED_DEV_EXPLORATORY','status':row.get('status'),'CI_scope':'DEVELOPMENT_SENSITIVITY_NOT_INDEPENDENT'})
devraw=C.load('reports/icde_eab_main_006/X2/rebuild_002/all_per_query.csv')
C.table(C.R/'b2_dev_per_query.csv',devraw)
assert len(set((x['dataset'],x['query_id']) for x in devraw))==164
assert all(row['method'] and row['queries'] and row['mean_r'] is not None and row['E2E_mean_ms'] is not None for row in main)
ocr=[]
for name in ['Biomedical','Economics']:
 for plan in ['BM25-R50','BM25-R100']:
  for empty in [False,True]:
   xx=[x for x in candidate if x['domain']==name and x['plan']==plan and bool(x['empty_OCR_relevant_pages'])==empty]
   ocr.append({'domain':name,'plan':plan,'any_empty_OCR_relevant_page':empty,'queries':len(xx),'harm':sum(x['harm'] for x in xx),'severe':sum(x['severe_r_gt_0p05'] for x in xx),'mean_r':np.mean([x['mean_r'] for x in xx]) if xx else None,'scope':'ALL_QUERIES_RETAINED__ASSOCIATION_NOT_CAUSAL'})
C.table(C.R/'b2_ocr_sensitivity.csv',ocr)
life=C.load('reports/icde_eab_release_validation_010/A0/replay_002/lifecycle_cost_replay.csv');reuse=C.load('reports/icde_eab_release_validation_010/A0/replay_002/reuse_sensitivity.csv');cohort=C.load('reports/icde_eab_release_validation_010/A0/replay_002/cohort_comparison.csv')
for r in life:r.update({'domain':'Biomedical','evidence':'CONDITIONAL_COMPONENT_MODEL_009_WARM_COHORT','quality_cost_cohort_warning':'Do not combine 007 warm70.22 with009 warm39.13; no crosscohort controlled speedup','setup_uncertainty':'NOT_INCLUDED'})
outputs={'cross_domain_main_results.csv':main,'b2_evidence_tiers.csv':[{'domain':n,'queries':len({x['query_id'] for x in actions if x['domain']==n}),'evidence':'FROZEN_EXTERNAL_DESCRIPTIVE','sources':27 if n=='Biomedical' else 5,'connected_components':27 if n=='Biomedical' else 1,'independence':'conditional source27 uncertainty' if n=='Biomedical' else 'sourceCI unavailable'} for n in ['Biomedical','Economics']]+[{'domain':x,'queries':n,'evidence':'EXPOSED_DEV','independence':'NOT_INDEPENDENT_TEST'} for x,n in [('HR',40),('Finance-EN',39),('Industrial',40),('Pharma',45)]],'b2_bio_eco_paired.csv':paired,'b2_candidate_harm_matrix.csv':matrices,'candidate_harm_analysis.csv':candidate,'b2_query_repairs_and_fallbacks.csv':repairs,'b2_action_transitions.csv':actions,'b2_decision_cost_components.csv':overhead,'information_value_analysis.csv':iv,'b2_information_value_breakdown.csv':iv,'b2_lifecycle_reuse_scenarios.csv':life,'b2_reuse_break_even.csv':reuse,'b2_timing_cohort_compatibility.csv':cohort,'b2_source_query_page_mapping.csv':dep,'b2_case_examples.csv':cases}
for filename,rows in outputs.items():C.table(C.R/filename,rows)
# Additional conditional bounds from published paired envelope intervals remain intact.
C.table(C.R/'b2_preserved_envelope_uncertainty.csv',C.load('reports/icde_eab_external_validation_013/monitor_001/auto2_attempt_001/summary/economics_posthoc_static_envelope.csv'))
fig,axs=plt.subplots(1,2,figsize=(10,4))
for row in paired:
 lab=row['domain']+' QP−'+('Q' if row['contrast'].endswith('Q_regret') else 'R100');y=paired.index(row)
 for ax,key,lo,hi in [(axs[0],'delta_r','r95_low','r95_high'),(axs[1],'delta_E2E_ms','E2E95_low_ms','E2E95_high_ms')]:ax.errorbar(row[key],y,xerr=[[row[key]-row[lo]],[row[hi]-row[key]]],fmt='o',capsize=3);ax.axvline(0,color='grey',linewidth=.6);ax.set_yticks(range(4));ax.set_yticklabels([x['domain']+' QP−'+('Q' if x['contrast'].endswith('Q_regret') else 'R100') for x in paired],fontsize=8)
axs[0].set_xlabel('Positive regret difference');axs[1].set_xlabel('Complete warm path difference (ms)');fig.suptitle('Pointwise descriptive intervals; Economics source CI unavailable');fig.tight_layout();fig.savefig(C.R/'paired_information_value.png',dpi=180);fig.savefig(C.R/'paired_information_value.pdf');plt.close(fig)
fig,axs=plt.subplots(1,2,figsize=(10,4))
for ax,name in zip(axs,['Biomedical','Economics']):
 for contained,harm,color in [(True,False,'tab:green'),(True,True,'tab:red'),(False,False,'tab:blue'),(False,True,'tab:orange')]:
  rr=[x for x in matrices if x['domain']==name and x['contained']==contained and x['harm']==harm];bottom=[sum(x['queries'] for x in matrices if x['domain']==name and x['plan']==p and ((x['contained'],x['harm']) in [(True,False),(True,True),(False,False),(False,True)][:[(True,False),(True,True),(False,False),(False,True)].index((contained,harm))])) for p in ['BM25-R50','BM25-R100']];ax.bar(['R50','R100'],[x['queries'] for x in rr],bottom=bottom,label=f'contained={contained},harm={harm}',color=color)
 ax.set_title(name);ax.set_ylabel('Queries');ax.legend(fontsize=6)
fig.tight_layout();fig.savefig(C.R/'candidate_coverage_harm.png',dpi=180);fig.savefig(C.R/'candidate_coverage_harm.pdf');plt.close(fig)
fig,axs=plt.subplots(1,2,figsize=(10,4))
for ax,model in zip(axs,['ColQwen2','ColPali']):
 for scenario in ['OCR_EXCLUSIVE_NEW_INDEX','OCR_SHARED_HALF_NEW_INDEX','OCR_PREPAID_NEW_INDEX','ALREADY_RESIDENT_ALL_PREPAID']:
  rr=[x for x in life if x['model']==model and x['scenario']==scenario];ax.plot([int(x['N']) for x in rr],[float(x['R100_over_FullV_ratio']) for x in rr],marker='o',label=scenario)
 ax.axhline(1,color='gray');ax.set_xscale('log');ax.set_title(model+' / Biomedical009 cohort');ax.set_xlabel('Hypothetical query count');ax.set_ylabel('R100 / FullV conditional totalwall');ax.legend(fontsize=5)
fig.tight_layout();fig.savefig(C.R/'lifecycle_ownership.png',dpi=180);fig.savefig(C.R/'lifecycle_ownership.pdf');plt.close(fig)
summary={n:{'R50_harm':sum(x['R50_r']>1e-10 for x in repairs if x['domain']==n),'R100_harm':sum(x['R100_r']>1e-10 for x in repairs if x['domain']==n),'fully_repaired':sum(x['fully_repaired'] for x in repairs if x['domain']==n),'improved':sum(x['improved'] for x in repairs if x['domain']==n),'worsened':sum(x['worsened'] for x in repairs if x['domain']==n),'QP_correct_reference_fallback':sum(x['correct_reference_fallback'] for x in repairs if x['domain']==n),'QP_false_safe':sum(x['false_safe'] for x in repairs if x['domain']==n)} for n in ['Biomedical','Economics']}
C.write(C.R/'b2_key_numbers.json',{'candidate':summary,'paired':paired,'information':iv,'queries':218,'Dev_queries':164,'new_model_evaluations':0,'GPU_jobs':0})
C.prose(C.R/'b2_reviewer_mechanisms.md','# B2 mechanism analysis — POSTHOC_DESCRIPTIVE\n\n'+json.dumps(summary,ensure_ascii=False,indent=2)+'\n\nPositive reference-relative regret is not mean quality difference. Candidate top10 containment implies exact ranking parity under fixed scorer/ties; missing candidates need not cause nDCG harm. R50→R100 can repair some queries and worsen others by inserting reference-low-judged pages: no universal monotonic quality. Severe harm threshold .05 is diagnostic, not perquery K1.\n\nAll218 external queries retained; 164 Dev repeatedly exposed. QP uses a paid probe, reuses lexical results on fast action, but pays it before FullV fallback. Actual measured complete path and withinrequest wall scopes are separate from optimistic standalone-counterfactual recompositions. No CPU+GPU addition.\n\nOpportunity is static outcome-fitted envelope minus label-dependent same-catalog fractional oracle; realization gap is measured policy minus oracle. The oracle is optimistic and unimplementable; no risk-matched execution or newcertificate was run. LP3 excludes R50 to match learnedcatalog; LP4 separately includes it. A negative dynamic increment must be retained.\n\nEconomics5PDFs connect into1sourcecomponent via multi-document relevance;53families do not substitute for independent sources. All paired intervals copied and numerically reconciled with closed008/013; no cherry-picked bootstrap repetitions. NewK1 NOT_CERTIFIED. Setup projections use009warm only;007and009crosscohort comparability is insufficient. No end-to-end Serving or businessreturn claim.\n')
C.prose(C.R/'claim_to_evidence_matrix.md','|Claim|Evidence|Status|\n|---|---|---|\n|Candidate count does not bound regret|candidate_harm_analysis / matrix / repair CSV; all218queries|POSTHOC_DESCRIPTIVE|\n|Probe lowers Q risk at extra completepathcost|b2_bio_eco_paired / measuredrequestcosts|DESCRIPTIVE|\n|QP universally beats R100|paired intervals cross0|NOT_SUPPORTED|\n|Observable information closes Oracle opportunity|samecatalog LP vs measured policies|INSUFFICIENT|\n|Ownership changes lifecycle ordering|009cohort conditional model; singletonsetup|CONDITIONAL_MODEL|\n|Economics sourcelevel guarantee|5PDFs→1component|NOT_CERTIFIED|\n|Serving acceleration|strictA/A absent|NOT_ESTABLISHED|\n')
C.finish('B2_analysis','PASS_POSTHOC_MECHANISM_ANALYSIS',json.dumps(summary,ensure_ascii=False),'Keep negative findings; no new independent benchmark or certification. Proceed B3 with no-CS branch if B0blocked.')
