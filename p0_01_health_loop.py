import requests,time,statistics,json
from pathlib import Path
url='http://127.0.0.1:8001/api/health/db'
out=Path('/app/test_reports/p0_01_health_15m.json')
progress=Path('/app/test_reports/p0_01_health_15m.progress')
lat=[]
codes=[]
errors=0
status_reason_counts={}
start=time.time()
end=start+900
iteration=0
while time.time()<end:
    iteration+=1
    t0=time.perf_counter()
    code=None
    status='request_error'
    reason='request_error'
    try:
        r=requests.get(url,timeout=3)
        code=r.status_code
        codes.append(code)
        body=r.json()
        status=body.get('status') or 'unknown'
        reason=body.get('reason') or 'none'
    except Exception:
        errors+=1
    latency=(time.perf_counter()-t0)*1000
    lat.append(latency)
    key=f"{status}|{reason}"
    status_reason_counts[key]=status_reason_counts.get(key,0)+1
    if iteration % 30 == 0:
        progress.write_text(json.dumps({'iteration':iteration,'elapsed_sec':round(time.time()-start,1),'last_code':code,'last_latency_ms':round(latency,2)}))
    sleep_for=1-(time.perf_counter()-t0)
    if sleep_for>0:
        time.sleep(sleep_for)

lat_sorted=sorted(lat)
p95=lat_sorted[int(0.95*len(lat_sorted))-1] if lat_sorted else None
report={
  'started_at_epoch':start,
  'ended_at_epoch':time.time(),
  'duration_sec':round(time.time()-start,2),
  'total_requests':len(lat),
  'errors':errors,
  'http_code_counts':{str(c):codes.count(c) for c in sorted(set(codes))},
  'count_503':codes.count(503),
  'p95_ms':round(p95,2) if p95 is not None else None,
  'avg_ms':round(sum(lat)/len(lat),2) if lat else None,
  'max_ms':round(max(lat),2) if lat else None,
  'status_reason_counts':status_reason_counts,
}
out.write_text(json.dumps(report,ensure_ascii=False,indent=2))
progress.write_text(json.dumps({'done':True,'duration_sec':report['duration_sec'],'count_503':report['count_503'],'p95_ms':report['p95_ms']}))
