from core import *
import subprocess,concurrent.futures,time
CLI=load(ROOT/'build.json')['native_cli']
def one(row):
    f=ROOT/row['path'];out=f/'native-model-preview.png';t=time.time()
    p=subprocess.run([CLI,'snapshot',str(f/'environment.solidcraft'),'--out',str(out),'--width','800','--height','500','--no-grid','--no-axes','--view','iso'],capture_output=True,text=True,encoding='utf-8',timeout=60)
    if p.returncode:raise RuntimeError((p.stdout+p.stderr)[-2000:])
    reply=json.loads(p.stdout);assert out.exists()
    receipt={'id':row['id'],'renderer':reply.get('renderer'),'sha256':sha(out),'seconds':time.time()-t,'scope':'Actual native modelling/product viewport snapshot. Not the saved HDR/path-traced lighting result.'};dump(f/'native-model-preview.json',receipt);return receipt
if __name__=='__main__':
    results=[];errors=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        jobs={pool.submit(one,r):r for r in load(ROOT/'environments/index.json')['items']}
        for f in concurrent.futures.as_completed(jobs):
            try:results.append(f.result())
            except Exception as e:errors.append({'id':jobs[f]['id'],'error':str(e)})
            if (len(results)+len(errors))%40==0:print('NATIVE_ENV_PREVIEWS',len(results),'errors',len(errors),flush=True)
    dump(ROOT/'reports/native-environment-previews.json',{'status':'PASS' if not errors else 'FAIL','count':len(results),'expected':280,'results':results,'errors':errors})
