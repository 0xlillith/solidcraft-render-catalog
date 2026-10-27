"""Materialize all six wood finishes and native 1K profiles for eight scanned PBR assets.

This creates additive derivative assets. It never changes archived source maps,
source engineering records, or application limits. Not a plugin/importer standard.
"""
from __future__ import annotations
import argparse,concurrent.futures,hashlib,json,pathlib
import numpy as np
from PIL import Image
from channels import albedo,normals,roughness,orm,materialize

def read(p):return json.loads(p.read_text(encoding='utf8'))
def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pixels(p):
 with Image.open(p) as im:im.load();return np.asarray(im)
def save_maps(folder,maps):
 folder.mkdir(parents=True,exist_ok=True);receipt={}
 for role,array in maps.items():
  path=folder/(role+'.png');Image.fromarray(array).save(path,compress_level=4)
  receipt[role]={'path':path.name,'sha256':digest(path),'bytes':path.stat().st_size,'dimensions':list(array.shape[:2][::-1]),'color_space':'srgb' if role=='base_color' else 'linear_data'}
 return receipt

def wood_group(spec):
 repo,runtime,out,wood,cut,finishes=spec
 folder=runtime/'stage-01-woods/build/maps'/wood['id']/cut/'runtime-1024'
 base=pixels(folder/'base_color.png');normal=pixels(folder/'normal_opengl.png');rough=pixels(folder/'roughness.png')
 contract=read(folder.parent/'map-contract.json');sources={k:digest(folder/(k+'.png')) for k in ('base_color','normal_opengl','roughness')}
 rows=[]
 for finish in finishes:
  identity=f"wood.{wood['id']}.{cut}.{finish['id']}";dest=out/'wood-finishes'/identity
  maps,coat=materialize(base,normal,rough,finish)
  receipt=save_maps(dest,maps)
  row={'id':identity,'name':f"{wood['name']} / {cut} / {finish['name']}",'source_collection':'wood-stage01-20261025','source_mapset':wood['id']+'/'+cut,'source_file_sha256':sources,'physical_profile_id':wood['physical_profile_id'],'patch_mm':contract['patch_mm'],'native_profile_max_dimension':1024,'maps':receipt,'pbr':{'base_color_srgb':[255,255,255],'metallic':0,'roughness':1,'normal_strength':1,'dielectric_ior':1.5},'clearcoat':coat,'finish_baked':{'color_multiplier_linear':finish['color_multiplier_linear'],'roughness_factor':finish['roughness_factor'],'normal_scale':finish['normal_scale']},'apply_factors_again':False,'finite_patch_not_seamless':True,'native_runtime_textures_not_persistent':True,'auto_assign_physical_material':False,'native_render_validation':'not_yet_run','premium_qualified':False}
  (dest/'material.json').write_text(json.dumps(row,indent=2)+'\n',encoding='utf8');rows.append(row|{'path':dest.relative_to(out).as_posix()})
 print('WOOD_FINISHES',wood['id'],cut,len(rows),flush=True)
 return rows

def scan(row,runtime,out):
 slug=row['id'][5:];source=runtime/'scanned-pbr-r1/build/maps'/slug/'runtime-2048';dest=out/'scanned-native-1024'/slug
 base=albedo(pixels(source/'base_color.png'),size=1024);normal=normals(pixels(source/'normal_opengl.png'),size=1024);rough=roughness(pixels(source/'roughness.png'),size=1024)
 dx=normal.copy();dx[:,:,1]=255-dx[:,:,1]
 maps={'base_color':base,'normal_opengl':normal,'normal_directx':dx,'roughness':rough,'orm':orm(rough)}
 receipt=save_maps(dest,maps)
 data={'id':row['id'],'name':row['name'],'source_collection':'scanned-pbr-quality-r1-20261026','source_asset':row['provider_source'],'source_license':row['license'],'source_file_hash':row['source_hash'],'source_file_sha256':{key:digest(source/(key+'.png')) for key in ('base_color','normal_opengl','roughness')},'physical_profile_id':row['physical_profile_id'],'patch_mm':row['scan_extent_mm'],'source_runtime_resolution':2048,'native_profile_max_dimension':1024,'source_2k_4k_unchanged':True,'maps':receipt,'pbr':{'base_color_srgb':[255,255,255],'metallic':0,'roughness':1,'normal_strength':1,'dielectric_ior':1.5},'auto_assign_physical_material':False,'native_runtime_textures_not_persistent':True,'native_render_validation':'not_yet_run','premium_qualified':False}
 (dest/'material.json').write_text(json.dumps(data,indent=2)+'\n',encoding='utf8')
 print('SCAN_NATIVE_PROFILE',slug,flush=True)
 return data|{'path':dest.relative_to(out).as_posix()}

def main():
 p=argparse.ArgumentParser();p.add_argument('--repo',type=pathlib.Path,required=True);p.add_argument('--runtime',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);p.add_argument('--only',choices=['all','scans','wood'],default='all');args=p.parse_args()
 if args.out.exists() and any(args.out.iterdir()):raise SystemExit('Refusing to overwrite derivative output; choose a fresh directory')
 args.out.mkdir(parents=True,exist_ok=True);records=[]
 if args.only in ('all','scans'):
  rows=read(args.repo/'quality/scanned-pbr-r1/registry/resource-index.json')['records']
  for row in rows:records.append(scan(row,args.runtime,args.out))
 if args.only in ('all','wood'):
  woods=read(args.repo/'authoring/stage-01-woods/data/woods.json');finishes=read(args.repo/'authoring/stage-01-woods/data/finishes.json')['finishes']
  specs=[(args.repo,args.runtime,args.out,w,c,finishes) for w in woods['woods'] for c in woods['cuts']]
  with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
   for rows in pool.map(wood_group,specs):records.extend(rows)
 if len({r['id'] for r in records})!=len(records):raise RuntimeError('Duplicate derivative identity')
 payload={'purpose':'versioned native material QA derivatives, not a plugin schema','records':records,'count':len(records),'source_releases_unchanged':True,'physical_properties_unchanged':True,'native_validation_is_separate':True}
 (args.out/'index.json').write_text(json.dumps(payload,indent=2)+'\n',encoding='utf8')
 print('DERIVATIVE_PROFILE_COMPLETE',len(records),flush=True)
if __name__=='__main__':main()
