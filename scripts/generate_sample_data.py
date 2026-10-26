"""Generate clearly labelled synthetic data for offline notebook/dashboard exploration."""
import random
from datetime import datetime, timezone, timedelta
from pathlib import Path
import pandas as pd
random.seed(42)
def main():
    now=datetime.now(timezone.utc); rows=[]
    for eid,name,base in [(1,'Synthetic fast API',45),(2,'Synthetic delayed API',180),(3,'Synthetic variable API',90)]:
        for i in range(60):
            latency=max(1,random.gauss(base,base*.18))
            if i in (17,43): latency*=4
            success=random.random()>.08
            category=None if success else random.choice(['http_error','connection_error','read_timeout'])
            rows.append({'timestamp':(now-timedelta(minutes=(180-i*3))).isoformat(),'endpoint_id':eid,'endpoint_name':name,'response_time_ms':round(latency,2),'status_code':200 if success else (500 if category=='http_error' else None),'success':success,'failure_category':category,'synthetic':True})
    path=Path(__file__).resolve().parents[1]/'data'/'synthetic_sample_data.csv'; pd.DataFrame(rows).to_csv(path,index=False); print(f'Wrote {len(rows)} SYNTHETIC rows to {path}')
if __name__=='__main__': main()
