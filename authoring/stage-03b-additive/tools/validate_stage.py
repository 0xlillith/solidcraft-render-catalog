"""Independent checks of the delivered bytes and links; never native acceptance."""
import json,hashlib,struct,zlib,subprocess,sys
from pathlib import Path
import numpy as np
from PIL import Image
import os
os.environ.setdefault('OPENCV_IO_ENABLE_OPENEXR','1')
import cv2
from inputs import ROOT,records,recipes,variants,dump

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pngcheck(p,n,srgb):
 b=p.read_bytes()
 if b[:8]!=b'\x89PNG\r\n\x1a\n':raise ValueError('PNG signature')
 off=8;chunks=[]
 while off<len(b):
  count=struct.unpack('>I',b[off:off+4])[0];typ=b[off+4:off+8];data=b[off+8:off+8+count];crc=struct.unpack('>I',b[off+8+count:off+12+count])[0]
  if zlib.crc32(typ+data)&0xffffffff!=crc:raise ValueError('PNG CRC')
  chunks.append(typ);off+=count+12
 if off!=len(b) or chunks[-1]!=b'IEND' or ((b'sRGB' in chunks)!=srgb):raise ValueError('PNG chunks/color space')
 with Image.open(p) as im:
  im.load()
  if im.size!=(n,n):raise ValueError('PNG dimension')
  return np.array(im)

def main():
 build=ROOT/'build';ps=records();rs=recipes();vs=variants(ps,rs);run=json.loads((ROOT/'reports/build.json').read_text())
 if not run['complete'] or run['master_resolution']!=2048 or run['appearances']!=198:raise ValueError('Partial production refused')
 official=json.loads((ROOT/'reports/gltf-validation.json').read_text())
 if official['files']!=476 or official['errors'] or official['warnings']:raise ValueError('Official portable validator did not pass')
 expected_names={v['id'] for v in vs}
 if {p.name for p in (build/'materials').iterdir() if p.is_dir()}!=expected_names:raise ValueError('Wrong material coverage')
 pngs=exrs=0
 for recipe in rs:
  folder=build/'maps'/recipe['family']/recipe['id'];meta=json.loads((folder/'maps.json').read_text());heights=[];tones=[]
  if meta['recipe']!=recipe:raise ValueError('Recipe changed')
  for label,n in [('master',2048),('runtime',1024)]:
   a={}
   for name,entry in meta[label].items():
    p=ROOT/entry['path']
    if digest(p)!=entry['sha256']:raise ValueError('Map digest mismatch')
    if name=='height_mm_exr':
     z=cv2.imread(str(p),cv2.IMREAD_UNCHANGED)
     if z is None or z.shape!=(n,n) or z.dtype!=np.float32 or not np.isfinite(z).all():raise ValueError('EXR contract')
     a[name]=z;exrs+=1
    else:a[name]=pngcheck(p,n,name=='base_color_modulation');pngs+=1
   z=a['height_mm_exr'];heights.append(z)
   if abs(z).max()>=.25 or abs(a['height_mm_u16'].astype(float)/65535*.5-.25-z).max()>.5/65535:raise ValueError('Height encoding')
   gl=a['normal_opengl'];dx=a['normal_directx'];normal=gl/127.5-1
   if abs(np.linalg.norm(normal,axis=-1)-1).max()>.008:raise ValueError('Normal not unit')
   gy,gx=np.gradient(z,recipe['patch_mm'][1]/n,recipe['patch_mm'][0]/n);expected=np.stack([-gx,gy,np.ones_like(z)],-1);expected/=np.linalg.norm(expected,axis=-1,keepdims=True)
   if abs(expected-normal).max()>1/255+1e-6:raise ValueError('Height/normal relationship')
   if not np.array_equal(dx[:,:,1],255-gl[:,:,1]) or not np.array_equal(dx[:,:,[0,2]],gl[:,:,[0,2]]):raise ValueError('Handedness')
   orm=a['orm'];metal=255 if recipe['family']=='metal-am' else 0
   if not (orm[:,:,0]==255).all() or not (orm[:,:,2]==metal).all() or not (a['metallic']==metal).all() or not np.array_equal(orm[:,:,1],a['roughness']):raise ValueError('ORM roles')
  if abs(heights[0].reshape(1024,2,1024,2).mean((1,3))-heights[1]).max()>1e-7:raise ValueError('Linear physical-height filtering')
 pp={p['id']:p for p in ps};rr={r['id']:r for r in rs};optical=0
 for v in vs:
  folder=build/'materials'/v['id'];p=pp[v['physical_profile_id']];r=rr[v['recipe_id']]
  if json.loads((folder/'physical.json').read_text())!=p:raise ValueError('Physical record drift')
  appearance=json.loads((folder/'appearance.json').read_text())
  if appearance['variant']!=v or appearance['recipe']!=r:raise ValueError('Appearance/recipe linkage')
  with Image.open(folder/'preview.png') as im:
   im.load()
   if im.size!=(480,320):raise ValueError('Preview size')
  receipt=json.loads((folder/'preview-receipt.json').read_text())
  if receipt['output_sha256']!=digest(folder/'preview.png') or receipt['supersampling']!=2:raise ValueError('Preview receipt')
  mp=build/'maps'/r['family']/r['id']/'runtime-1024'
  for name,h in receipt['runtime_inputs'].items():
   if digest(mp/(name+'.png'))!=h:raise ValueError('Stale preview input')
  doc=json.loads((folder/'material.gltf').read_text());mat=doc['materials'][0]
  if mat['extras']['physical_profile_id']!=p['id'] or mat['pbrMetallicRoughness']['metallicFactor']!=int(p['family']=='metal-am'):raise ValueError('Portable identity')
  if p['translucent_intent']:
   optical+=1;o=json.loads((folder/'transmission-study.gltf').read_text());m=o['materials'][0]
   if m['doubleSided'] or m['extensions']['KHR_materials_volume']['thicknessFactor']!=.002:raise ValueError('Closed optical study contract')
 if (pngs,exrs,optical)!=(700,100,40):raise ValueError('Incomplete assets')
 if json.loads((ROOT/'data/physical-profiles.json').read_text())['profiles']!=ps:raise ValueError('Source properties drift')
 report={'status':'PASS','physical_profiles':24,'physical_property_records':sum(len(p['properties']) for p in ps),'appearances':198,'mapsets':50,'map_pngs':pngs,'height_exrs':exrs,'previews':198,'opaque_glb_gltf_files':396,'closed_optical_glb_gltf_files':80,'official_gltf':{'files':official['files'],'errors':official['errors'],'warnings':official['warnings']},'native_acceptance':'not_run','premium_qualification':'pending','plugin_standard':None,'limits':'Source numerical facts and generated file integrity; not manufacturing or optical certification'}
 dump(ROOT/'reports/validation.json',report);print(json.dumps(report))
if __name__=='__main__':main()
