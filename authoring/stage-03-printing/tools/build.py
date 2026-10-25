"""Original physically-scaled FFF surface studies; no printer/integration plugin.
Numpy fields -> height-derived normals -> portable samples and an offline gallery.
"""
from __future__ import annotations
import argparse, copy, csv, hashlib, html, json, math, os, struct, time
os.environ.setdefault('OPENCV_IO_ENABLE_OPENEXR','1')
from pathlib import Path
import numpy as np
from PIL import Image, PngImagePlugin, ImageDraw
import cv2
from data import ROOT, VERSION, dump, records
BUILD=ROOT/'build'
HEIGHT_RANGE=.5 # signed millimetres in [-.25,.25]
PATTERNS={'wall','aligned-seam','fuzzy-wall','monotonic-top','concentric-top','ironed-top','smooth-bed','textured-bed','support-contact','sanded-wall','smoothed-wall'}

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
def dec(a):
    a=np.asarray(a);return np.where(a<=.04045,a/12.92,((a+.055)/1.055)**2.4)
def enc(a):
    a=np.maximum(0,np.asarray(a));return np.where(a<=.0031308,a*12.92,1.055*np.power(a,1/2.4)-.055)
def unit(a):
    return a/np.maximum(1e-15,np.linalg.norm(a,axis=-1,keepdims=True))
def validate_recipe(r,n):
    if type(n)!=int or not 32<=n<=2048 or n&(n-1):raise ValueError('power of two size 32..2048 required')
    if r['pattern'] not in PATTERNS or r['group'] not in ('smooth','fiber','wood'):raise ValueError('unknown recipe')
    for key,lo,hi in [('layer_height_mm',.04,.4),('nozzle_diameter_mm',.2,.8),('extrusion_width_mm',.2,1.0)]:
        v=r[key]
        if isinstance(v,bool) or not isinstance(v,(float,int)) or not math.isfinite(v) or not lo<=v<=hi:raise ValueError(key)
    if r['layer_height_mm']>r['nozzle_diameter_mm']*.8:raise ValueError('layer/nozzle envelope')
    if r['patch_mm']!=[12.8,12.8]:raise ValueError('fixed metric source patch')

def wave(x,y):
    # Fixed analytic multi-scale fields; no randomized machine-dependent noise.
    return (.45*np.sin(x*5.71+y*3.83)+.27*np.cos(x*15.37-y*13.19)+.18*np.sin(x*37.11+y*21.73)+.10*np.cos(x*83.17-y*59.31)).astype(np.float32)
def field_at(x,y,r):
    validate_recipe(r,32)
    h=r['layer_height_mm'];w=r['extrusion_width_mm'];p=r['pattern'];g=r['group']
    fine=wave(x*2.5,y*2.5);grain=wave(x*.45,y*.45)
    ridge=.5+.5*np.cos(2*np.pi*y/h)
    z=.22*h*(ridge**.65-.5)
    if p=='aligned-seam':z=z+.035*np.exp(-((x-7.4)/.09)**2)*(.65+.35*ridge)
    elif p=='fuzzy-wall':z=.65*z+.04*wave(x*.7,y*.7)
    elif p in ('monotonic-top','ironed-top'):
        z=.11*h*np.cos(2*np.pi*x/w)
        if p=='ironed-top':z=.18*z+.0015*np.sin(2*np.pi*y/.12)
    elif p=='concentric-top':
        radius=np.sqrt((x-6.4)**2+(y-6.4)**2+.0001);z=.11*h*np.cos(2*np.pi*radius/w)
    elif p=='smooth-bed':z=.001*fine
    elif p=='textured-bed':z=.018*wave(x*.6,y*.6)+.002*fine
    elif p=='support-contact':
        z=.12*h*np.cos(2*np.pi*x/(w*1.6))-.018*np.maximum(0,wave(x*.7,y*.7))**3+.002*fine
    elif p=='sanded-wall':z=.14*z+.0025*wave(x*.1,y*2)
    elif p=='smoothed-wall':z=.03*z+.0005*grain
    if g=='fiber':
        micro=.004*wave(x*3,y*.9);z=z+micro;tone=.95+.045*grain+.035*fine;rough=.69+.08*grain
    elif g=='wood':
        micro=.007*wave(x*1.1,y*2.3);z=z+micro;tone=.90+.09*grain+.05*fine;rough=.74+.08*grain
    else:
        z=z+.0007*fine;tone=.97+.018*grain+.012*fine;rough=.32+.035*grain
    if p=='ironed-top':rough=rough*.72
    if p=='sanded-wall':rough=rough*.7+.22
    if p=='smoothed-wall':rough=rough*.25+.06
    if p=='textured-bed':rough=rough*.7+.25
    return np.broadcast_arrays(z,np.clip(tone,.65,1),np.clip(rough,.045,.95))

def fields(r,n):
    validate_recipe(r,n)
    x=(np.arange(n,dtype=np.float32)[None,:]+.5)*12.8/n
    y=(n-np.arange(n,dtype=np.float32)[:,None]-.5)*12.8/n
    z,t,rough=field_at(x,y,r)
    return {'height':z.astype(np.float32),'tone':t.astype(np.float32),'rough':rough.astype(np.float32),'patch_mm':r['patch_mm']}
def smaller(f):
    return {k:(a.reshape(a.shape[0]//2,2,a.shape[1]//2,2).mean((1,3),dtype=np.float32) if isinstance(a,np.ndarray) else a) for k,a in f.items()}
def normals(z,patch):
    # PNG rows descend while physical +V goes up.
    dy,dx=np.gradient(z,patch[1]/z.shape[0],patch[0]/z.shape[1],edge_order=1)
    return unit(np.stack([-dx,dy,np.ones_like(z)],axis=-1))
def png(path,a,srgb=False):
    path.parent.mkdir(parents=True,exist_ok=True);info=PngImagePlugin.PngInfo()
    if srgb:info.add(b'sRGB',b'\0')
    Image.fromarray(a).save(path,pnginfo=info,compress_level=6)
    return {'path':path.relative_to(ROOT).as_posix(),'sha256':sha(path),'bytes':path.stat().st_size,'width':a.shape[1],'height':a.shape[0],'channels':a.shape[2] if a.ndim==3 else 1,'bit_depth':a.dtype.itemsize*8,'encoding':'srgb' if srgb else 'linear_data'}
def map_export(f,folder):
    z=f['height'];n=z.shape[0]
    if not np.isfinite(z).all() or np.max(np.abs(z))>.25:raise ValueError('height out of range')
    normal=np.rint((normals(z,f['patch_mm'])*.5+.5)*255).astype(np.uint8)
    dx=normal.copy();dx[:,:,1]=255-dx[:,:,1]
    base=np.repeat(np.rint(np.clip(enc(f['tone']),0,1)*255).astype(np.uint8)[:,:,None],3,axis=2)
    rough=np.rint(f['rough']*255).astype(np.uint8);metal=np.zeros((n,n),np.uint8)
    orm=np.stack([np.full_like(metal,255),rough,metal],-1)
    height=np.rint((z/.5+.5)*65535).astype(np.uint16)
    result={}
    for name,a in [('base_color_modulation',base),('normal_opengl',normal),('normal_directx',dx),('roughness',rough),('metallic',metal),('orm',orm),('height_mm_u16',height)]:result[name]=png(folder/(name+'.png'),a,name=='base_color_modulation')
    # Independent full-float millimetre height, not sRGB or normalized displacement.
    exr=folder/'height_mm.exr'
    if not cv2.imwrite(str(exr),z,[cv2.IMWRITE_EXR_TYPE,cv2.IMWRITE_EXR_TYPE_FLOAT]):raise RuntimeError('EXR encoder failure')
    result['height_mm_exr']={'path':exr.relative_to(ROOT).as_posix(),'sha256':sha(exr),'bytes':exr.stat().st_size,'width':n,'height':n,'channels':1,'bit_depth':32,'encoding':'linear_mm'}
    return result

def material_geometry():
    # Flat and curved 12.8 mm coupons. Arc length, not just bounding box, is 12.8 mm.
    pos=[];norm=[];uv=[];tangent=[];idx=[]
    for curved in (False,True):
        base=len(pos);cols=64 if curved else 1
        for row in (0,1):
            for j in range(cols+1):
                u=j/cols;angle=(u-.5)*math.pi/2;R=.0128/(math.pi/2)
                if curved:
                    pos.append([.010+R*math.sin(angle),R*(math.cos(angle)-1),(.5-row)*.0128]);norm.append([math.sin(angle),math.cos(angle),0]);tangent.append([math.cos(angle),-math.sin(angle),0,1])
                else:
                    pos.append([-.010+(u-.5)*.0128,0,(.5-row)*.0128]);norm.append([0,1,0]);tangent.append([1,0,0,1])
                uv.append([u,row])
        for j in range(cols):
            a=base+j;b=a+cols+1;idx.extend([a,a+1,b,a+1,b+1,b])
    return pos,norm,uv,tangent,idx

def gltf(profile,variant,mapdir,folder):
    pos,norm,uv,tangent,idx=material_geometry();chunks=[];views=[];access=[];offset=0
    for array,dtype,count,typ,target in [(pos,'<f4',3,'VEC3',34962),(norm,'<f4',3,'VEC3',34962),(uv,'<f4',2,'VEC2',34962),(tangent,'<f4',4,'VEC4',34962),(idx,'<u4',1,'SCALAR',34963)]:
        a=np.asarray(array,dtype=dtype);raw=a.tobytes();views.append({'buffer':0,'byteOffset':offset,'byteLength':len(raw),'target':target});offset+=len(raw);chunks.append(raw)
        record={'bufferView':len(views)-1,'componentType':5126 if dtype=='<f4' else 5125,'count':a.size//count,'type':typ}
        if len(access)==0:record.update(min=a.min(0).tolist(),max=a.max(0).tolist())
        access.append(record)
    binary=b''.join(chunks);folder.mkdir(parents=True,exist_ok=True);(folder/'sample.bin').write_bytes(binary)
    palette=dec(np.array(profile['appearance_palette_srgb'])/255).tolist()
    names=['base_color_modulation','orm','normal_directx'];uris=[os.path.relpath(mapdir/(n+'.png'),folder).replace(os.sep,'/') for n in names]
    doc={'asset':{'version':'2.0','generator':'Original FFF catalog stage03/'+VERSION},'scene':0,'scenes':[{'nodes':[0]}],'nodes':[{'mesh':0,'name':variant['name']}],'meshes':[{'primitives':[{'attributes':{'POSITION':0,'NORMAL':1,'TEXCOORD_0':2,'TANGENT':3},'indices':4,'material':0}]}],'materials':[{'name':variant['id'],'doubleSided':True,'pbrMetallicRoughness':{'baseColorFactor':palette+[1],'baseColorTexture':{'index':0},'metallicFactor':0,'roughnessFactor':1,'metallicRoughnessTexture':{'index':1}},'normalTexture':{'index':2},'extras':{'physical_profile_id':profile['id'],'finite_patch_mm':[12.8,12.8],'coordinate_note':'Y-up metres; UV v runs down. The green-flipped normal is intentional for increasing-v tangent basis.','optics':'opaque illustrative dielectric; no measured refractive index or transmission','geometry':'two open coupons, not an engineering solid; no bulk mass assignment'}}],'images':[{'uri':u} for u in uris],'textures':[{'source':i,'sampler':0} for i in range(3)],'samplers':[{'magFilter':9729,'minFilter':9729,'wrapS':33071,'wrapT':33071}],'buffers':[{'uri':'sample.bin','byteLength':len(binary)}],'bufferViews':views,'accessors':access}
    dump(folder/'material.gltf',doc)
    emb=copy.deepcopy(doc);emb['buffers'][0].pop('uri');bb=bytearray(binary)
    for i,name in enumerate(names):
        raw=(mapdir/(name+'.png')).read_bytes();bb.extend(b'\0'*((-len(bb))%4));start=len(bb);bb.extend(raw)
        emb['bufferViews'].append({'buffer':0,'byteOffset':start,'byteLength':len(raw)});emb['images'][i]={'bufferView':len(emb['bufferViews'])-1,'mimeType':'image/png'}
    emb['buffers'][0]['byteLength']=len(bb);bb.extend(b'\0'*((-len(bb))%4))
    jj=json.dumps(emb,separators=(',',':'),allow_nan=False).encode();jj+=b' '*((-len(jj))%4)
    raw=struct.pack('<III',0x46546c67,2,12+8+len(jj)+8+len(bb))+struct.pack('<II',len(jj),0x4e4f534a)+jj+struct.pack('<II',len(bb),0x004e4942)+bb
    (folder/'material.glb').write_bytes(raw)

def preview(profile,r,f,path):
    w,h=640,380; yy,xx=np.mgrid[:h,:w];rgb=np.zeros((h,w,3),np.float32)
    rgb[:]=[.016,.022,.032];mask=(xx>=30)&(xx<370)&(yy>=30)&(yy<350)
    u=np.clip((xx-30)/340,0,1);v=np.clip((yy-30)/320,0,1)
    # A curved coupon beside the planar patch, lit in the same fixed studio.
    arc=(xx>=405)&(xx<610)&(yy>=38)&(yy<342);angle=((xx-405)/205-.5)*1.1
    N=np.zeros((h,w,3),np.float32);N[:,:,2]=1
    N[arc]=np.stack([np.sin(angle),np.zeros_like(angle),np.cos(angle)],-1)[arc]
    u[arc]=np.clip((xx[arc]-405)/205,0,1);v[arc]=np.clip((yy[arc]-38)/304,0,1);mask|=arc
    n=f['height'].shape[0];ix=np.minimum(n-1,(u*n).astype(int));iy=np.minimum(n-1,(v*n).astype(int))
    base=dec(np.array(profile['appearance_palette_srgb'])/255)[None,None,:]*f['tone'][iy,ix,None]
    local=normals(f['height'],[12.8,12.8])[iy,ix]
    T=unit(np.stack([N[:,:,2],np.zeros_like(angle),-N[:,:,0]],-1));B=np.cross(N,T);N=unit(T*local[:,:,0,None]+B*local[:,:,1,None]+N*local[:,:,2,None])
    rough=f['rough'][iy,ix];a2=np.maximum(.001,rough**4);nv=np.maximum(.001,N[:,:,2])
    result=base*(.12+.05*np.maximum(N[:,:,1],0))[:,:,None]
    for direction,power in [([-.5,.55,1],2.1),([.7,-.1,1],.7),([-.7,-.7,.4],.3)]:
        L=unit(np.array(direction,float));H=unit(L+np.array([0,0,1]));nl=np.maximum(0,np.sum(N*L,axis=-1));nh=np.maximum(0,np.sum(N*H,axis=-1));vh=max(0,H[2]);D=a2/(np.pi*(nh*nh*(a2-1)+1)**2);G=2*nv/(nv+np.sqrt(a2+(1-a2)*nv*nv))*2*nl/(nl+np.sqrt(a2+(1-a2)*nl*nl));F=.04+.96*(1-vh)**5
        result+=power*((base*.96/np.pi)*nl[:,:,None]+(D*G*F/(4*nv))[:,:,None])
    rgb[mask]=result[mask];rgb=enc(rgb/(1+rgb));arr=np.rint(np.clip(rgb,0,1)*255).astype(np.uint8)
    png(path,arr,True)

def gallery(items):
    data=json.dumps(items,ensure_ascii=True).replace('<','\\u003c')
    page='''<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>FFF material authoring</title><style>body{margin:0;background:#10151e;color:#e7edf5;font:16px system-ui}header,main{padding:30px 4vw}header{background:#1b2633}h1{font-size:38px;margin:10px 0}p{max-width:1050px;line-height:1.6;color:#b6c7d7}input,select,button{background:#263545;color:#fff;border:1px solid #536679;border-radius:6px;padding:10px;margin:4px}#grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:18px}.card{background:#1b2633;padding:12px;border-radius:8px}.card img{width:100%;border-radius:5px} .card p{font-size:13px}a{color:#83cce5}dialog{background:#192330;color:#fff;max-width:1000px;border:1px solid #54708a}dialog::backdrop{background:#000b}pre{white-space:pre-wrap;max-height:55vh;overflow:auto}small{color:#9eb1c4}label{display:inline-block}</style><header><small>SOLIDCRAFT RESOURCE AUTHORING / STAGE 03</small><h1>Printed surfaces, with physical context</h1><p>11 named material references · 280 appearances · 73 metric map sets. Layer heights, seam, top roads and finishing are visual studies, not slicing profiles or predictions of printed strength. Native application and premium acceptance remain pending.</p><p><a href="README.md">Read scope and sources</a> · <a href="data/physical-profiles.json">Physical reference records</a> · <a href="registry/resource-index.json">Stage resource index</a></p></header><main><label>Find <input id="q" placeholder="PLA, fuzzy, 0.08..."></label><label>Material <select id="product"><option value="">All materials</option></select></label><label>Surface <select id="pattern"><option value="">All surfaces</option></select></label><p id="count"></p><section id="grid"></section><button id="more">Show more</button><dialog id="detail"><button id="close">Close</button><h2 id="title"></h2><div id="links"></div><pre id="record"></pre></dialog></main><script>const rows=DATA;let limit=48;const $=id=>document.getElementById(id);for(const [id,key]of [['product','product'],['pattern','pattern']])for(const v of [...new Set(rows.map(r=>r[key]))].sort()){const o=document.createElement('option');o.value=v;o.textContent=v;$(id).append(o)}function show(r){$('title').textContent=r.name;$('record').textContent=JSON.stringify(r,null,2);$('links').replaceChildren();for(const [name,path] of [['Material GLB',r.path+'/material.glb'],['Editable glTF',r.path+'/material.gltf'],['Physical data',r.path+'/physical.json'],['Recipe',r.path+'/material.json'],['Maps',r.map_contract]]){const a=document.createElement('a');a.href=path;a.textContent=name+' ';a.style.marginRight='16px';$('links').append(a)}$('detail').showModal()}function draw(){const q=$('q').value.toLowerCase(),p=$('product').value,t=$('pattern').value;const out=rows.filter(r=>(!p||r.product===p)&&(!t||r.pattern===t)&&JSON.stringify([r.name,r.id,r.layer_height_mm]).toLowerCase().includes(q));$('count').textContent=out.length+' matches / '+rows.length+' appearances';$('grid').replaceChildren();for(const r of out.slice(0,limit)){const box=document.createElement('article');box.className='card';const img=document.createElement('img');img.loading='lazy';img.src=r.path+'/preview.png';img.alt=r.name;const h=document.createElement('h3');h.textContent=r.product;const p=document.createElement('p');p.textContent=r.pattern+' · '+r.layer_height_mm+' mm layer · '+r.nozzle_diameter_mm+' mm nozzle study';const b=document.createElement('button');b.textContent='Files and physical context';b.onclick=()=>show(r);box.append(img,h,p,b);$('grid').append(box)}$('more').hidden=out.length<=limit}for(const id of ['q','product','pattern'])$(id).oninput=()=>{limit=48;draw()};$('more').onclick=()=>{limit+=48;draw()};$('close').onclick=()=>$('detail').close();draw();</script>'''.replace('DATA',data)
    (ROOT/'index.html').write_text(page,encoding='utf-8')

def build(n=2048,limit=None):
    profiles,recipes,variants=records();byid={p['id']:p for p in profiles};saved={};start=time.time()
    if limit:recipes=recipes[:limit];variants=[v for v in variants if v['process_id'] in {r['id'] for r in recipes}]
    for i,r in enumerate(recipes):
        f=fields(r,n);folder=BUILD/'maps'/r['group']/r['id'];exports={}
        exports['master']=map_export(f,folder/f'master-{n}')
        if n>=64:exports['runtime']=map_export(smaller(f),folder/f'runtime-{n//2}')
        contract={'id':r['id'],'recipe':r,'exports':exports,'height':{'unit':'mm','uint16_scale':.5,'uint16_offset':-.25,'exr':'signed float32 mm'},'normal_axes':'+U right; +V image-up; +N outward','normal_derivation':'finite differences of metric height; generated again after linear downsampling','native_acceptance':'not_run','optical_reflectance':'illustrative; not measured','ao':'ORM red=1; no baked lighting or invented cavity occlusion'}
        dump(folder/'map-contract.json',contract);saved[r['id']]=(r,fields(r,256),folder)
        print('MAPSET',i+1,'/',len(recipes),r['id'],flush=True)
    inventory=[]
    for i,v in enumerate(variants):
        p=byid[v['profile_id']];r,f,md=saved[v['process_id']];folder=BUILD/'materials'/v['id'];folder.mkdir(parents=True,exist_ok=True)
        dump(folder/'physical.json',p);dump(folder/'material.json',{**v,'process':r,'map_contract':os.path.relpath(md/'map-contract.json',folder).replace(os.sep,'/')})
        pnginfo=preview(p,r,f,folder/'preview.png')
        mapdir=md/(f'runtime-{n//2}' if n>=64 else f'master-{n}')
        gltf(p,v,mapdir,folder)
        dump(folder/'native-appearance-proposal.json',{'status':'not_executed','not_plugin_standard':True,'physical_reference':p['id'],'effective_printed_density':None,'requires_explicit_target':True,'uniform_appearance_only':{'color':p['appearance_palette_srgb'],'opacity':1,'pbr':{'metallic':0,'roughness':float(f['rough'].mean()),'dielectric_ior':1.5}},'note':'Not a valid installed library or a material mass model. API binding awaits community and native review.'})
        inventory.append({'id':v['id'],'name':v['name'],'kind':'material_appearance','product':p['name'],'profile_id':p['id'],'pattern':r['pattern'],'layer_height_mm':r['layer_height_mm'],'nozzle_diameter_mm':r['nozzle_diameter_mm'],'path':folder.relative_to(ROOT).as_posix(),'map_contract':(md/'map-contract.json').relative_to(ROOT).as_posix(),'native_acceptance':'not_run','premium_qualification':'not_qualified'})
        if (i+1)%40==0:print('MATERIAL',i+1,'/',len(variants),flush=True)
    dump(ROOT/'registry/resource-index.json',{'purpose':'authoring inventory only; no plugin contract','items':inventory,'physical_profiles':[{'id':p['id'],'name':p['name'],'path':'data/physical-profiles.json'} for p in profiles],'map_sets':len(saved)})
    dump(BUILD/'generation.json',{'status':'GENERATED','master_size':n,'runtime_size':n//2,'profiles':len(profiles),'properties':sum(len(p['properties']) for p in profiles),'map_sets':len(saved),'appearances':len(inventory),'seconds':time.time()-start,'validation':'separate gate'})
    gallery(inventory)
    with (ROOT/'registry/resource-index.csv').open('w',encoding='utf-8',newline='') as fh:
        writer=csv.DictWriter(fh,fieldnames=list(inventory[0]));writer.writeheader();writer.writerows(inventory)
    print('GENERATED',len(inventory),'appearances',flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--size',type=int,default=2048);p.add_argument('--limit',type=int);a=p.parse_args();build(a.size,a.limit)
