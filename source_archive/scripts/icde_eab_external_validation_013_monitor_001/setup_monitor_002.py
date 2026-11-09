import os
os.environ['CUDA_VISIBLE_DEVICES']='';os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
import common as C
import json,sys,ast,collections,shutil,types
import numpy as np
C.start('setup_002')
frozen=C.load('artifacts/icde_eab_external_validation_013/resume_001/freeze_001/economics_frozen_protocol.json','UNCHANGED_CORE_PROTOCOL');assert C.sha(C.ROOT/'artifacts/icde_eab_external_validation_013/resume_001/freeze_001/economics_frozen_protocol.json')=='c6b76cf2242afe4b8791cd5997b56336f2e6779cc3e17af172575e222950b613'
assert len(frozen['query_ids'])==58 and len(set(frozen['query_ids']))==58 and frozen['seed']==C.SEED and frozen['frozen_Q_QP']['kappa']==20
assert frozen['random_mix_probabilities']==[0.,0.,0.7231294321302025,0.2768705678697975]
assert shutil.disk_usage(C.STORAGE).free>30*2**30
for info in frozen['official_inputs'].values():assert C.sha(info['path'])==info['SHA256']
for p,h in frozen['code_SHA256'].items():assert C.sha(C.ROOT/p)==h
for name in ['economics_worker_001.py','engine_frozen_004.py','gpu_smoke_monitor_001.py','summarize_economics_001.py','supervisor_001.py']:compile((C.ROOT/'scripts'/C.RUN/name).read_text(),name,'exec')
tree=ast.parse((C.ROOT/'scripts'/C.RUN/'economics_worker_001.py').read_text());calls=[n.func.attr for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)];assert not any(x in ['fit','tune','backward','step'] for x in calls)
assert C.sha(C.ROOT/'scripts'/C.RUN/'learning_base_001.py')==C.sha(C.ROOT/'scripts/icde_eab_independent_007/learning_base_001.py')
sys.path.insert(0,str(C.ROOT/'src'))
import torch,engine_frozen_004 as E,learning_base_001 as L
from aaber.router.fast_query_router import FastLexicalFeatureEncoder
torch.set_num_threads(1)
env=E.backend();pages=[{'corpus_id':0,'markdown':'alpha climate beta'},{'corpus_id':1,'markdown':'beta sustainability'}];bm=env['BM25'](pages);enc=FastLexicalFeatureEncoder();enc.fit_corpus([types.SimpleNamespace(searchable_text=p['markdown']) for p in pages]);f=enc.transform(types.SimpleNamespace(question='alpha climate'));x=np.array([f[n] for n in enc.feature_names]);o,s=bm.search('alpha climate');xp=np.r_[x,E.probe_features(bm,'alpha climate',o,s)];assert len(x)==150 and len(xp)==163
models=C.load('artifacts/icde_eab_independent_007/T0/locked_models.json','FROZEN_POLICIES');smoke=[]
for m in models:
 arr=[np.array(a) for a in m['model']];arr[0]=arr[0].astype(bool);pred=L.predict(tuple(arr),(xp if m['method']=='QP_regret' else x)[None]);assert pred.shape==(1,4) and np.isfinite(pred).all();smoke.append({'method':m['method'],'synthetic_feature_inference':'PASS','refit':False})
assert not torch.cuda.is_initialized()
execproto={**frozen,'code_SHA256':{str(p.relative_to(C.ROOT)):C.sha(p) for p in (C.ROOT/'scripts'/C.RUN).glob('*.py')},'execution_addendum':{'scope':'new run/stage paths, absolutebackupindexpath, onlyquery/qrelneededcolumns, sourceauditledgerkeys; BM25containmentdiagnosticfix andRecall100/missdiagnostics beforeoutcomes; no action/scoring/model/hyperparamchanges','worker_source':'007/t2_biomedical_exact_004','diff':'worker_format_resource_diff.patch','user_monitor_authorized':True,'poll_interval_s':60,'contamination_attempt_limit':3,'not_an_exclusive_GPU_reservation':True,'Orange_background':'durablependingentries; no MCPcredential copiedto server','desktop_notifications':'localWindowswatcher on meaningful changes; servercontinuesifdesktopoffline'}}
C.write(C.A/'execution_protocol.json',execproto);C.write(C.R/'execution_addendum.json',execproto['execution_addendum']);C.write(C.R/'CPU_preflight.json',{'status':'PASS_COMPILE_NO_TRAINING_CALLS_FIXED_MODEL_SYNTHETIC_ADAPTER','Q':150,'QP':163,'synthetic_models':smoke,'queries':58,'CUDA_initialized':False,'core_protocol_unchanged':True,'method_outcomes':0})
C.prose(C.R/'worker_format_resource_diff.patch',(C.ROOT/'scripts'/C.RUN/'worker_format_resource_diff.patch').read_text())
C.prose(C.R/'monitor_plan.md','# Actual autonomous execution plan\n\nPoll60s quietly untilone A6000 hasno GPUprocess, <128MiB and0%utilization; confirm3times, thenfixed8pagesmoke underResourceGuard. PASS/noOOM/noforeignpid only permits3independentprocesses×3requests×58queries×9methods andseparateGPUprofile, allon the selectedoneGPU. Externalprocessarrival terminates only ownexperimentprocessgroup, preservesabortedattempt, waitsfornewidle; atmost3contaminatedattempts. CUDA_OOM/otherCUDAerror/disk<30GiB/corehashfailure stops foruser, neverretunes. Originalmodel/κ20/R50/R100/BM25/Q/QP/RR/FrozenMix and58queryIDs fixed. SourceCI NA (oneconnectedcomponent);2000family/processpairedconditionalCI+fiveoverlappingdocLOO, allnegativecases, posthocstaticenvelopeseparate. NoESG, sealedCal/Eval/BL/test/CS, modeltraining, GitHubpush orCMT.\n\nServermonitor is independent of Codex turn lifetime. Desktopwatcher notifiesonlymeaningfulevents; OSnotifications arebesteffort. Orange tool credentials are not exported: livephase records arequeued underorange_pending for MCPwriteback on nextactiveconversation, rather than falselyclaimingautomaticOrangeupdates.\n')
C.finish('setup_002','PASS_AUTONOMOUS_MONITOR_EXECUTOR_PREFLIGHT_NO_GPU','fixedcorec6b76... verified;all4datasetSHAs;Q150/QP163syntheticPASS;worker/engine/statscompilePASS;no fit/tune/backward;noGPUinitialized','启动服务器唯一后台monitor；静态资源不变保持安静，关键状态桌面通知；真实完成后保留原始结果和待Orange回写记录。')
