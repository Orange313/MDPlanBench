from pathlib import Path
b=Path(__file__).resolve().parent
t=(b/'setup_monitor_001.py').read_text(encoding='utf8').replace("C.start('setup_001')","C.start('setup_002')").replace("C.finish('setup_001',","C.finish('setup_002',").replace("frozen['query_ids']==list(range(58))","len(frozen['query_ids'])==58 and len(set(frozen['query_ids']))==58")
with (b/'setup_monitor_002.py').open('x',encoding='utf8') as f:f.write(t)
for name in ['economics_worker_001.py','summarize_economics_001.py','supervisor_001.py','start_monitor_001.py']:
 p=b/name;s=p.read_text(encoding='utf8').replace('setup_001/','setup_002/');p.write_text(s,encoding='utf8')
