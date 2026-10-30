"""Rebuild one selected extra from its own editable definition, never a pack.

Examples:
  python tools/extras/improve.py --id wood.red-alder.plain-sawn.gloss-varnish --out NEW_DIRECTORY
  python tools/extras/improve.py --id scan.white_oak_veneer --out NEW_DIRECTORY
  python tools/extras/improve.py --id earth.quikrete-concrete-1101.exposed-stones --metric-preview --out NEW_DIRECTORY

Outputs are additive; existing destinations and changed original inputs refuse.
No networking, release publication, physical assignment or installed-app edits.
"""
from __future__ import annotations
import argparse,hashlib,json,sys,os
from pathlib import Path
# Configure the bounded, hash-verified height decoder before cv2 is first imported.
os.environ.setdefault('OPENCV_IO_ENABLE_OPENEXR','1')
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/library'))
from common import asset_directory, confined
sys.path.insert(0,str(Path(__file__).parent/'quality/tools'))

def load(path):return json.loads(path.read_text(encoding='utf-8'))
def digest(path):
 with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(path,data):path.write_bytes((json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8'))
def pixels(path,rgb=False):
 import numpy as np
 from PIL import Image
 with Image.open(path) as im:
  im.load();return np.asarray(im.convert('RGB') if rgb else im).copy()

def asset_folder(identity: str, root=ROOT):
 root=Path(root)
 if (root/'catalog/paths.json').is_file() or (root/'assets').is_dir():
  return asset_directory(identity,root)
 # Old fixtures may pass either the repository or its extras directory.
 original=root if (root/'INDEX.json').is_file() else root/'extras'
 index=load(original/'INDEX.json');items=index['items']
 if len(items)!=index['count']:raise ValueError('Index count mismatch')
 rows={item['id']:item for item in items}
 if identity not in rows:raise ValueError('Unknown extra identity '+identity)
 return confined(original,rows[identity]['folder'])
def checked_sources(folder, paths):
 receipt={x['path']:x for x in load(folder/'FILES.json')['files']}
 result={}
 for role,path in paths.items():
  relative=path.relative_to(folder).as_posix();expected=receipt.get(relative)
  if not expected or not path.is_file():raise FileNotFoundError('Restore the original source first: '+relative)
  actual=digest(path)
  if actual!=expected['sha256']:raise ValueError('Original source has changed; do not mix its receipt with edited data: '+relative)
  result[role]={'path':relative,'sha256':actual}
 return result

def generate(identity: str, out: Path, *, metric_preview=False, root=ROOT):
 folder=asset_folder(identity,root);definition=load(folder/'definition.json')
 if out.exists():raise FileExistsError('Choose a new output directory; no existing derivative is overwritten')
 import numpy as np
 from PIL import Image
 from channels import albedo,normals,roughness,orm,materialize
 kind='metric-preview' if metric_preview else 'native-1024'
 if metric_preview:
  if not identity.startswith('earth.') or 'mapset_id' not in definition:raise ValueError('Only a named earth surface supports this metric preview')
  import os;os.environ.setdefault('OPENCV_IO_ENABLE_OPENEXR','1')
  import cv2
  from metric_preview import preview
  # Use this extra's declared original asset layout, not the old aggregate index.
  source=folder/'files/build/maps'/definition['family']/definition['finish']/'runtime-1024'
  paths={'height':source/'height_mm.exr','base_color':source/'base_color.png','roughness':source/'roughness.png'}
  sources=checked_sources(folder,paths)
  profile=load(asset_folder(definition['physical_profile_id'],root)/'definition.json')
  resource=next((folder/'recipes').rglob('resource.json'))
  extent=load(resource)['finite_patch_mm']
  height=cv2.imread(str(paths['height']),cv2.IMREAD_UNCHANGED)
  if height is None:raise ValueError('EXR height decode failed')
  base=pixels(paths['base_color']);rough=pixels(paths['roughness'])
  out.mkdir(parents=True)
  preview(out/'preview.png',height,base[:,:,0].astype(np.float32)/255,rough.astype(np.float32)/255,profile['appearance_palette_srgb'],extent)
  metadata={'id':identity,'kind':kind,'software_preview':True,'native_image':False,'source_files':sources,'patch_mm':extent,'png_sha256':digest(out/'preview.png'),'premium_qualified':False}
  put(out/'material.json',metadata);return metadata
 if identity.startswith('wood.'):
  app=definition['appearance'];source=folder/'files/build/maps'/app['mapset']/'runtime-1024'
  paths={role:source/(role+'.png') for role in ('base_color','normal_opengl','roughness')};sources=checked_sources(folder,paths)
  maps,coat=materialize(pixels(paths['base_color'],True),pixels(paths['normal_opengl'],True),pixels(paths['roughness']),app)
  extent=app['patch_mm'];pbr={'base_color_srgb':[255,255,255],'metallic':0,'roughness':1,'normal_strength':1,'dielectric_ior':app['dielectric_ior']}
 elif identity.startswith('scan.'):
  slug=identity.removeprefix('scan.');source=folder/'files/build/maps'/slug/'runtime-2048'
  paths={role:source/(role+'.png') for role in ('base_color','normal_opengl','roughness')};sources=checked_sources(folder,paths)
  base=albedo(pixels(paths['base_color'],True),size=1024);normal=normals(pixels(paths['normal_opengl'],True),size=1024);rough=roughness(pixels(paths['roughness']),size=1024)
  dx=normal.copy();dx[:,:,1]=255-dx[:,:,1];maps={'base_color':base,'normal_opengl':normal,'normal_directx':dx,'roughness':rough,'orm':orm(rough)}
  coat=None;extent=definition['scan_extent_mm'];pbr={'base_color_srgb':[255,255,255],'metallic':0,'roughness':1,'normal_strength':1,'dielectric_ior':1.5}
 else:raise ValueError('This reviewed operation supports wood finishes and native scan profiles only')
 out.mkdir(parents=True);receipts={}
 for role,image in maps.items():
  path=out/(role+'.png');Image.fromarray(image).save(path,compress_level=4)
  receipts[role]={'path':path.name,'sha256':digest(path),'bytes':path.stat().st_size,'dimensions':list(image.shape[:2][::-1]),'color_space':'srgb' if role=='base_color' else 'linear_data'}
 metadata={'id':identity,'kind':kind,'definition_sha256':digest(folder/'definition.json'),'source_files':sources,'patch_mm':extent,'maps':receipts,'pbr':pbr,'clearcoat':coat,
  'base_color_mode':'replace','factors_baked_once':True,'auto_assign_physical_material':False,'native_render_validation':'not_run_for_this_new_output','premium_qualified':False}
 put(out/'material.json',metadata);return metadata

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--id',required=True);parser.add_argument('--out',required=True,type=Path);parser.add_argument('--metric-preview',action='store_true')
 a=parser.parse_args();result=generate(a.id,a.out,metric_preview=a.metric_preview);print(json.dumps({'id':result['id'],'out':str(a.out),'kind':result['kind'],'native_rendered':False}))
if __name__=='__main__':main()
