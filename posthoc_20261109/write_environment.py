from pathlib import Path
import argparse,json,os,platform,sys
from datetime import datetime
from zoneinfo import ZoneInfo
import numpy,scipy,matplotlib
ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
v=dict(time_beijing=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),python=sys.version,
    kernel=platform.release(),system=platform.system(),machine=platform.machine(),logical_cpus=os.cpu_count(),
    numpy=numpy.__version__,scipy=scipy.__version__,matplotlib=matplotlib.__version__,
    selected_thread_limits={k:os.getenv(k) for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','OMP_THREAD_LIMIT']},
    CUDA_initialized=False,GPU_jobs=0,notes='CPU replay environment; fresh OCR runtime recorded separately')
with a.out.open('x',encoding='utf8') as f:json.dump(v,f,indent=2);f.write('\n')
print(json.dumps(v,indent=2))
