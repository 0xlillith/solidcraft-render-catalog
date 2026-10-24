"""Actual low-sample GPU images of the generated lighting/setups, not just diagrams."""
from core import *
from mcp_client import Client
from native_render_previews import complete
import zipfile,time,traceback
if __name__=='__main__':
    items=[]
    collections=[('materials','material.solidcraft','selene-index.json')] if '--selene-only' in sys.argv else [('lighting','rig.solidcraft','index.json'),('setups','setup.solidcraft','index.json')]
    for category,filename,index in collections:
        for row in load(ROOT/category/index)['items']:
            f=ROOT/row['path'];native=f/filename
            if native.exists():items.append((row,f,native))
    results=[];errors=[];start=time.time()
    with Client(gpu=True) as c:
        for i,(row,f,native) in enumerate(items):
            try:
                with zipfile.ZipFile(native) as z:d=json.loads(z.read('document.json'))
                saved=d['render']['setups'];name=next((n for n in saved if n.endswith('Authoring Preview')),next(iter(saved)))
                job=copy.deepcopy(saved[name]['job']);job['options'].update(samples=64,denoise=True,linear_exr=False)
                c.execute('doc.open',{'path':str(native)});c.execute('render.settings.set',{'name':name,'set':{'width':320,'height':256,'job':job}})
                receipt=complete(c,{'setup':name},f/'native-render.png');receipt.update(id=row['id'],scope='Actual GPU result of the named authored native variant; 64 samples, denoised, not convergence/physical certification.');dump(f/'native-render-receipt.json',receipt);results.append({'id':row['id'],'sha256':receipt['sha256']})
            except Exception as e:errors.append({'id':row['id'],'error':str(e),'trace':traceback.format_exc()});print('SETUP_PREVIEW_ERROR',row['id'],str(e)[:300],flush=True)
            if (i+1)%40==0:dump(ROOT/'reports/native-setup-render-progress.json',{'count':len(results),'expected':len(items),'errors':errors});print('NATIVE_SETUP_PREVIEWS',len(results),'errors',len(errors),flush=True)
    dump(ROOT/'reports'/('native-selene-renders.json' if '--selene-only' in sys.argv else 'native-setup-renders.json'),{'status':'PASS' if not errors else 'FAIL','count':len(results),'expected':len(items),'results':results,'errors':errors,'seconds':time.time()-start})
