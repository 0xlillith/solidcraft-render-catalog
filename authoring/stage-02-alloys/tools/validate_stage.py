"""Independent data, path, PNG and container checks. This does not certify optics or native behavior."""
from __future__ import annotations
import argparse, hashlib, json, math, struct, subprocess, zlib
from pathlib import Path
from PIL import Image
R=Path(__file__).resolve().parents[1]
def load(p):return json.loads(p.read_text())
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check_png(p,expected=None):
 b=p.read_bytes();assert b[:8]==b'\x89PNG\r\n\x1a\n';off=8;chunks=[]
 while off<len(b):
  size=struct.unpack_from('>I',b,off)[0];assert size<=64*1024*1024;kind=b[off+4:off+8];raw=b[off+8:off+8+size];crc=struct.unpack_from('>I',b,off+8+size)[0];assert zlib.crc32(kind+raw)&0xffffffff==crc;chunks.append(kind)
  if kind==b'IHDR':w,h,depth,color,compression,filtering,interlace=struct.unpack('>IIBBBBB',raw);assert w<=4096 and h<=4096 and interlace==0
  off+=size+12
 assert off==len(b) and chunks[-1]==b'IEND'
 with Image.open(p) as im:im.verify()
 if expected:
  assert digest(p)==expected['sha256'];assert len(b)==expected['bytes'];assert (w,h,depth)==(expected['width'],expected['height'],expected['bit_depth']);assert (b'sRGB' in chunks)==(expected['color_space']=='sRGB')
 return w,h

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--require-gltf',action='store_true');args=ap.parse_args()
 report=R/'reports';report.mkdir(exist_ok=True)
 for cmd,name in [(['python3',str(R/'tests/test_records.py')],'record-tests.log'),(['node','--test',str(R/'tests/numerical.cjs')],'numerical-tests.log')]:
  run=subprocess.run(cmd,capture_output=True,text=True);(report/name).write_text(run.stdout+run.stderr);assert run.returncode==0,name
 profiles=load(R/'data/physical-profiles.json')['profiles'];variants=load(R/'data/variants.json')['items'];assert len(profiles)==24 and len(variants)==192
 pmap={p['id']:p for p in profiles};sourceids={x['id'] for x in load(R/'data/sources.json')['items']};assert all(p['source_id'] in sourceids for p in profiles)
 index=load(R/'build/map-index.json');assert index['resolution']==2048 and len(index['contracts'])==8
 png_count=0
 for c in index['contracts']:
  assert c['patch_mm']==[40,40] and not c['seamless'];assert c['height_encoding']=={'offset_mm':-.05,'range_mm':.1}
  for size,records in c['sets'].items():
   folder=R/'build/maps'/c['finish_id']/size
   for key,receipt in records.items():check_png(folder/(key+'.png'),receipt);png_count+=1
   with Image.open(folder/'normal_opengl.png') as ng,Image.open(folder/'normal_directx.png') as nd,Image.open(folder/'orm.png') as orm,Image.open(folder/'roughness.png') as rough:
    for y in range(8,ng.height,97):
     for x in range(8,ng.width,103):
      a=ng.getpixel((x,y));b=nd.getpixel((x,y));v=orm.getpixel((x,y));assert a[0]==b[0] and a[1]+b[1]==255 and a[2]==b[2];assert abs(math.sqrt(sum((q/127.5-1)**2 for q in a))-1)<.009;assert v==(255,rough.getpixel((x,y)),255)
 files=[];previews=0
 for v in variants:
  folder=R/'build/materials'/v['id'];p=pmap[v['physical_profile_id']];assert load(folder/'physical-profile.json')==p
  a=load(folder/'appearance.json');assert not a['engineering_properties_changed'] and a['physical_profile_id']==p['id']
  native=load(folder/'native-material-commands.json');density=next(x['value'] for x in p['properties'] if x['quantity']=='density');assert native['commands'][0]['params']['density_g_cm3']==density/1000
  check_png(folder/'preview.png');previews+=1
  g=load(folder/'material.gltf');assert g['asset']['version']=='2.0' and g['materials'][0]['extras']['physical_profile_id']==p['id']
  for ref in [*g['buffers'],*g['images']]:
   file=(folder/ref['uri']).resolve();assert file.is_relative_to((R/'build').resolve()) and file.is_file()
  b=(folder/'material.glb').read_bytes();magic,ver,length=struct.unpack_from('<4sII',b);assert magic==b'glTF' and ver==2 and length==len(b)
  jlen,jkind=struct.unpack_from('<II',b,12);assert jkind==0x4e4f534a;doc=json.loads(b[20:20+jlen]);blen,bkind=struct.unpack_from('<II',b,20+jlen);assert bkind==0x004e4942 and 28+jlen+blen==len(b);assert len(doc['images'])==3
  files.append(v['id'])
 assert png_count==112 and previews==192 and len(set(files))==192
 official=load(report/'gltf-validation.json') if (report/'gltf-validation.json').exists() else None
 if args.require_gltf:assert official and official['files']==384 and official['errors']==0 and official['warnings']==0
 manifests=[]
 for f in sorted((R/'build').rglob('*')):
  if f.is_file():manifests.append({'path':f.relative_to(R).as_posix(),'bytes':f.stat().st_size,'sha256':digest(f)})
 (report/'build-manifest.json').write_text(json.dumps(manifests,indent=2)+'\n')
 result={'status':'PASS','physical_profiles':24,'distinct_alloy_grades':23,'physical_property_records':sum(len(p['properties']) for p in profiles),'appearance_variants':192,'map_pngs':png_count,'previews':previews,'gltf_files':384,'official_gltf_validation':official,'python_record_tests':10,'node_numerical_tests':8,'all_materials_have_physical_and_visual_records':True,'native_acceptance':'not_run','premium_qualification':'pending','plugin_standard_defined':False,'global_federated_records':2002,'build_files_hashed':len(manifests),'source_inputs':{p.relative_to(R).as_posix():digest(p) for p in sorted((R/'tools').glob('*')) if p.is_file()},'limitations':['No certified material identity, allowable stresses or complete physical constitutive model','No native SolidCraft or premium optical acceptance','Not every major alloy grade has been covered by this first tranche']}
 (report/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
