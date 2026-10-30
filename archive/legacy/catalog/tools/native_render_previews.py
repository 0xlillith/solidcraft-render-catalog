"""Actual low-budget native renders; each receipt names the representation exercised.
This is a visual integration sample, not photorealistic convergence or source-spec acceptance.
"""
from core import *
from mcp_client import Client
import time,traceback

def complete(c,params,path):
    started=c.execute('render.start',params);job=started['job'];deadline=time.monotonic()+90
    while True:
        state=c.execute('render.status',{'job':job});phase=state.get('progress',{}).get('phase')
        if phase=='completed':break
        if phase in ('failed','cancelled'):raise RuntimeError(state)
        if time.monotonic()>deadline:
            c.execute('render.cancel',{'job':job});raise TimeoutError(str(state))
        time.sleep(.08)
    exported=c.execute('render.export',{'job':job,'path':str(path),'overwrite':True});assert path.is_file()
    return {'job':job,'start':started,'completed':state,'export':exported,'sha256':sha(path)}


def main():
    records=[];errors=[];start=time.time();items=load(ROOT/'materials/index.json')['items'];probe='--probe' in sys.argv
    if probe:items=[x for x in items if x['id'] in ['MAT-001','MAT-071','MAT-112']]
    with Client(gpu=True) as c:
        backends=c.execute('render.backends');dump(ROOT/'reports/native-render-backends.json',backends);print('NATIVE_GPU_READY',flush=True)
        for i,item in enumerate(items):
            f=ROOT/item['path'];r=load(f/'material.json')
            try:
                if r['transmission'] and (f/'optical-study.solidcraft').exists():
                    c.execute('doc.open',{'path':str(f/'optical-study.solidcraft')})
                    c.execute('render.settings.capture_hdr',{'name':'Uniform material preview','set':{'width':320,'height':256,'job':{'method':'gpu_path','options':{'samples':64,'denoise':True,'max_depth':12,'tone_map':'aces_fitted','lighting':{'environment':[0,0,0],'area_lights':[]}}}},'path':str(ROOT/'source/assets/render/starter/environments/exports/white-enveloping-studio.hdr'),'rotation_rad':float(np.pi),'intensity':0.1,'assume_linear_srgb':False})
                    params={'setup':'Uniform material preview'};variant='native smooth 8 mm closed-slab optical study; no rough/spectral/transmission-map equivalence'
                else:
                    c.execute('doc.open',{'path':str(f/'material.solidcraft')});request=load(f/'native-runtime-texture-request.json');request.update(samples=64,max_depth=8,tone_map='aces_fitted',denoise=True)
                    request['settings']={'width':320,'height':256,'background':[30,35,43],'camera':{'target':[0,0,0],'yaw':-.7,'pitch':.85,'roll':0,'distance':150,'fov':.65,'up':'z'}}
                    request['environment']={'kind':'hdr','path':str(ROOT/'source/assets/render/starter/environments/exports/white-enveloping-studio.hdr'),'rotation_rad':float(np.pi),'intensity':0.1,'assume_linear_srgb':False}
                    request['lighting']={'environment':[0,0,0],'area_lights':[]};params=request;variant='native GPU planar color/normal/roughness/metallic coupon; no displacement or unsupported material extensions'
                receipt=complete(c,params,f/'native-render.png');receipt.update(id=r['id'],variant=variant,width=320,height=256,samples=64,denoised=True,convergence_claim=False);dump(f/'native-render-receipt.json',receipt);records.append({'id':r['id'],'variant':variant,'png_sha256':receipt['sha256']})
            except Exception as e:errors.append({'id':r['id'],'error':str(e),'trace':traceback.format_exc()});print('NATIVE_RENDER_ERROR',r['id'],str(e)[:600],flush=True)
            if (i+1)%20==0 or probe:dump(ROOT/'reports/native-render-progress.json',{'completed':len(records),'errors':errors,'total':len(items)});print('NATIVE_RENDERS',len(records),'errors',len(errors),flush=True)
            # Stop a systematic unsupported request rather than running hundreds of identical failures.
            if len(errors)>=3 and not records:break
    dump(ROOT/'reports'/('native-render-probe.json' if probe else 'native-material-renders.json'),{'status':'PASS' if not errors and len(records)==len(items) else 'FAIL','count':len(records),'expected':len(items),'results':records,'errors':errors,'seconds':time.time()-start})
if __name__=='__main__':main()
