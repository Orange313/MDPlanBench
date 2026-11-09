"""One guarded fixed-model smoke only; resource failure never becomes an OOM/no-OOM result."""
import common as C
import os,sys,subprocess,json,time,shutil,ctypes,threading
from pathlib import Path
C.start(sys.argv[1]);assert shutil.disk_usage(C.STORAGE).free>=30*2**30
def observed():
 raw=subprocess.check_output(['nvidia-smi','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader'],text=True)
 procs=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid,process_name,used_memory','--format=csv,noheader'],text=True)
 busy={s.split(',')[0].strip() for s in procs.splitlines()};rows=[]
 for line in raw.splitlines():
  z=[x.strip() for x in line.split(',')];rows.append({'gpu':int(z[0]),'uuid':z[1],'memory_MiB':int(z[2].split()[0]),'utilization':int(z[3].split()[0]),'idle':z[1] not in busy and int(z[2].split()[0])<128 and int(z[3].split()[0])==0})
 return {'time_bj':C.stamp(),'rows':rows,'processes':procs}
samples=[observed()];idle=[x for x in samples[0]['rows'] if x['idle']]
if not idle:
 C.write(C.R/'gpu_smoke_result.json',{'status':'RESOURCE_BLOCKED','observations':samples,'model_load':'NOT_RUN','peak_VRAM':'NOT_MEASURED','CUDA_error':'NOT_RUN','CUDA_OOM':'NOT_RUN_NOT_OBSERVED','no_OOM_pass':False,'full_main_experiment':'NOT_RUN_RESOURCE_BLOCKED'})
 C.finish(sys.argv[1].replace('/','_'),'RESOURCE_BLOCKED__CUDA_OOM_NOT_RUN','No idleGPU by process/memory/utilization;model/pageindexsmokeNOT_RUN;fullEconomicsNOT_RUN','不共享占用卡，不以空余显存推断独占，不将未运行写成无OOM通过。');sys.exit()
chosen=next((x for x in idle if x['gpu']==int(sys.argv[2])),None)
if chosen is None:
 C.write(C.R/'gpu_smoke_result.json',{'status':'RESOURCE_BLOCKED','model_load':'NOT_RUN','CUDA_OOM':'NOT_RUN'})
 C.finish(sys.argv[1].replace('/','_'),'RESOURCE_BLOCKED','SelectedGPUchangedbeforeCUDA','waitfornewidle;noCUDAstarted');sys.exit()
gpu=chosen['gpu']
for _ in range(2):
 time.sleep(1);samples.append(observed());assert next(x for x in samples[-1]['rows'] if x['gpu']==gpu)['idle'],'RESOURCE_BLOCKED_BEFORE_CUDA'
C.write(C.A/'three_idle_checks.json',samples)
os.environ['CUDA_VISIBLE_DEVICES']=str(gpu);os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1';os.environ['TOKENIZERS_PARALLELISM']='false'
sys.path.insert(0,str(C.ROOT/'src'))
from mdrouter_v5.gpu_accounting import ResourceGuard,profile_call
guard=ResourceGuard(gpu,C.A/'resource_guard.json',period=.1)
records=[];stop=threading.Event();model=processor=None;status='FAIL_OTHER';error=None
class Memory(ctypes.Structure):_fields_=[('total',ctypes.c_ulonglong),('free',ctypes.c_ulonglong),('used',ctypes.c_ulonglong)]
class Util(ctypes.Structure):_fields_=[('gpu',ctypes.c_uint),('memory',ctypes.c_uint)]
def watch():
 while not stop.wait(.1):
  m=Memory();u=Util();a=guard.lib.nvmlDeviceGetMemoryInfo(guard.handle,ctypes.byref(m));b=guard.lib.nvmlDeviceGetUtilizationRates(guard.handle,ctypes.byref(u));records.append({'monotonic':time.perf_counter(),'used_bytes':m.used if a==0 else None,'gpu_utilization':u.gpu if b==0 else None})
thread=threading.Thread(target=watch,daemon=True);thread.start();result={}
try:
 import torch,pyarrow.parquet as pq,io,ast,collections,math
 import numpy as np
 from PIL import Image
 from transformers import AutoModel,AutoTokenizer
 from colpali_engine.models import ColQwen2,ColQwen2Processor
 from aaber.common.text import tokenize
 from mdrouter_v5.graded_metrics import stable_ranking
 torch.set_num_threads(1);torch.manual_seed(C.SEED);torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
 models=C.load('manifests/hr_models_verified.json','FROZEN_MODEL_LOADER');cfg=C.load('configs/hr_pilot_sparse_004.json','FROZEN_PARAMETERS');source=C.load('scripts/cross_domain_four_plan_001.py','EXACT_FROZEN_LOADER')
 nodes=[x for x in ast.parse(source).body if isinstance(x,ast.FunctionDef) and x.name=='load_visual'];assert len(nodes)==1
 env={'MODELS':models,'CFG':cfg,'torch':torch,'ColQwen2':ColQwen2,'ColQwen2Processor':ColQwen2Processor}
 exec(compile(ast.Module(nodes,type_ignores=[]),'original_frozen_loader','exec'),env)
 torch.cuda.reset_peak_memory_stats();t=time.perf_counter();model,processor=env['load_visual']();torch.cuda.synchronize();loadwall=time.perf_counter()-t
 assert processor.image_processor.size['longest_edge']==768*28*28
 rows=pq.read_table(C.STORAGE/'assets/corpus/test-00000-of-00001.parquet',columns=['corpus-id','image']).to_pylist();rows=sorted(rows,key=lambda r:int(r['corpus-id']))[:8];out=C.STORAGE/('smoke_'+sys.argv[1].replace('/','_'));out.mkdir(exist_ok=False);emb=[]
 def block():
  with torch.inference_mode():
   for i in range(0,len(rows),2):
    guard.check();rr=rows[i:i+2];images=[Image.open(io.BytesIO(x['image']['bytes'])).convert('RGB') for x in rr];x=processor.process_images(images).to('cuda:0');v=model(**x);valid=x['attention_mask'].bool();emb.extend([e[m].detach().to(torch.float16).cpu() for e,m in zip(v,valid)])
  return len(emb)
 _,activity=profile_call(block,C.A/'page_index_trace.json')
 with torch.inference_mode():
  q=model(**processor.process_queries(['What is the structure of a biological cell?']).to('cuda:0'))[0].float();ours=[];official=[]
  for e in emb:
   e=e.float().cuda();ours.append((q@e.T).max(1).values.sum().item());official.append(processor.score_multi_vector([q],[e],device='cuda:0')[0,0].item())
 assert max(abs(a-b) for a,b in zip(ours,official))<1e-3,'SCORER_PARITY_FAIL'
 torch.save({'ids':[int(r['corpus-id']) for r in rows],'embeddings':emb},out/'visual_smoke.pt');guard.check();torch.cuda.synchronize()
 result={'model_load_wall_s':loadwall,'pages':8,'sample_rule':'first8numericpageIDs, noqualityselection','peak_torch_allocated_bytes':torch.cuda.max_memory_allocated(),'peak_torch_reserved_bytes':torch.cuda.max_memory_reserved(),'GPU_activity_index':activity,'scorer_max_absdiff':max(abs(a-b) for a,b in zip(ours,official)),'image_pixel_budget':'UNCHANGED_768*28*28','index_batch':2,'labels_or_method_quality_read':0}
 C.SOUT.append(out/'visual_smoke.pt');status='PASS_GUARDED_GPU_SMOKE_NO_OOM'
except Exception as ex:
 error=str(ex);status='CUDA_OOM' if 'out of memory' in error.lower() else 'RESOURCE_BLOCKED_CONTAMINATION' if 'foreign' in error.lower() or 'occupied' in error.lower() else 'CUDA_ERROR_OTHER'
finally:
 try:guard.close()
 except Exception as ex:status='RESOURCE_BLOCKED_CONTAMINATION';error=(error or '')+' guardclose:'+str(ex)
 stop.set();thread.join()
 if model is not None:del model,processor
 try:
  import torch
  torch.cuda.empty_cache()
 except Exception:pass
C.write(C.R/'gpu_smoke_result.json',{'status':status,'physical_GPU':gpu,'UUID':chosen['uuid'],'result':result,'device_samples':records,'NVML_peak_device_used_bytes':max((x['used_bytes'] or 0 for x in records),default=None),'error':error,'CUDA_OOM':status=='CUDA_OOM','full_main_experiment':'NOT_STARTED_BY_SMOKE_SCRIPT','scope':'Only ownjob; guardabortsonexternalprocess; no guaranteed scheduler reservation'})
C.finish(sys.argv[1].replace('/','_'),status,json.dumps(result)+(';error='+error if error else ''),'仅真正PASS且E0冻结登记后允许完整Economics；OOM/资源污染/其它CUDA错误均停止，不调模型/批量/分辨率追求通过。')
