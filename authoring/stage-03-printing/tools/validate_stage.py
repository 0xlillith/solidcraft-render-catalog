"""Independent whole-delivery inspection. No native/premium approval is inferred."""
from __future__ import annotations
import os
os.environ.setdefault('OPENCV_IO_ENABLE_OPENEXR','1')
import argparse, hashlib, json, math, struct, zlib
from pathlib import Path
import numpy as np
from PIL import Image
import cv2
from data import ROOT, dump, records

def require(condition, message):
    if not condition: raise ValueError(message)
def load(path):
    def unique(pairs):
        obj={}
        for k,v in pairs:
            if k in obj:raise ValueError('duplicate JSON key '+k)
            obj[k]=v
        return obj
    return json.loads(path.read_text(encoding='utf-8'),object_pairs_hook=unique,parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)))
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def png_chunks(path):
    raw=path.read_bytes();require(raw[:8]==b'\x89PNG\r\n\x1a\n','PNG signature');p=8;out=[]
    while p<len(raw):
        require(p+12<=len(raw),'PNG truncated chunk');n=struct.unpack('>I',raw[p:p+4])[0];kind=raw[p+4:p+8];value=raw[p+8:p+8+n]
        require(p+12+n<=len(raw),'PNG length');require(zlib.crc32(kind+value)&0xffffffff==struct.unpack('>I',raw[p+8+n:p+12+n])[0],'PNG CRC')
        out.append((kind,value));p+=12+n
    require(out[0][0]==b'IHDR' and out[-1][0]==b'IEND','PNG required chunks');return out

def validate(require_gltf=True):
    profiles,recipes,variants=records();generation=load(ROOT/'build/generation.json')
    require((generation['master_size'],generation['runtime_size'],generation['map_sets'],generation['appearances'])==(2048,1024,73,280),'Incomplete or reduced-resolution generation')
    for name,key,expected in [('physical-profiles','profiles',profiles),('process-recipes','items',recipes),('material-variants','items',variants)]:
        require(load(ROOT/'data'/f'{name}.json')[key]==expected,'Generated source records disagree: '+name)
    require(sum(len(p['properties']) for p in profiles)==194,'physical record count')
    for p in profiles:
        require(p['source']['table_visually_verified'] and not p['source']['redistributed_document'],'source review declaration')
        require(p['effective_printed_density_kg_m3'] is None and p['full_mechanical_model'] is None,'unsupported engineering claim')
        for x in p['properties']:
            require(x['source_id']==p['source']['id'],'source link')
            require(math.isclose(x['value'],x['source_value']*x['conversion']['scale']+x['conversion']['offset'],rel_tol=1e-12,abs_tol=1e-7),'SI conversion')
    png_count=0;exr_count=0;map_folders={}
    for r in recipes:
        directory=ROOT/'build/maps'/r['group']/r['id'];contract=load(directory/'map-contract.json');require(contract['recipe']==r,'recipe identity')
        map_folders[r['id']]=directory;last_z=None
        for label,n in [('master',2048),('runtime',1024)]:
            images={}
            for role,rec in contract['exports'][label].items():
                f=(ROOT/rec['path']).resolve();require(f.is_relative_to(directory.resolve()),'unsafe map path')
                require(f.is_file() and f.stat().st_size==rec['bytes'] and digest(f)==rec['sha256'],'map digest '+str(f))
                require((rec['width'],rec['height'])==(n,n),'declared dimensions')
                if role=='height_mm_exr':continue
                chunks=png_chunks(f);ihdr=chunks[0][1];w,h,depth,color=struct.unpack('>IIBB',ihdr[:10]);require((w,h)==(n,n),'PNG actual size')
                require(depth==(16 if role=='height_mm_u16' else 8),'actual PNG bit depth')
                require(color==(0 if role in ('roughness','metallic','height_mm_u16') else 2),'actual PNG channel type')
                require(any(k==b'sRGB' for k,v in chunks)==(role=='base_color_modulation'),'color-space declaration')
                with Image.open(f) as im:im.load();images[role]=np.array(im)
                png_count+=1
            exr=ROOT/contract['exports'][label]['height_mm_exr']['path'];z=cv2.imread(str(exr),cv2.IMREAD_UNCHANGED)
            require(z is not None and z.dtype==np.float32 and z.shape==(n,n) and np.isfinite(z).all(),'EXR actual float data');require(float(np.max(np.abs(z)))<=.25,'height bounds')
            exr_count+=1
            decoded=images['height_mm_u16'].astype(float)/65535*.5-.25
            require(float(np.max(np.abs(decoded-z)))<=.5/65535,'height16 vs floatEXR')
            if last_z is not None:np.testing.assert_allclose(z,last_z.reshape(1024,2,1024,2).mean((1,3),dtype=np.float32),atol=1e-7,rtol=0)
            last_z=z
            N=images['normal_opengl'].astype(np.int16);D=images['normal_directx'].astype(np.int16)
            require(np.all(N[:,:,1]+D[:,:,1]==255) and np.array_equal(N[:,:,0],D[:,:,0]) and np.array_equal(N[:,:,2],D[:,:,2]),'normal conventions')
            norm=N/127.5-1;require(float(np.max(np.abs(np.linalg.norm(norm,axis=-1)-1)))<.008,'normal normalization')
            dy,dx=np.gradient(z,12.8/n,12.8/n);expected=np.stack([-dx,dy,np.ones_like(z)],-1);expected/=np.linalg.norm(expected,axis=-1,keepdims=True)
            require(float(np.max(np.abs(expected-norm)))<=1/255+2e-6,'physical height normal derivative')
            orm=images['orm'];require(np.all(orm[:,:,0]==255) and np.all(orm[:,:,2]==0) and np.array_equal(orm[:,:,1],images['roughness']),'ORM roles');require(np.all(images['metallic']==0),'non-metal')
            require(images['roughness'].min()>=11 and images['roughness'].max()<=243,'roughness bounds')
        print('VALIDATED_MAPS',r['id'],flush=True)
    require((png_count,exr_count)==(1022,146),'map count')
    byid={p['id']:p for p in profiles};preview_count=0
    for v in variants:
        d=ROOT/'build/materials'/v['id'];m=load(d/'material.json');require(m['id']==v['id'] and m['profile_id']==v['profile_id'],'material identity')
        require(load(d/'physical.json')==byid[v['profile_id']],'physical reference mismatch');require((d/m['map_contract']).resolve()==(map_folders[v['process_id']]/'map-contract.json').resolve(),'map contract link')
        require(m['native_acceptance']=='not_run' and m['premium_qualification']=='not_qualified','false acceptance')
        png_chunks(d/'preview.png')
        with Image.open(d/'preview.png') as im:im.load();require(im.size==(640,380) and im.mode=='RGB','preview dimensions')
        preview_count+=1
        gltf=load(d/'material.gltf');require(gltf['materials'][0]['extras']['physical_profile_id']==v['profile_id'],'glTF physical link')
        for value in gltf['images']+gltf['buffers']:
            path=(d/value['uri']).resolve();require(path.is_relative_to((ROOT/'build').resolve()) and path.is_file(),'missing or unsafe portable resource')
        b=(d/'material.glb').read_bytes();require(struct.unpack('<III',b[:12])==(0x46546c67,2,len(b)),'GLB header');require(len(b)%4==0,'GLB alignment')
        proposal=load(d/'native-appearance-proposal.json');require(proposal['status']=='not_executed' and proposal['effective_printed_density'] is None,'native proposal boundary')
    counts={ext:len(list((ROOT/'build/materials').rglob('*.'+ext))) for ext in ('gltf','glb','bin')}
    require(all(v==280 for v in counts.values()),'portable file counts')
    idx=load(ROOT/'registry/resource-index.json');require(len(idx['items'])==280 and len(idx['physical_profiles'])==11 and idx['map_sets']==73,'index coverage')
    require(len({i['id'] for i in idx['items']})==280,'index duplicate')
    official=load(ROOT/'reports/gltf-validation.json') if require_gltf else {'status':'NOT_RUN'}
    if require_gltf:require(official['files']==560 and official['errors']==0 and official['warnings']==0,'official glTF validation')
    result={'status':'PASS' if require_gltf else 'STRUCTURAL_PASS_ONLY','physical_profiles':11,'physical_property_records':194,'appearance_variants':280,'map_sets':73,'map_pngs':png_count,'height_exrs':exr_count,'previews':preview_count,'portable_files':counts,'official_gltf_validation':official,'native_acceptance':'not_run','premium_qualification':'not_qualified','plugin_contract':None,'scope':'Independent archive-ready byte/PNG/color/map/physical-data validation. No printer process, mechanical equivalence or native-render acceptance.'}
    dump(ROOT/'reports/validation.json',result);return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--without-official-gltf',action='store_true');a=p.parse_args()
    try:out=validate(not a.without_official_gltf);print('VALIDATION',out['status'],out['appearance_variants'])
    except Exception as e:dump(ROOT/'reports/validation.json',{'status':'FAIL','error':str(e)});raise
