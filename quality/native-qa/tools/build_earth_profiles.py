"""Additive corrected previews and bounded coarse-aggregate material profiles."""
from __future__ import annotations
import os;os.environ.setdefault('OPENCV_IO_ENABLE_OPENEXR','1')
import argparse,hashlib,importlib.util,json,pathlib
import numpy as np,cv2
from PIL import Image
from build_native_profiles import save_maps
import clasts

def load(p):return json.loads(p.read_text(encoding='utf8'))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--repo',type=pathlib.Path,required=True);ap.add_argument('--runtime',type=pathlib.Path,required=True);ap.add_argument('--out',type=pathlib.Path,required=True);a=ap.parse_args()
 if a.out.exists() and any(a.out.iterdir()):raise SystemExit('Choose a new empty output directory; original resources must not be overwritten')
 a.out.mkdir(parents=True,exist_ok=True)
 src=a.repo/'authoring/stage-04-earth-masonry';sp=importlib.util.spec_from_file_location('earth_builder',src/'tools/build.py');earth=importlib.util.module_from_spec(sp);sp.loader.exec_module(earth)
 profiles={x['id']:x for x in load(src/'data/physical-profiles.json')['profiles']};variants=load(src/'data/material-variants.json')['items']
 previews=a.out/'software-previews';previews.mkdir(exist_ok=True)
 for row in variants:
  folder=a.runtime/'stage-04-earth-masonry/build/maps'/row['family']/row['finish']/'runtime-1024'
  height=cv2.imread(str(folder/'height_mm.exr'),cv2.IMREAD_UNCHANGED)
  with Image.open(folder/'base_color.png') as im:shade=np.asarray(im.convert('L'),np.float32)/255
  with Image.open(folder/'roughness.png') as im:rough=np.asarray(im,np.float32)/255
  earth.preview(previews/(row['id']+'.png'),height,shade,rough,profiles[row['physical_profile_id']]['appearance_palette_srgb'],earth.FAMILY_SCALE[row['family']])
 print('METRIC_PREVIEWS_REBUILT',len(variants),flush=True)
 map_records={}
 for recipe in clasts.RECIPES:
  mapdir=a.out/'maps'/recipe
  for n in (2048,1024):
   maps,height,coverage=clasts.encoded(recipe,n);folder=mapdir/('master-2048' if n==2048 else 'runtime-1024');receipt=save_maps(folder,maps)
   exr=folder/'height_mm.exr'
   if not cv2.imwrite(str(exr),height.astype(np.float32)):raise RuntimeError('EXR write failed')
   with exr.open('rb') as f:exr_sha=hashlib.file_digest(f,'sha256').hexdigest()
   receipt['height_mm_exr']={'path':exr.name,'sha256':exr_sha,'bytes':exr.stat().st_size,'units':'mm','dimensions':[n,n]}
   print('COARSE_MAPS',recipe,n,flush=True)
   if n==1024:map_records[recipe]={'path':folder.relative_to(a.out).as_posix(),'maps':receipt,'coverage_fraction':float((coverage>.5).mean())}
  (mapdir/'recipe.json').write_text(json.dumps({'recipe':clasts.RECIPES[recipe],'stones':clasts.layout(recipe),'measurement_basis':'original authored morphology, not a measured quarry or mix','seamless':False},indent=2),encoding='utf8')
 accepted={'earth.granite-gravel','earth.limestone-chips','earth.compacted-rock-base','earth.quikrete-concrete-1101','earth.poured-concrete-generic'}
 records=[]
 for row in variants:
  recipe=row['mapset_id']
  if recipe not in map_records or row['physical_profile_id'] not in accepted:continue
  profile=profiles[row['physical_profile_id']]
  records.append({'id':row['id'],'name':row['name'],'version':'coarse-morphology-r2','physical_profile_id':profile['id'],'patch_mm':clasts.RECIPES[recipe]['patch_mm'],'maps':map_records[recipe]['maps'],'path':map_records[recipe]['path'],'pbr':{'base_color_srgb':profile['appearance_palette_srgb'],'metallic':0,'roughness':1,'normal_strength':1,'dielectric_ior':1.5},'base_color_mode':'modulate','native_render_validation':'not_yet_run','premium_qualified':False,'auto_assign_physical_material':False,'physical_properties_unchanged':True,'not_applied_to_sand_or_cement_powder':True})
 (a.out/'index.json').write_text(json.dumps({'appearance_derivatives':records,'count':len(records),'mapsets':map_records,'corrected_software_previews':len(variants),'historical_source_assets_unchanged':True},indent=2),encoding='utf8')
 print('EARTH_R2_READY',len(records),'appearances',len(map_records),'mapsets',flush=True)
if __name__=='__main__':main()
