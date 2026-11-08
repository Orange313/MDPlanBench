"""Pharma split audit only: no qrels, answers, plan outcomes, Cal or Eval losses."""
import common as C
import numpy as np,collections,hashlib,pathlib,re,unicodedata,difflib,json,os,time,sys
import pyarrow.parquet as pq
C.start('audit_001');C.STAGE='R1_FIXED_CORPUS_AUDIT'
P=C.ROOT/'artifacts/icde_decisive_suite_002/public_sources'
protocol={'run_id':C.RUN,'time_bj':C.stamp(),'status':'RULES_LOCKED_BEFORE_PROJECT_PHARMA_PLAN_OUTCOMES','objective':'Fixed-Corpus Query Generalization only; no unseen-document claim','seed':C.SEED,'corpus_revision':'262e203d7c59c55947f7042812e0bcc1eee190b1','primary_language':'canonical English representation, native original language not proved','lexical_edges':'inherit old candidate-family membership; additionally normalized exact, token Jaccard>=.5 or SequenceMatcher>=.85','semantic_audit':{'model':'BAAI/bge-base-en-v1.5','revision':'a5beb1e3e68b9ab74eb54cfd186867f64f240e1a','mode':'CPU FP32 normalized CLS, no retrieval instruction for sentence similarity','max_length':512,'batch_size':16,'threads':2,'main_edge_cosine':.85,'sensitivity_cosine':[.80,.85,.90],'ambiguous_band':[.80,.85],'ambiguity_rule':'quarantine entire endpoint families of cross-role pairs; no post-score tuning','meaning':'conservative similarity groups, not verified semantic equivalence or IID proof'},'assignment':'retain original candidate role of unaffected family; cross-role merged family entirely QUARANTINED; ambiguous cross-role endpoints QUARANTINED; no backfill/reassignment from Cal/Eval','fit_dev':'English rows only; same-family group CV; human/SDG/source strata reported, not outcomes-selected','translations':'two release blocks; align within language by ordinal with provenance-field checks; aliases inherit English family role; all non-English rows excluded from training/cal/eval','source_components':'sensitivity only; reused prior provenance metadata, not primary grouping or n_IID','risk':{'epsilon':.05,'delta_per_domain':.01,'new_contract':'PENDING_SEPARATE_AUDIT','Cal_and_Eval_loss_access':False},'allowed_query_columns':['query_id','query','language','query_generator','query_generation_pipeline','source_type','query_type_for_generation','query_types','query_format'],'forbidden_columns':['answer','raw_answers','content_type','bounding_boxes'],'new_raw_qrels_reads':0,'new_plan_scores_read':0,'literature_exposure':'methodology source fetch included public paper benchmark aggregate table; no project Pharma query-plan outcomes, Cal/Eval losses or thresholds selected from it; no claim of never seeing public benchmark summaries'}
C.write(C.R/'preaudit_protocol.json',protocol);C.write(C.A/'rules_freeze_record.json',{'time_bj':C.stamp(),'protocol_sha256':C.sha(C.R/'preaudit_protocol.json'),'freeze_scope':'unsupervised grouping/assignment rules ONLY; not risk certification or unsealing'})
for f,h in C.EXPECTED.items():
 C.load(C.FROZEN/f,'UNCHANGED_005_METADATA');assert C.INPUT[str((C.FROZEN/f).relative_to(C.ROOT))]['sha256']==h
previous=C.load('reports/icde_decisive_suite_002/manifest.json','PREVIOUS_CLOSED_RUN_METADATA');assert previous['new_formal_certification']==False
prior=C.load(C.OLD/'new_domain_partition_candidate.json','PRIOR_CANDIDATE_ROLE_IDS_ONLY');oldrole={int(q):x['role'] for x in prior['roles'] for q in x['query_ids']};oldfamily={int(q):x['family_id'] for x in prior['roles'] for q in x['query_ids']}
api=C.load(P/'pharma_api.json','PINNED_OFFICIAL_LFS_METADATA');assert api['sha']==protocol['corpus_revision'];official={x['rfilename']:x for x in api['siblings']};qpath=P/'pharma_queries.parquet';assert C.sha(qpath)==official['queries/test-00000-of-00001.parquet']['lfs']['sha256']
cols=protocol['allowed_query_columns'];qrows=pq.read_table(qpath,columns=cols).to_pylist();C.INPUT[str(qpath.relative_to(C.ROOT))]={'sha256':C.sha(qpath),'role':'UNLABELED_QUERY_COLUMNS_ONLY','columns':cols};C.write(C.A/'parquet_projection_audit.json',{'path':str(qpath),'columns_loaded':cols,'answer_columns_loaded':[],'qrels_opened':False})
english=sorted([r for r in qrows if r['language']=='english'],key=lambda r:r['query_id']);ids=[int(q['query_id']) for q in english];assert set(ids)==set(oldrole) and len(ids)==364
metadata={int(q['query_id']):q for q in english};ix={q:i for i,q in enumerate(ids)}
# Detect the two multilingual release blocks structurally; no qrels or answers are consulted.
runs=[]
for row in sorted(qrows,key=lambda r:r['query_id']):
 if not runs or runs[-1]['language']!=row['language']:runs.append({'language':row['language'],'rows':[]})
 runs[-1]['rows'].append(row)
aliases=[];translation_checks=[];sourcefields=['query_generator','query_generation_pipeline','source_type','query_type_for_generation','query_types','query_format']
for block in range(0,len(runs),6):
 rr=runs[block:block+6];assert len(rr)==6 and rr[0]['language']=='english' and len(set(x['language'] for x in rr))==6;assert len({len(x['rows']) for x in rr})==1
 for j,en in enumerate(rr[0]['rows']):
  for lang in rr:
   tr=lang['rows'][j];same=all(tr[k]==en[k] for k in sourcefields);translation_checks.append({'English_query_id':int(en['query_id']),'alias_query_id':int(tr['query_id']),'language':tr['language'],'release_block':block//6,'provenance_fields_equal':same});aliases.append((int(en['query_id']),int(tr['query_id']),tr['language'],same))
assert len(aliases)==2184
# Official literature declares multilingual translation; fields/order are structural validation, not independent human semantic verification.
C.table(C.R/'translation_alias_structural_checks.csv',translation_checks)
models=C.load('manifests/hr_models_verified.json','FROZEN_MODELS');dense=models['dense'];assert dense['revision']==protocol['semantic_audit']['revision']
for f in dense['files']:
 path=pathlib.Path(f['path']);assert C.sha(path)==f['sha256'];C.INPUT[str(path)]={'sha256':f['sha256'],'role':'LOCKED_CPU_DEDUP_MODEL_ONLY'}
olddev=[]
for d in C.DOM:
 for q in C.load(f'artifacts/splits/query_generalization_002/{d}/dev_queries.json','ALLOWED_OLD_DEV_QUERY_TEXT_NO_LABELS'):olddev.append({'domain':d,'query_id':int(q['query_id']),'query':q['query']})
# Force this audit to use no GPU, independently of availability.
os.environ['CUDA_VISIBLE_DEVICES']='';os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
import torch
from transformers import AutoModel,AutoTokenizer
torch.set_num_threads(2);torch.manual_seed(C.SEED);tokenizer=AutoTokenizer.from_pretrained(dense['local_path'],local_files_only=True);model=AutoModel.from_pretrained(dense['local_path'],local_files_only=True,dtype=torch.float32).to('cpu').eval()
texts=[q['query'] for q in english]+[q['query'] for q in olddev];enc=[];lengths=[];start=time.perf_counter()
with torch.inference_mode():
 for first in range(0,len(texts),16):
  batch=texts[first:first+16];full=tokenizer(batch,add_special_tokens=True,truncation=False)['input_ids'];lengths.extend(map(len,full));t=tokenizer(batch,padding=True,truncation=True,max_length=512,return_tensors='pt');out=model(**t).last_hidden_state[:,0].float();out=torch.nn.functional.normalize(out,dim=1);enc.append(out.numpy())
  if first%64==0:print(json.dumps({'stage':'R1_FIXED_CORPUS_AUDIT','encoded':min(first+16,len(texts)),'total':len(texts),'CPU_only':True,'elapsed_s':time.perf_counter()-start,'time_bj':C.stamp()}),flush=True)
emb=np.concatenate(enc);assert np.isfinite(emb).all() and not torch.cuda.is_initialized();np.savez(C.A/'unlabeled_query_embeddings.npz',English_query_ids=np.array(ids),English_embeddings=emb[:364],allowed_old_Dev_embeddings=emb[364:]);similarity=emb[:364]@emb[:364].T;crosssim=emb[:364]@emb[364:].T
norm=lambda s:' '.join(re.findall(r'[a-z0-9]+',unicodedata.normalize('NFKC',s).lower()));ss=[norm(q['query']) for q in english];tokens=[set(s.split()) for s in ss];pairs=[];edges=[]
for i in range(364):
 for j in range(i):
  jac=len(tokens[i]&tokens[j])/max(1,len(tokens[i]|tokens[j]));seq=difflib.SequenceMatcher(None,ss[i],ss[j]).ratio();cos=float(similarity[i,j]);lex=ss[i]==ss[j] or jac>=.5 or seq>=.85 or oldfamily[ids[i]]==oldfamily[ids[j]];row={'query_i':ids[j],'query_j':ids[i],'exact_normalized':ss[i]==ss[j],'token_jaccard':jac,'sequence_similarity':seq,'BGE_cosine':cos,'lexical_edge':lex,'main_semantic_edge':cos>=.85,'ambiguity_edge':.80<=cos<.85,'prior_roles_equal':oldrole[ids[j]]==oldrole[ids[i]],'query_i_hash':hashlib.sha256(ss[j].encode()).hexdigest(),'query_j_hash':hashlib.sha256(ss[i].encode()).hexdigest()};pairs.append(row)
  if lex or cos>=.80:edges.append(row)
C.table(C.R/'all_English_pairwise_similarity.csv',pairs);C.table(C.R/'near_duplicate_edges.csv',edges)
def families(threshold):
 par=list(range(364))
 def root(i):
  while par[i]!=i:par[i]=par[par[i]];i=par[i]
  return i
 for r in pairs:
  if r['lexical_edge'] or r['BGE_cosine']>=threshold:par[root(ix[r['query_i']])]=root(ix[r['query_j']])
 fam=collections.defaultdict(list)
 for i in range(364):fam[root(i)].append(ids[i])
 return list(fam.values())
sensitivity=[]
for tau in [.80,.85,.90]:
 ff=families(tau);bad=[v for v in ff if len({oldrole[q] for q in v})>1];sensitivity.append({'BGE_threshold':tau,'families':len(ff),'cross_prior_role_families':len(bad),'queries_in_cross_prior_role_families':sum(map(len,bad)),'max_family_size':max(map(len,ff)),'cost_or_quality_used_for_selection':False})
C.table(C.R/'grouping_sensitivity.csv',sensitivity)
main=families(.85);familyid={};members={};candidate_role={};quarantine=collections.defaultdict(set)
for v in main:
 key=hashlib.sha256(('Pharma_FCQG_v1:'+','.join(map(str,sorted(v)))).encode()).hexdigest();members[key]=sorted(v);roles={oldrole[q] for q in v};candidate_role[key]=next(iter(roles)) if len(roles)==1 else 'QUARANTINED'
 for q in v:familyid[q]=key
 if len(roles)>1:quarantine[key].add('main_family_merges_prior_roles')
for r in edges:
 if r['BGE_cosine']>=.80 and oldrole[r['query_i']]!=oldrole[r['query_j']]:
  quarantine[familyid[r['query_i']]].add('ambiguous_or_semantic_pair_crosses_prior_roles');quarantine[familyid[r['query_j']]].add('ambiguous_or_semantic_pair_crosses_prior_roles')
cross_old=[]
for i in range(364):
 for j,x in enumerate(olddev):
  exact=ss[i]==norm(x['query']);cos=float(crosssim[i,j])
  if exact or cos>=.80:
   cross_old.append({'Pharma_query_id':ids[i],'old_Dev_domain':x['domain'],'old_Dev_query_id':x['query_id'],'exact':exact,'BGE_cosine':cos,'status':'CONSERVATIVE_QUARANTINE_NOT_PROVEN_DUPLICATE'});quarantine[familyid[ids[i]]].add('possible_overlap_with_previously_used_Dev')
C.table(C.R/'cross_allowed_old_Dev_candidates.csv',cross_old,fields=['Pharma_query_id','old_Dev_domain','old_Dev_query_id','exact','BGE_cosine','status'])
# If structural translation metadata differ, quarantine all involved English families rather than invent alias certainty.
for en,tr,lang,same in aliases:
 if not same:quarantine[familyid[en]].add('translation_provenance_mismatch')
role={q:('QUARANTINED' if quarantine[familyid[q]] else candidate_role[familyid[q]]) for q in ids}
for r in pairs:
 if r['lexical_edge'] or r['BGE_cosine']>=.80:
  if role[r['query_i']]!='QUARANTINED' and role[r['query_j']]!='QUARANTINED':assert role[r['query_i']]==role[r['query_j']]
assert all(role[q]==oldrole[q] or role[q]=='QUARANTINED' for q in ids),'No Cal/Eval members moved into training'
provenance=C.load('reports/icde_decisive_suite_002/R1/retry_002/split_dependency_graph.csv','PREVIOUS_SOURCE_ASSOCIATION_METADATA_NO_NEW_QRELS_READ');prov={int(r['query_id']):r for r in provenance};records=[]
for q in ids:
 r=metadata[q];records.append({'query_id':q,'query_hash':hashlib.sha256(r['query'].encode()).hexdigest(),'original_candidate_role':oldrole[q],'family_id':familyid[q],'new_role':role[q],'quarantine_reasons':sorted(quarantine[familyid[q]]),'query_generator':r['query_generator'],'generation_pipeline':r['query_generation_pipeline'],'source_type':r['source_type'],'query_type_for_generation':r['query_type_for_generation'],'source_component':prov[q]['source_component'],'labels_access':'FIT_DEV_ONLY_AFTER_SEPARATE_MATERIALIZATION' if role[q] in ['fit','development'] else 'DENY','semantic_human_validated':False,'IID_validated':False})
C.table(C.R/'English_query_family_split.csv',records)
aliasrows=[{'English_query_id':en,'alias_query_id':tr,'language':lang,'family_id':familyid[en],'role':role[en],'active_for_training_or_evaluation':lang=='english' and role[en]!='QUARANTINED','structural_provenance_match':same,'semantic_translation_validation':'NOT_INDEPENDENTLY_VERIFIED_NON_ENGLISH_EXCLUDED'} for en,tr,lang,same in aliases];C.table(C.R/'translation_family_aliases.csv',aliasrows)
fams=[]
for fid,v in sorted(members.items()):
 selected=sorted(v,key=lambda q:hashlib.sha256((str(C.SEED)+':representative:'+str(q)).encode()).hexdigest())[0];fams.append({'family_id':fid,'English_query_ids':v,'role':role[v[0]],'future_candidate_representative':selected,'future_n_IID':None,'quarantine_reasons':sorted(quarantine[fid])})
split={'run_id':C.RUN,'status':'GROUPS_AND_ROLES_FROZEN_FOR_FIT_DEV_EXPLORATION_ONLY','objective':protocol['objective'],'rules_protocol_sha256':C.sha(C.R/'preaudit_protocol.json'),'seed':C.SEED,'families':fams,'IID_effective_n':None,'Cal_Eval_unsealing_authorized':False,'no_performance_seen_in_project':True,'old_candidate_manifest_sha256':C.sha(C.OLD/'new_domain_partition_candidate.json'),'source_query_parquet_sha256':C.sha(qpath),'English_canonical_query_n':364,'all_language_rows':2184,'non_English_active_rows':0,'sampling_target':'benchmark canonical-English families; future deployment mixture/query prevalence not yet specified','provenance_scope':'same fixed corpus; source-document overlap allowed; not unseen-document generalization'}
C.write(C.R/'split_manifest.json',split);C.write(C.A/'split_freeze_record.json',{'time_bj':C.stamp(),'split_sha256':C.sha(C.R/'split_manifest.json'),'rules_sha256':C.sha(C.R/'preaudit_protocol.json'),'freeze_scope':'group IDs/assignment only; NOT authorization for Cal/Eval labels, NOT a frozen risk protocol'})
for ro in ['fit','development']:
 rr=[{'query_id':q['query_id'],'query':q['query'],'language':'english','family_id':familyid[q['query_id']],'generator':q['query_generator']} for q in english if role[q['query_id']]==ro];C.write(C.A/(ro+'_unlabeled_queries.json'),rr)
counts=[]
for ro in ['fit','development','new_calibration_sealed','new_final_evaluation_sealed','QUARANTINED']:
 z=[r for r in records if r['new_role']==ro];counts.append({'role':ro,'English_queries':len(z),'candidate_families':len(set(r['family_id'] for r in z)),'human':sum(r['query_generator']=='human' for r in z),'SDG':sum(r['query_generator']=='sdg' for r in z),'summary_source':sum(r['source_type']=='summary' for r in z),'image_source':sum(r['source_type']=='image' for r in z),'effective_IID_n':None,'labels_opened':0})
C.table(C.R/'role_capacity.csv',counts)
source_counts=[]
for comp in sorted({r['source_component'] for r in records}):
 z=[r for r in records if r['source_component']==comp];source_counts.append({'source_component':comp,'English_query_n':len(z),'primary_active_roles':sorted({r['new_role'] for r in z if r['new_role']!='QUARANTINED'}),'use':'sensitivity only, not primary split or IID count'})
C.table(C.R/'source_component_sensitivity.csv',source_counts)
# Authorization gates are separate from the split manifest. Test denials BEFORE any label/file read.
access={'run_id':C.RUN,'Fit_labels':'PENDING_SCOPED_MATERIALIZATION','Dev_labels':'PENDING_SCOPED_MATERIALIZATION','Cal_labels':'SEALED_DENY','Eval_labels':'SEALED_DENY','old_BL_test_CS':'SEALED_DENY','new_certification':'DENY_PENDING_SEPARATE_RISK_ASSUMPTION_POWER_AUDIT','epsilon':.05,'delta':.01,'new_qrels_reads_this_run':0,'new_answer_payload_reads_this_run':0}
C.write(C.R/'access_policy.json',access)
tests=[]
def authorize(qid,purpose):
 ro=role.get(qid)
 if purpose not in ['fit','development'] or ro!=purpose:raise PermissionError('denied before label/file I/O')
 return True
for purpose,ro in [('fit','new_calibration_sealed'),('development','new_final_evaluation_sealed'),('calibrate','new_calibration_sealed'),('eval','new_final_evaluation_sealed')]:
 qs=[q for q in ids if role[q]==ro]
 if not qs:tests.append({'requested':purpose,'actual_role':ro,'status':'NOT_RUN_NO_ELIGIBLE_QUERY','label_file_reads':0});continue
 try:authorize(qs[0],purpose);raise AssertionError('protected query authorized')
 except PermissionError:tests.append({'requested':purpose,'actual_role':ro,'status':'PASS_DENIED_BEFORE_IO','label_file_reads':0})
for ro in ['fit','development']:
 qs=[q for q in ids if role[q]==ro]
 if qs:assert authorize(qs[0],ro);tests.append({'requested':ro,'actual_role':ro,'status':'PASS_SCOPED_ID_CHECK_ONLY_NO_LABEL_READ','label_file_reads':0})
C.write(C.A/'seal_interface_checks.json',tests)
capacity=[]
for r in counts:
 n=r['candidate_families']
 if r['role'] in ['new_calibration_sealed','new_final_evaluation_sealed']:capacity.append({'role':r['role'],'available_candidate_families':n,'validated_IID_n':None,'hypothetical_zero_loss_UCB_IF_IID_alpha01':-np.expm1(np.log(.01)/n) if n else None,'minimum_zero_loss_IID_n_for_epsilon05':90,'status':'HYPOTHETICAL_CAPACITY_NOT_CERTIFICATION'})
C.table(C.R/'capacity_diagnostic.csv',capacity)
recipe={'status':'LOCKED_RECIPE_PENDING_DOWNLOAD_AND_BUILD','corpus_revision':api['sha'],'official_corpus_files':[{k:x[k] for k in ['rfilename','size','lfs']} for x in api['siblings'] if x['rfilename'].startswith('corpus/')],'plans':['T-BM25','BM25 Top50 exact visual rerank','Full V-Multi exact MaxSim'],'models':{k:{a:v.get(a) for a in ['repo','revision']} for k,v in models.items()},'BM25':'same frozen tokenizer/k1=1.5/b=.75; score0 omitted','visual_score':'FP32 same MaxSim for full/subset; global passage padding; fixed batch64; (-score,int_page_id) ties','index_id':'pharma_fixedcorpus_index_001','actual_index_sha256':None,'local_corpus_payload_verified':False,'query_outcomes_viewed':False}
C.write(C.R/'fixed_corpus_index_recipe.json',recipe)
sampling={'query_population':'curated official benchmark canonical-English representation, not a random traffic sample','source_mechanisms':{'human':182,'SDG':182,'summary':259,'image':105},'IID_evidence':'INSUFFICIENT','why':['no released random-query sampling frame/inclusion probabilities','two human questions may share a context; summary/annotator/template IDs unavailable','generation and filtering change the population; generator labels do not prove independent draws','duplicate removal and random split do not prove IID or future same-distribution sampling','source-component sharing allowed under fixed corpus, but residual within-context dependence remains unknown'],'known_components':23,'known_components_are_IID_n':False,'n_effective_for_new_K1':None,'legitimate_scope':'leakage-controlled Fit/Dev exploration conditional on conservative query-family rule; all performance exploratory','future_required':['declare target query/family weighting and human/SDG mixture','specify defensible independent sampling unit and future stability','separate risk object/alpha/bound/power audit before any Cal loss access','explicit later authorization for Cal/Eval; old sealed labels stay sealed']}
C.write(C.R/'sampling_assumptions_audit.json',sampling)
trainrows=next(r for r in counts if r['role']=='fit');devrows=next(r for r in counts if r['role']=='development');train_ok=trainrows['English_queries']>0 and devrows['English_queries']>0 and all(x['status'].startswith('PASS') for x in tests)
gate={'Fit_Dev_exploration_data_gate':'PASS_CONDITIONAL_GROUPED_EXPLORATION' if train_ok else 'INSUFFICIENT','Fit_Dev_execution_readiness':'BLOCKED_INDEX_AND_ROLE_SCOPED_QRELS_NOT_MATERIALIZED','formal_certification_gate':'NOT_CERTIFIED','Eval_gate':'SEALED_NOT_RUN','cross_active_role_near_duplicate_edges':0,'semantic_independence_proved':False,'effective_IID_n':None,'corpus_identity':'PASS_OFFICIAL_LFS_IDENTITIES_LOCKED','actual_local_index':'NOT_BUILT_HASH_PENDING','models':'PASS_REUSED_FROZEN_REVISIONS','source_overlap':'ALLOWED_ONLY_FIXED_CORPUS_QUERY_GENERALIZATION','no_user_decision_inferred_for_unsealing':True,'g0_passed':False}
C.write(C.R/'training_certification_gate.json',gate)
C.prose(C.R/'independence_audit.md','# 固定语料查询泛化：独立性与泄漏审计\n\n'+json.dumps(C.clean({'counts':counts,'sensitivity':sensitivity,'sampling':sampling,'gate':gate}),ensure_ascii=False,indent=2)+'\n\n同文档跨分区不是本目标下自动监督泄漏，故不再以23组件跨角色一项否决Fit/Dev。但组件数量也不是有效IID查询样本量。问题族来自规则化文本/语义保守聚类，无人工语义等价证明，残余依赖不能消除或由bootstrap证明。\n\n翻译按两个公开发布块342/22、各六语言序列以及非答案来源字段校验，所有非英语alias不参与训练或评测；结构匹配不是人工翻译准确率验证。未重新读取qrels或answer，source组件复用上一轮已生成的结构元数据。\n\n[官方创建方法§3.2–3.5](https://arxiv.org/html/2601.08620v2)说明问题包含人工/生成和过滤、翻译等流程，并非发布随机流量抽样设计。本轮从方法来源推断IID证据不足，而不是断言所有查询必然不独立。[固定数据卡](https://huggingface.co/datasets/vidore/vidore_v3_pharmaceuticals/tree/262e203d7c59c55947f7042812e0bcc1eee190b1)提供来源字段与许可。[BGE官方说明](https://huggingface.co/BAAI/bge-base-en-v1.5)支持CLS归一化和句子相似无指令模式；cosine阈值只是审计规则，无预设概率含义。\n\n公开文献抓取自动包含官方聚合性能表，未用于本轮任何划分、阈值或模型选择；没有打开项目新域query×plan结果、Cal/Eval标签或损失。不宣称对一切公开基准成绩完全未知。\n')
C.prose(C.R/'decision_gate.md','# 训练 / 认证 / Eval 门槛\n\n'+json.dumps(C.clean(gate),ensure_ascii=False,indent=2)+'\n\n**允许范围**：按冻结问题族进行Fit/Dev探索性训练与比较；来源组件作为敏感性分组。模型/语料和索引构建配方固定，实际index尚未构建，不能称检索准备完成。训练执行前须完成已授权Fit/Dev标签的严格分区物化与索引hash绑定；本轮不打开这些标签。\n\n**继续暂停**：正式Cal认证与Eval成绩读取；尚缺可辩护独立采样单元/有效n、总体加权、风险合同、置信界/多检验功效的独立审计，epsilon=.05、delta=.01不变。没有因为split冻结而解除封存。\n')
C.prose(C.R/'claim_to_evidence_matrix.md','# Claim–evidence\n\n|主张|状态|证据|\n|---|---|---|\n|同来源文档允许跨split，只声明fixed-corpus query generalization|PASS_SCOPE|用户决定、preaudit_protocol|\n|预定义相似边在active roles间无交叉|PASS_RULE_BASED|all_English_pairwise_similarity、split_manifest|\n|所有真实问题族已证明语义独立/IID|INSUFFICIENT|sampling_assumptions_audit|\n|新域Fit/Dev模型效果|NOT_RUN|没有读新域plan outcomes|\n|新K1/独立Eval成立|NOT_CERTIFIED / NOT_RUN|access_policy、seal_interface_checks|\n|新Pharma索引已构建|NOT_RUN|fixed_corpus_index_recipe实际hash为null|\n')
facts='固定语料目标下完成364英语/2184多语言行审计；全66066英语对及与119旧Dev问题的语义扫描，仅CPU。保守规则形成'+str(len(main))+'候选族；Fit/Dev保留'+str(trainrows['English_queries'])+'/'+str(devrows['English_queries'])+'查询（'+str(trainrows['candidate_families'])+'/'+str(devrows['candidate_families'])+'族），Cal/Eval继续封存，隔离'+str(next(r for r in counts if r['role']=='QUARANTINED')['English_queries'])+'查询；跨active角色预定义近重复边0。'
decision='Fit/Dev仅通过规则化隔离下的探索性数据门槛，尚需索引构建/hash和分区标签物化才可实际训练。IID/有效n仍UNKNOWN；正式认证NOT_CERTIFIED，Eval SEALED。保留23组件为敏感性，不作IID n，不修改ε=.05/δ=.01或005。'
C.prose(C.R/'round_summary.md','# 结论—决策—阻塞—证据\n\n**结论**：'+facts+'\n\n**决策**：'+decision+'\n\n**阻塞**：随机抽样/上下文与标注者依赖证据缺失；尚无实际Pharma index；Cal/Eval合同与授权保持暂停。\n\n**证据**：本目录split_manifest、independence_audit、role_capacity、sampling_assumptions、gate、hash清单；新标签、答案、plan results读取均0。\n')
C.write(C.A/'audit_metrics.json',{'English_pair_count':len(pairs),'cross_old_Dev_pair_count':crosssim.size,'main_families':len(main),'sensitivity':sensitivity,'counts':counts,'translation_provenance_mismatches':sum(not r['provenance_fields_equal'] for r in translation_checks),'token_lengths':{'max':max(lengths),'truncated':sum(x>512 for x in lengths)},'embedding_CPU_wall_s':time.perf_counter()-start,'GPU_jobs':0,'Cal_Eval_loss_reads':0,'qrels_reads':0,'answer_payload_reads':0,'gate':gate})
C.finish('PASS_GROUPED_FIT_DEV_DATA_GATE_NOT_CERTIFIED',facts,decision)
