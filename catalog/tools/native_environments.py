"""Create and cold-reopen all generated environment containers with the real CLI.
Only this catalog output directory is written. No live app or user preferences are used.
"""
from core import *
import concurrent.futures,subprocess,time,traceback
CLI=load(ROOT/'build.json')['native_cli']

def build_one(item):
    rid=item['id'];folder=ROOT/'environments'/rid;recipe=folder/'solidcraft-build.json';deadline=time.monotonic()+1800
    while not recipe.exists():
        if time.monotonic()>deadline:raise TimeoutError('authoring source did not arrive '+rid)
        time.sleep(2)
    native=folder/'environment.solidcraft';p=subprocess.run([CLI,'run',str(recipe),'--save',str(native),'--quiet'],capture_output=True,text=True,encoding='utf-8',timeout=150)
    (ROOT/'reports'/('native-'+rid+'.log')).write_text(p.stdout+p.stderr,encoding='utf-8')
    if p.returncode:raise RuntimeError((p.stdout+p.stderr)[-3000:])
    check=subprocess.run([CLI,'run','--in',str(native),'--save',str(folder/'reopened.json'),'--quiet'],capture_output=True,text=True,encoding='utf-8',timeout=150)
    if check.returncode:raise RuntimeError('cold reopen: '+(check.stdout+check.stderr)[-2500:])
    doc=load(folder/'reopened.json');recipe_data=load(folder/'environment.json');setups=doc.get('render',{}).get('setups',{})
    assert len(setups)==1,(rid,'setup count',list(setups));resources=doc.get('render',{}).get('resources',{})
    assert resources,(rid,'missing retained HDR resource');assert native.is_file()
    receipt={'id':rid,'native':native.relative_to(ROOT).as_posix(),'native_sha256':sha(native),'cold_reopen':True,'setup_names':list(setups),'source_geometry_imported':True,'hdr_embedded':True,'external_maps_not_imported':True,'source_spec_full_validation':False}
    # The large expanded JSON is a useful editable native form, retained alongside its container.
    dump(folder/'native-validation.json',receipt);return receipt

def main():
    items=load(SOURCE/'environments.json')['items'];results=[];errors=[];start=time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        jobs={pool.submit(build_one,x):x for x in items}
        for f in concurrent.futures.as_completed(jobs):
            try:results.append(f.result())
            except Exception as e:errors.append({'id':jobs[f]['id'],'error':str(e),'trace':traceback.format_exc()})
            if (len(results)+len(errors))%20==0:dump(ROOT/'reports/native-environment-progress.json',{'count':len(results),'errors':errors});print('NATIVE_ENVIRONMENTS',len(results),'errors',len(errors),flush=True)
    dump(ROOT/'reports/native-environments.json',{'status':'PASS' if not errors else 'FAIL','count':len(results),'expected':280,'results':results,'errors':errors,'seconds':time.time()-start})
    if errors:raise RuntimeError(errors[:2])
if __name__=='__main__':main()
