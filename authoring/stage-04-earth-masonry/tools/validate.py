"""Independent consistency/asset gate, not a claim of native renderer acceptance."""
import hashlib, json, pathlib, os, math, sys
import cv2, numpy as np
from PIL import Image
import trimesh
R=pathlib.Path(__file__).resolve().parents[1]
def digest(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for block in iter(lambda:f.read(1048576),b''):h.update(block)
 return h.hexdigest()
def check():
 p=json.loads((R/'data/physical-profiles.json').read_text())['profiles'];v=json.loads((R/'data/material-variants.json').read_text())['items'];r=json.loads((R/'data/process-recipes.json').read_text())['processes']
 assert len(p)==28 and len(v)==168 and len(r)==30
 physical={x['id'] for x in p};recipes={x['id'] for x in r};ids=set()
 for x in v:
  assert x['id'] not in ids;ids.add(x['id']);assert x['physical_profile_id'] in physical;assert x['mapset_id'] in recipes
 for x in p:
  assert x['physical_properties']
  for item in x['physical_properties']:
   a=item['value'];assert a is None or (isinstance(a,list) and 0<a[0]<a[1]) or (isinstance(a,(int,float)) and math.isfinite(a) and a>0)
   assert item['source_url'].startswith('https://') and item['unit']
 maps=[];files=[]
 os.environ['OPENCV_IO_ENABLE_OPENEXR']='1'
 for row in r:
  fam,fin=row['id'].split('.',1)
  base=R/'build/maps'/fam/fin
  for size in (2048,1024):
   d=base/(('master-' if size==2048 else 'runtime-')+str(size))
   assert d.is_dir(),d
   for name in ['base_color','normal_opengl','normal_directx','roughness','metallic','orm','height_mm_u16']:
    image=d/(name+'.png');assert image.is_file(),image
    with Image.open(image) as i:
     i.verify()
    with Image.open(image) as i:
     assert i.size==(size,size)
     assert (i.mode in ('I;16','I') if name=='height_mm_u16' else i.mode in ('L','RGB'))
    maps.append(image)
   h=cv2.imread(str(d/'height_mm.exr'),cv2.IMREAD_UNCHANGED)
   assert h is not None and h.shape==(size,size) and h.dtype==np.float32 and np.isfinite(h).all() and np.max(np.abs(h))<=8
   im=np.asarray(Image.open(d/'height_mm_u16.png'),dtype=np.float32)
   assert np.max(np.abs((im/65535*16-8)-h))<.0008
   o=np.asarray(Image.open(d/'orm.png'));a=np.asarray(Image.open(d/'roughness.png'))
   assert (o[:,:,0]==255).all() and np.array_equal(o[:,:,1],a) and (o[:,:,2]==0).all()
   n=np.asarray(Image.open(d/'normal_opengl.png'));dx=np.asarray(Image.open(d/'normal_directx.png'))
   assert np.array_equal(n[:,:,0],dx[:,:,0]) and np.array_equal(n[:,:,2],dx[:,:,2]);assert np.all(n[:,:,1].astype(int)+dx[:,:,1].astype(int)==255)
   files.append(d/'height_mm.exr')
 for x in v:
  d=R/'build/materials'/x['id'];assert d.is_dir()
  for name in ['material.gltf','material.glb','gltf_buffer.bin','preview.png','resource.json']:
   assert (d/name).exists(),d/name
  s=trimesh.load(d/'material.glb',force='scene');assert len(s.geometry)>=2
  a=json.loads((d/'resource.json').read_text());assert a['physical_profile_id']==x['physical_profile_id']
  files.extend([d/'material.glb',d/'material.gltf',d/'preview.png'])
 json_files=[*R.glob('data/*.json'),*R.glob('registry/*.json')]
 receipt={'status':'PASS','physical_profiles':len(p),'appearance_variants':len(v),'shared_mapsets':len(r),'map_pngs':len(maps),'height_exrs':len(files)-3*len(v),'portable_glb_gltf':len(v)*2,'previews':len(v),'native_acceptance':'not_run','premium_qualification':'pending','plugin_standard':None,'releases_verification':'pending','sample_hashes':{str(z.relative_to(R)):digest(z) for z in (maps[:2]+files[:2])}}
 (R/'reports').mkdir(exist_ok=True);(R/'reports/validation.json').write_text(json.dumps(receipt,indent=2)+'\n')
 print(json.dumps(receipt,indent=2))
if __name__=='__main__':check()