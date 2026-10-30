"""Original metric textures and portable coupons; source facts never drive invented physics."""
from __future__ import annotations
import os
os.environ.setdefault('OPENCV_IO_ENABLE_OPENEXR','1')
import argparse, copy, hashlib, html, json, math, struct, sys, time
from pathlib import Path
import numpy as np
from PIL import Image, PngImagePlugin
import cv2
from inputs import ROOT, dump, records, recipes, variants, main as make_data
BUILD=ROOT/'build'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dec(a):
    a=np.asarray(a);return np.where(a<=.04045,a/12.92,((a+.055)/1.055)**2.4)
def enc(a):
    a=np.maximum(0,np.asarray(a));return np.where(a<=.0031308,12.92*a,1.055*a**(1/2.4)-.055)
def unit(a):return a/np.maximum(np.linalg.norm(a,axis=-1,keepdims=True),1e-15)
def noise(x,y,seed=17):
    i=np.floor(x).astype(np.int64);j=np.floor(y).astype(np.int64);u=x-i;v=y-j;u=u*u*(3-2*u);v=v*v*(3-2*v)
    def h(a,b):
        z=(a*374761393+b*668265263+seed*1442695041)&0xffffffff;z=((z^(z>>13))*1274126177)&0xffffffff;return ((z^(z>>16))&0xffffffff)/4294967295
    return ((1-v)*((1-u)*h(i,j)+u*h(i+1,j))+v*((1-u)*h(i,j+1)+u*h(i+1,j+1))).astype(np.float32)
def fields(r,n):
    if type(n)!=int or n<32 or n>2048 or n&(n-1):raise ValueError('Power-of-two dimensions 32..2048 required')
    if r not in recipes():raise ValueError('Unknown or modified source recipe')
    sx,sy=r['patch_mm'];x=(np.arange(n,dtype=np.float32)[None,:]+.5)*sx/n;y=(n-np.arange(n,dtype=np.float32)[:,None]-.5)*sy/n
    p=r['pattern'];fam=r['family'];l=r['layer_mm'] or .1
    grain=noise(x*7,y*7)-.5;fine=noise(x*39,y*39,23)-.5;macro=noise(x*.6,y*.6,31)-.5
    rough=np.broadcast_to(.62+.1*grain,(n,n)).copy();tone=.96+.035*grain+.025*macro
    if fam=='fff':
        ridge=.5+.5*np.cos(2*np.pi*y/l);z=.20*l*(ridge**.7-.5)+.0006*fine;rough=.33+.04*grain
        if p=='seam':z=z+.030*np.exp(-((x-sx*.57)/.10)**2)*(.7+.3*ridge)
        elif p=='fuzzy':z=.7*z+.045*(noise(x*4,y*4,49)-.5);rough=.65+.10*grain
        elif p in ('top-roads','ironed'):
            z=.018*np.cos(2*np.pi*x/.45)+.0007*fine
            if p=='ironed':z=z*.15;rough=.24+.04*grain
        elif p=='bed-texture':z=.018*grain+.001*fine;rough=.63+.1*grain
        elif p=='sanded':z=.08*z+.002*(noise(x*.8,y*17,62)-.5);rough=.50+.05*grain
        elif p=='polished':z=.0003*grain;rough=.13+.02*grain
        elif p!='wall':raise ValueError(p)
    elif fam=='vat':
        z=.032*l*np.cos(2*np.pi*y/l)+.00025*fine;rough=.30+.035*grain
        if p=='angled-stairs':z=.10*l*(2*((x+y*.8)/l%1)-1)+.0003*fine
        elif p=='support-marks':
            z=.001*grain
            for cx,cy in [(1.1,1.5),(3.5,4.6),(5.2,2.7)]:z=z+.035*np.exp(-((x-cx)**2+(y-cy)**2)/.026)
            rough=.39+.04*grain
        elif p=='sanded':z=.0018*(noise(x*.8,y*22,52)-.5);rough=.43+.04*grain
        elif p=='polished':z=.00015*grain;rough=.08+.015*grain
        elif p=='matte':z=.0025*grain;rough=.64+.05*grain
        elif p!='wall':raise ValueError(p)
    elif fam=='powder-polymer':
        granular=(noise(x*19,y*19,63)-.5);z=.022*granular+.008*grain+.001*fine;rough=.78+.12*grain
        if p=='bead-blasted':z=.011*grain+.0015*fine;rough=.66+.09*grain
        elif p=='tumbled':z=.006*grain+.0007*fine;rough=.49+.06*grain
        elif p=='smoothed':z=.0006*grain;rough=.19+.035*grain
        elif p!='as-built':raise ValueError(p)
    else:
        granular=noise(x*24,y*24,71)-.5;z=.016*granular+.006*grain;rough=.70+.10*grain
        if p=='upskin':z=z+.06*l*np.sin(2*np.pi*y/.12);rough=.57+.10*grain
        elif p=='vertical':z=z+.08*l*np.cos(2*np.pi*y/l)
        elif p=='downskin':z=.033*granular+.013*grain+.12*l*np.cos(2*np.pi*y/l);rough=.83+.07*grain
        elif p=='shot-peened':z=.007*grain+.001*fine;rough=.51+.08*grain
        elif p=='machined':z=.002*np.cos(2*np.pi*(np.hypot(x+3,y-3)/.17))+.0003*fine;rough=.25+.035*grain
        elif p=='polished':z=.0001*fine;rough=.065+.008*grain
        elif p=='sintered-roads':z=.013*np.cos(2*np.pi*y/.2)+.004*grain+.0008*fine;rough=.62+.08*grain
        else:raise ValueError(p)
    z,t,rough=np.broadcast_arrays(z,tone,rough)
    return {'height':z.astype(np.float32),'tone':np.clip(t,.7,1).astype(np.float32),'rough':np.clip(rough,.045,.95).astype(np.float32),'patch_mm':r['patch_mm'],'metallic':int(fam=='metal-am')}
def smaller(f):return {k:(a.reshape(a.shape[0]//2,2,a.shape[1]//2,2).mean((1,3),dtype=np.float32) if isinstance(a,np.ndarray) else a) for k,a in f.items()}
def normals(z,patch):
    dy,dx=np.gradient(z,patch[1]/z.shape[0],patch[0]/z.shape[1]);return unit(np.stack([-dx,dy,np.ones_like(z)],-1))
def png(p,a,srgb=False):
    p.parent.mkdir(parents=True,exist_ok=True);info=PngImagePlugin.PngInfo()
    if srgb:info.add(b'sRGB',b'\0')
    Image.fromarray(a).save(p,pnginfo=info,compress_level=5)
    return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'width':a.shape[1],'height':a.shape[0],'channels':a.shape[2] if a.ndim==3 else 1,'bits':a.dtype.itemsize*8,'encoding':'sRGB' if srgb else 'linear'}
def maps(f,folder):
    z=f['height'];n=z.shape[0]
    if not np.isfinite(z).all() or abs(z).max()>=.25:raise ValueError('height overflow')
    gl=np.rint((normals(z,f['patch_mm'])*.5+.5)*255).astype(np.uint8);dx=gl.copy();dx[:,:,1]=255-gl[:,:,1]
    r=np.rint(f['rough']*255).astype(np.uint8);m=np.full((n,n),255*f['metallic'],np.uint8);base=np.repeat(np.rint(enc(f['tone'])*255).astype(np.uint8)[:,:,None],3,2)
    result={}
    for key,a in [('base_color_modulation',base),('normal_opengl',gl),('normal_directx',dx),('roughness',r),('metallic',m),('orm',np.stack([np.full_like(r,255),r,m],-1)),('height_mm_u16',np.rint((z/.5+.5)*65535).astype(np.uint16))]:result[key]=png(folder/(key+'.png'),a,key=='base_color_modulation')
    exr=folder/'height_mm.exr'
    if not cv2.imwrite(str(exr),z,[cv2.IMWRITE_EXR_TYPE,cv2.IMWRITE_EXR_TYPE_FLOAT]):raise RuntimeError('EXR encode')
    result['height_mm_exr']={'path':exr.relative_to(ROOT).as_posix(),'sha256':sha(exr),'width':n,'height':n,'bits':32,'encoding':'linear millimetres'}
    return result

def geometry(patch,closed=False):
    s=patch[0]/1000;pos=[];norm=[];uv=[];tan=[];idx=[]
    if closed:
        dims=np.array([s,.002,s]);faces=[([0,1,0],[1,0,0]),([0,-1,0],[-1,0,0]),([1,0,0],[0,0,-1]),([-1,0,0],[0,0,1]),([0,0,1],[1,0,0]),([0,0,-1],[-1,0,0])]
        for nn,tt in faces:
            N=np.array(nn);T=np.array(tt);B=np.cross(N,T);center=N*dims/2;base=len(pos)
            for u,v in [(0,0),(1,0),(0,1),(1,1)]:
                pos.append((center+T*np.dot(abs(T),dims)*(u-.5)+B*np.dot(abs(B),dims)*(v-.5)).tolist());norm.append(nn);uv.append([u,v]);tan.append(tt+[1])
            idx.extend([base,base+1,base+2,base+1,base+3,base+2])
    else:
        for curved in (False,True):
            base=len(pos);cols=64 if curved else 1
            for v in (0,1):
                for j in range(cols+1):
                    u=j/cols;a=(u-.5)*math.pi/2;R=s/(math.pi/2)
                    pos.append([s*.8+R*math.sin(a),R*(math.cos(a)-1),(.5-v)*s] if curved else [-s*.8+(u-.5)*s,0,(.5-v)*s]);norm.append([math.sin(a),math.cos(a),0] if curved else [0,1,0]);tan.append([math.cos(a),-math.sin(a),0,1] if curved else [1,0,0,1]);uv.append([u,v])
            for j in range(cols):a=base+j;b=a+cols+1;idx.extend([a,a+1,b,a+1,b+1,b])
    return pos,norm,uv,tan,idx

def portable(profile,r,folder,mapfolder,optical=False):
    pos,norm,uv,tan,idx=geometry(r['patch_mm'],optical);chunks=[];views=[];access=[];offset=0
    for arr,dtype,size,typ,target in [(pos,'<f4',3,'VEC3',34962),(norm,'<f4',3,'VEC3',34962),(uv,'<f4',2,'VEC2',34962),(tan,'<f4',4,'VEC4',34962),(idx,'<u4',1,'SCALAR',34963)]:
        a=np.asarray(arr,dtype=dtype);raw=a.tobytes();views.append({'buffer':0,'byteOffset':offset,'byteLength':len(raw),'target':target});offset+=len(raw);chunks.append(raw);acc={'bufferView':len(views)-1,'componentType':5126 if dtype=='<f4' else 5125,'count':a.size//size,'type':typ}
        if not access:acc.update(min=a.min(0).tolist(),max=a.max(0).tolist())
        access.append(acc)
    folder.mkdir(parents=True,exist_ok=True);stem='transmission-study' if optical else 'material';binary=b''.join(chunks);(folder/(stem+'.bin')).write_bytes(binary)
    color=dec(np.array(profile['appearance_palette_srgb'])/255).tolist();metal=int(profile['family']=='metal-am');names=['base_color_modulation','orm','normal_directx']
    mat={'name':profile['name']+' / '+r['id'],'doubleSided':not optical,'pbrMetallicRoughness':{'baseColorFactor':color+[1],'baseColorTexture':{'index':0},'roughnessFactor':1,'metallicFactor':metal,'metallicRoughnessTexture':{'index':1}},'normalTexture':{'index':2},'extras':{'physical_profile_id':profile['id'],'condition':profile['condition'],'patch_mm':r['patch_mm'],'optics':'authored unmeasured RGB; no spectral or native acceptance','normal_convention':'Source +V is image-up; this explicit increasing-v mesh uses the green-flipped map','mass_assignment':False}}
    doc={'asset':{'version':'2.0','generator':'Original additive extension stage03b/1'},'scene':0,'scenes':[{'nodes':[0]}],'nodes':[{'mesh':0}],'meshes':[{'primitives':[{'attributes':{'POSITION':0,'NORMAL':1,'TEXCOORD_0':2,'TANGENT':3},'indices':4,'material':0}]}],'materials':[mat],'textures':[{'source':i,'sampler':0} for i in range(3)],'images':[{'uri':os.path.relpath(mapfolder/(k+'.png'),folder).replace(os.sep,'/')} for k in names],'samplers':[{'magFilter':9729,'minFilter':9729,'wrapS':33071,'wrapT':33071}],'buffers':[{'uri':stem+'.bin','byteLength':len(binary)}],'bufferViews':views,'accessors':access}
    if optical:
        mat['pbrMetallicRoughness']['baseColorFactor']=[.98,.98,.98,1];mat['extensions']={'KHR_materials_transmission':{'transmissionFactor':.85},'KHR_materials_ior':{'ior':1.5},'KHR_materials_volume':{'thicknessFactor':.002,'attenuationDistance':.02,'attenuationColor':color}};doc['extensionsUsed']=list(mat['extensions']);mat['extras']['optics']='Closed 2 mm slab with explicitly authored transmission 0.85, IOR 1.5 and 20 mm attenuation reference; not measured resin optics or scattering.'
    dump(folder/(stem+'.gltf'),doc);emb=copy.deepcopy(doc);emb['buffers'][0].pop('uri');bb=bytearray(binary)
    for i,k in enumerate(names):
        raw=(mapfolder/(k+'.png')).read_bytes();bb.extend(b'\0'*((-len(bb))%4));start=len(bb);bb.extend(raw);emb['bufferViews'].append({'buffer':0,'byteOffset':start,'byteLength':len(raw)});emb['images'][i]={'bufferView':len(emb['bufferViews'])-1,'mimeType':'image/png'}
    emb['buffers'][0]['byteLength']=len(bb);bb.extend(b'\0'*((-len(bb))%4));jj=json.dumps(emb,separators=(',',':'),allow_nan=False).encode();jj+=b' '*((-len(jj))%4)
    (folder/(stem+'.glb')).write_bytes(struct.pack('<III',0x46546c67,2,28+len(jj)+len(bb))+struct.pack('<II',len(jj),0x4e4f534a)+jj+struct.pack('<II',len(bb),0x004e4942)+bb)

def sample(a,u,v):
    h,w=a.shape[:2];x=np.clip(u*w-.5,0,w-1);y=np.clip(v*h-.5,0,h-1);ix=np.floor(x).astype(int);iy=np.floor(y).astype(int);jx=np.minimum(ix+1,w-1);jy=np.minimum(iy+1,h-1);fx=x-ix;fy=y-iy
    if a.ndim==3:fx=fx[...,None];fy=fy[...,None]
    return (1-fy)*((1-fx)*a[iy,ix]+fx*a[iy,jx])+fy*((1-fx)*a[jy,ix]+fx*a[jy,jx])
def preview(p,r,folder,mapfolder):
    # Exact runtime bytes; 2x pixel sampling and linear-domain averaging.
    S=2;w,h=480,320;yy,xx=np.mgrid[:h*S,:w*S];x=(xx+.5)/S;y=(yy+.5)/S
    u=np.clip((x-22)/230,0,1);v=np.clip((y-25)/270,0,1);flat=(x>=22)&(x<252)&(y>=25)&(y<295)
    curved=(x>=290)&(x<459)&(y>=25)&(y<295);angle=((x-290)/169-.5)*1.15;N=np.zeros((*x.shape,3));N[:,:,2]=1;N[curved]=np.stack([np.sin(angle),np.zeros_like(angle),np.cos(angle)],-1)[curved];u[curved]=(x[curved]-290)/169;mask=flat|curved
    paths={k:mapfolder/(k+'.png') for k in ['base_color_modulation','normal_opengl','roughness']}
    tone=sample(dec(np.asarray(Image.open(paths['base_color_modulation']),dtype=float)/255),u,v)
    local=unit(sample(np.asarray(Image.open(paths['normal_opengl']),dtype=float)/127.5-1,u,v));rough=sample(np.asarray(Image.open(paths['roughness']),dtype=float)/255,u,v)
    T=unit(np.stack([N[:,:,2],np.zeros_like(x),-N[:,:,0]],-1));B=np.cross(N,T);N=unit(T*local[:,:,:1]+B*local[:,:,1:2]+N*local[:,:,2:3])
    base=dec(np.array(p['appearance_palette_srgb'])/255)*tone;metal=int(p['family']=='metal-am');f0=base if metal else np.full_like(base,.04);nv=np.maximum(.001,N[:,:,2]);a2=np.maximum(.00002,rough**4);rgb=base*(.10 if not metal else .13)
    for direction,power in [([-.6,.65,1],2.1),([.75,-.1,1],.8),([-.45,-.7,.6],.5)]:
        L=unit(np.array(direction));H=unit(L+np.array([0,0,1]));nl=np.maximum(0,np.sum(N*L,-1));nh=np.maximum(0,np.sum(N*H,-1));D=a2/(np.pi*(nh*nh*(a2-1)+1)**2);G=2*nv/(nv+np.sqrt(a2+(1-a2)*nv*nv))*2*nl/(nl+np.sqrt(a2+(1-a2)*nl*nl));F=f0+(1-f0)*(1-H[2])**5
        rgb+=power*((1-metal)*base*.96/np.pi*nl[:,:,None]+F*(D*G/(4*nv))[:,:,None])
    rgb[~mask]=[.017,.023,.032];rgb=rgb.reshape(h,S,w,S,3).mean((1,3));arr=np.rint(np.clip(enc(rgb/(1+rgb)),0,1)*255).astype(np.uint8)
    rec=png(folder/'preview.png',arr,True);dump(folder/'preview-receipt.json',{'output_sha256':rec['sha256'],'runtime_inputs':{k:sha(v) for k,v in paths.items()},'supersampling':2,'averaging':'linear before tone mapping/sRGB','renderer':'original opaque software coupon shader; transmission-study is a separate portable asset; not native evidence'})

def gallery(vs,ps):
    items=[];pp={p['id']:p for p in ps}
    for v in vs:
        p=pp[v['physical_profile_id']];items.append({**v,'brand':p['brand'],'process':p['manufacturing_process'],'condition':p['condition'],'properties':len(p['properties']),'path':'build/materials/'+v['id'],'transmission_study':p['translucent_intent']})
    data=json.dumps(items).replace('</','<\\/');text='''<!doctype html><meta charset="utf-8"><title>Additive material collection</title><style>body{margin:0;background:#111923;color:#dce7ef;font:16px system-ui}header,main{padding:28px}h1{margin:8px 0}input,select{padding:12px;margin:8px;background:#24303d;color:inherit;border:1px solid #607182}#grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));gap:18px}article{background:#202c38;padding:14px;border-radius:12px}img{width:100%}a{color:#83cddd}small{color:#b7c9d4}button{padding:8px}</style><header><h1>Additive manufacturing — category completion</h1><p>Source-linked material references and original metric appearances. Not certified printer settings, engineering allowables or native acceptance.</p><input id="q" placeholder="Search grade, brand, process or finish"><select id="family"><option value="">All families</option><option>fff</option><option>vat</option><option>powder-polymer</option><option>metal-am</option></select><p id="count"></p><a href="data/physical-summary.csv">Physical data CSV</a> · <a href="data/source-audit.json">Source exclusions</a> · <a href="README.md">Guide</a></header><main id="grid"></main><script>const rows=DATA;const q=document.querySelector('#q'),f=document.querySelector('#family'),g=document.querySelector('#grid');function show(){g.replaceChildren();let rs=rows.filter(r=>(!f.value||r.family===f.value)&&JSON.stringify(r).toLowerCase().includes(q.value.toLowerCase()));document.querySelector('#count').textContent=rs.length+' appearances';for(const r of rs){let a=document.createElement('article'),im=document.createElement('img');im.src=r.path+'/preview.png';im.loading='lazy';a.append(im);let t=document.createElement('h3');t.textContent=r.name;a.append(t);let s=document.createElement('small');s.textContent=r.brand+' · '+r.process+' · '+r.properties+' source property records';a.append(s);for(const [file,label] of [['material.glb','GLB'],['material.gltf','glTF'],['physical.json','Physical data'],['appearance.json','Recipe']]){let b=document.createElement('p'),l=document.createElement('a');l.href=r.path+'/'+file;l.textContent=label;b.append(l);a.append(b)}if(r.transmission_study){let b=document.createElement('p'),l=document.createElement('a');l.href=r.path+'/transmission-study.glb';l.textContent='Closed transmission study (authored optics)';b.append(l);a.append(b)}g.append(a)}}q.addEventListener('input',show);f.addEventListener('change',show);show()</script>'''.replace('DATA',data)
    (ROOT/'index.html').write_text(text,encoding='utf8')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--size',type=int,default=2048);ap.add_argument('--limit',type=int,default=0);a=ap.parse_args();make_data();ps=records();rs=recipes();vs=variants(ps,rs);rs=rs[:a.limit] if a.limit else rs;ids={r['id'] for r in rs};vs=[v for v in vs if v['recipe_id'] in ids];metas=[]
    for i,r in enumerate(rs):
        f=fields(r,a.size);folder=BUILD/'maps'/r['family']/r['id'];full=maps(f,folder/('master-'+str(a.size)));small=maps(smaller(f),folder/('runtime-'+str(a.size//2)));meta={'recipe':r,'master':full,'runtime':small,'height_encoding':{'min_mm':-.25,'max_mm':.25},'native_acceptance':'not_run'};dump(folder/'maps.json',meta);metas.append(meta);print('MAPSET',i+1,len(rs),r['id'],flush=True)
    lookup={p['id']:p for p in ps};rr={r['id']:r for r in rs}
    for i,v in enumerate(vs):
        p=lookup[v['physical_profile_id']];r=rr[v['recipe_id']];folder=BUILD/'materials'/v['id'];mp=BUILD/'maps'/r['family']/r['id']/('runtime-'+str(a.size//2));portable(p,r,folder,mp);dump(folder/'physical.json',p);dump(folder/'appearance.json',{'variant':v,'recipe':r,'metallic':int(p['family']=='metal-am'),'palette_srgb':p['appearance_palette_srgb'],'native_installation':False,'full_physics':False,'optical_study':p['translucent_intent']});preview(p,r,folder,mp)
        if p['translucent_intent']:portable(p,r,folder,mp,True)
        if (i+1)%20==0:print('MATERIAL',i+1,len(vs),flush=True)
    gallery(vs,ps);dump(ROOT/'reports/build.json',{'profiles':len(ps),'appearances':len(vs),'mapsets':len(rs),'master_resolution':a.size,'runtime_resolution':a.size//2,'complete':not a.limit and a.size==2048,'native_acceptance':'not_run','plugin_standard':None});print('BUILT',len(vs),flush=True)
if __name__=='__main__':main()
