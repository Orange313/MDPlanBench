from pathlib import Path
import difflib,json
B=Path(__file__).resolve().parent;old=B.parent/'resume_001'
common=(old/'common.py').read_text(encoding='utf8').replace("RUN='icde_eab_external_validation_013_resume_001'","RUN='icde_eab_external_validation_013_monitor_001'").replace("ART=ROOT/'artifacts'/PARENT/'resume_001';REPORT=ROOT/'reports'/PARENT/'resume_001'","ART=ROOT/'artifacts'/PARENT/'monitor_001';REPORT=ROOT/'reports'/PARENT/'monitor_001'")
common += "\nPLANS=['Full-Visual','BM25-R50','BM25-R100','BM25']\n"
(B/'common.py').write_text(common,encoding='utf8');(B/'archive_code.py').write_text((old/'archive_code.py').read_text(encoding='utf8').replace('icde-eab-external-validation-013-resume-001','icde-eab-external-validation-013-monitor-001'),encoding='utf8')
engine=(B/'original_engine_exact_004.txt').read_text(encoding='utf8');newengine=engine.replace("self.ip=C.ROOT/'cache/indexes'/index","self.ip=__import__('pathlib').Path(index)").replace("str(p.relative_to(C.ROOT))","str(p)")
(B/'engine_frozen_004.py').write_text(newengine,encoding='utf8')
source=(B/'original_t2_biomedical_exact_004.txt').read_text(encoding='utf8');t=source
def rep(a,b):
 global t
 assert a in t,a;t=t.replace(a,b)
rep("gpu=int(sys.argv[1]);proc=int(sys.argv[2]);C.start(f'T2/process_{proc}_001')","gpu=int(sys.argv[1]);proc=int(sys.argv[2]);attempt=sys.argv[3];C.start(f'{attempt}/process_{proc:02d}')")
rep('import engine_exact_004 as E','import engine_frozen_004 as E')
rep("C.ART/'T1/biomedical_frozen_protocol.json'","C.ART/'setup_001/execution_protocol.json'")
rep("index=C.ROOT/'cache/indexes/icde_eab_independent_007_biomedical_colqwen_001'","index=C.STORAGE/'indexes'/('economics_auto_'+attempt)")
rep("C.ART/'T1_preparation/ocr_001/pages.json'","C.STORAGE/'ocr_001/pages.json'")
rep('shutil.disk_usage(C.ROOT).free>15*2**30','shutil.disk_usage(C.STORAGE).free>30*2**30')
rep('E.Engine(index.name,guard)','E.Engine(str(index),guard)')
rep("raw=C.ROOT/'artifacts/icde_eab_main_006/X3/biomedical_audit_inputs_001'","raw=C.STORAGE/'assets'")
rep("C.ART/'T0/locked_models.json'","C.ROOT/'artifacts/icde_eab_independent_007/T0/locked_models.json'")
rep(':Biomedical:',':Economics:')
rep('==160','==58')
rep("'total':160","'total':58")
rep("'unique_queries':160","'unique_queries':58")
rep('1016','452')
rep('Biomedical','Economics');rep('Bio_','Economics_')
rep("C.write(C.A/'completed.json'","C.write(C.A/'completed.json'")
rep("else list(range(len(eng.ids)));contained=", "else bmorder[:10] if action=='BM25' else list(range(len(eng.ids)));contained=")
rep("'reference_top10_in_candidates':contained", "'BM25_Recall100':len(positives&{eng.ids[j] for j in bmorder[:100]})/len(positives),'reference_judged_positive_misses':len({p for p in ref if ql[qid].get(p,0)>0}-{eng.ids[j] for j in cand}),'reference_top10_in_candidates':contained")
# Resource-only guard before timings/profiling; unchanged model/route/scoring and random weights.
rep('guard.check();torch.cuda.synchronize();t=time.perf_counter()',"guard.check();assert shutil.disk_usage(C.STORAGE).free>30*2**30,'DISK_BLOCKED';torch.cuda.synchronize();t=time.perf_counter()")
rep("return pq.read_table(path).to_pylist()","return pq.read_table(path,columns={'queries':['query-id','query'],'qrels':['query-id','corpus-id','score']}[kind]).to_pylist()")
compile(t,'economics_worker_001.py','exec');compile(newengine,'engine_frozen_004.py','exec')
(B/'economics_worker_001.py').write_text(t,encoding='utf8')
# Same frozen 8-page smoke, unique output per monitor attempt; no change to model/config.
smoke=(old/'gpu_smoke_001.py').read_text(encoding='utf8').replace("C.start('gpu_smoke_001')","C.start(sys.argv[1])").replace("C.finish('gpu_smoke_001',","C.finish(sys.argv[1].replace('/','_'),").replace("out=C.STORAGE/'smoke_index_001'","out=C.STORAGE/('smoke_'+sys.argv[1].replace('/','_'))")
smoke=smoke.replace("chosen=idle[0];gpu=chosen['gpu']", "chosen=next((x for x in idle if x['gpu']==int(sys.argv[2])),None)\nif chosen is None:\n C.write(C.R/'gpu_smoke_result.json',{'status':'RESOURCE_BLOCKED','model_load':'NOT_RUN','CUDA_OOM':'NOT_RUN'})\n C.finish(sys.argv[1].replace('/','_'),'RESOURCE_BLOCKED','SelectedGPUchangedbeforeCUDA','waitfornewidle;noCUDAstarted');sys.exit()\ngpu=chosen['gpu']")
compile(smoke,'gpu_smoke_monitor_001.py','exec');(B/'gpu_smoke_monitor_001.py').write_text(smoke,encoding='utf8')
(B/'worker_format_resource_diff.patch').write_text(''.join(difflib.unified_diff(source.splitlines(True),t.splitlines(True),fromfile='007/frozen_Biomedical_worker',tofile='013/unchanged_policy_Economics_adapter'))+''.join(difflib.unified_diff(engine.splitlines(True),newengine.splitlines(True),fromfile='007/exact_engine',tofile='013/absolute_index_path_engine')),encoding='utf8')
print(json.dumps({'status':'PASS_SYNTAX_AND_EXACT_REPLACEMENT_ANCHORS','scientific_parameter_changes':0,'model_or_policy_refit':0}))
