"""Filter actual runtime maps, not undersampled analytic fields, for catalog images.
Original software coupon shader; no SolidCraft/native/photometric acceptance.
"""
from __future__ import annotations
import argparse, hashlib, json, time
from pathlib import Path
import numpy as np
from PIL import Image
from data import ROOT, records, dump
from build import dec, enc, unit, png

def sample(image,u,v):
    h,w=image.shape[:2];x=np.clip(u*w-.5,0,w-1);y=np.clip(v*h-.5,0,h-1)
    x0=np.floor(x).astype(int);y0=np.floor(y).astype(int);x1=np.minimum(x0+1,w-1);y1=np.minimum(y0+1,h-1)
    a=x-x0;b=y-y0
    if image.ndim==3:a=a[:,:,None];b=b[:,:,None]
    return (1-b)*((1-a)*image[y0,x0]+a*image[y0,x1])+b*((1-a)*image[y1,x0]+a*image[y1,x1])

def shade(arrays):
    # 2x pixel integration before tone mapping and output transfer; all input maps are 1K.
    scale=2;w,h=640*scale,380*scale;yy,xx=np.mgrid[:h,:w];xx=(xx+.5)/scale;yy=(yy+.5)/scale
    mask=(xx>=30)&(xx<370)&(yy>=30)&(yy<350)
    u=np.clip((xx-30)/340,0,1);v=np.clip((yy-30)/320,0,1)
    arc=(xx>=405)&(xx<610)&(yy>=38)&(yy<342);angle=((xx-405)/205-.5)*1.1
    N=np.zeros((h,w,3),np.float32);N[:,:,2]=1
    N[arc]=np.stack([np.sin(angle),np.zeros_like(angle),np.cos(angle)],-1)[arc]
    u[arc]=np.clip((xx[arc]-405)/205,0,1);v[arc]=np.clip((yy[arc]-38)/304,0,1);mask|=arc
    normal=unit(sample(arrays['normal'],u,v))
    T=unit(np.stack([N[:,:,2],np.zeros_like(angle),-N[:,:,0]],-1));B=np.cross(N,T)
    N=unit(T*normal[:,:,0,None]+B*normal[:,:,1,None]+N*normal[:,:,2,None])
    color=sample(arrays['color'],u,v)
    rough=sample(arrays['rough'],u,v);a2=np.maximum(.001,rough**4);nv=np.maximum(.001,N[:,:,2])
    diffuse=color*(.12+.05*np.maximum(N[:,:,1],0))[:,:,None];specular=np.zeros((h,w),np.float32)
    for direction,power in [([-.5,.55,1],2.1),([.7,-.1,1],.7),([-.7,-.7,.4],.3)]:
        L=unit(np.array(direction,float));H=unit(L+np.array([0,0,1]));nl=np.maximum(0,np.sum(N*L,axis=-1));nh=np.maximum(0,np.sum(N*H,axis=-1));vh=max(0,H[2])
        D=a2/(np.pi*(nh*nh*(a2-1)+1)**2);G=2*nv/(nv+np.sqrt(a2+(1-a2)*nv*nv))*2*nl/(nl+np.sqrt(a2+(1-a2)*nl*nl));F=.04+.96*(1-vh)**5
        diffuse+=power*(color*.96/np.pi)*nl[:,:,None];specular+=power*D*G*F/(4*nv)
    diffuse[~mask]=0;specular[~mask]=0
    return diffuse.reshape(380,2,640,2,3).mean((1,3)),specular.reshape(380,2,640,2).mean((1,3)),mask.reshape(380,2,640,2).mean((1,3))

def finish(profile,transport):
    diffuse,specular,coverage=transport
    linear=diffuse*dec(np.array(profile['appearance_palette_srgb'])/255)[None,None,:]+specular[:,:,None]+(1-coverage)[:,:,None]*np.array([.016,.022,.032])
    return np.rint(np.clip(enc(linear/(1+linear)),0,1)*255).astype(np.uint8)

def render(profile,arrays):
    return finish(profile,shade(arrays))

def main(limit=None):
    profiles,recipes,variants=records();profiles={p['id']:p for p in profiles};byprocess={r['id']:r for r in recipes}
    selected=variants if limit is None else variants[:limit];selected=sorted(selected,key=lambda v:(v['process_id'],v['id']));outputs=[];start=time.time();arrays=None;current=None
    for i,v in enumerate(selected):
        r=byprocess[v['process_id']];folder=ROOT/'build/maps'/r['group']/r['id'];contract=json.loads((folder/'map-contract.json').read_text())
        if current!=r['id']:
            arrays={};sources={}
            for role,key in [('base_color_modulation','color'),('normal_opengl','normal'),('roughness','rough')]:
                rec=contract['exports']['runtime'][role];f=ROOT/rec['path'];raw=f.read_bytes()
                if hashlib.sha256(raw).hexdigest()!=rec['sha256']:raise ValueError('map changed before preview')
                with Image.open(f) as im:a=np.array(im).astype(np.float32)
                if a.shape[:2]!=(1024,1024):raise ValueError('Previews require actual 1K runtime maps')
                arrays[key]=dec(a/255) if key=='color' else a/127.5-1 if key=='normal' else a/255
                sources[role]=rec['sha256']
            current=r['id'];transport=shade(arrays)
        out=ROOT/'build/materials'/v['id']/'preview.png';receipt=png(out,finish(profiles[v['profile_id']],transport),True)
        with Image.open(out) as im:im.load()
        receipt.update(id=v['id'],input_map_sha256=sources,scope='Original software coupon shader using actual runtime textures; 2x linear pixel integration. Not a native SolidCraft render.',native_acceptance='not_run')
        dump(out.with_name('preview-receipt.json'),receipt);outputs.append({'id':v['id'],'sha256':receipt['sha256']})
        if (i+1)%40==0:print('FILTERED_PREVIEWS',i+1,len(selected),flush=True)
    report={'status':'PASS' if len(outputs)==280 else 'PARTIAL','count':len(outputs),'runtime_map_resolution':1024,'pixel_supersampling':2,'averaging_domain':'linear_before_tone_mapping_and_srgb','outputs':outputs,'seconds':time.time()-start,'native_acceptance':'not_run','premium_qualification':'not_qualified'}
    dump(ROOT/'reports/preview-validation.json',report);print('PREVIEWS',report['status'],len(outputs),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--limit',type=int);a=p.parse_args();main(a.limit)
