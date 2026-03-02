import requests,time,json
from pathlib import Path
url='http://127.0.0.1:8001/api/health/db'
out=Path('/app/test_reports/p0_01_health_24h_monitor.jsonl')
progress=Path('/app/test_reports/p0_01_health_24h.progress')
start=time.time()
end=start+86400
count=0
code_503=0
errors=0
while time.time()<end:
    count+=1
    ts=time.time()
    entry={'ts':ts}
    try:
        r=requests.get(url,timeout=3)
        body=r.json()
        entry.update({'code':r.status_code,'status':body.get('status'),'db_status':body.get('db_status'),'reason':body.get('reason'),'latency_ms':body.get('db_latency_ms'),'cached':body.get('db_probe_cached')})
        if r.status_code==503:
            code_503+=1
    except Exception as e:
        errors+=1
        entry.update({'code':None,'error':str(e)[:120]})
    with out.open('a') as f:
        f.write(json.dumps(entry,ensure_ascii=False)+'\n')
    if count % 60 == 0:
        progress.write_text(json.dumps({'elapsed_sec':round(time.time()-start,1),'samples':count,'count_503':code_503,'errors':errors}))
    time.sleep(10)

progress.write_text(json.dumps({'done':True,'elapsed_sec':round(time.time()-start,1),'samples':count,'count_503':code_503,'errors':errors}))
