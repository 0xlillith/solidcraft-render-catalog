"""Enumerate every material appearance without confusing references/lights with materials."""
from __future__ import annotations
import argparse,json,pathlib,collections,math

def read(p):return json.loads(p.read_text(encoding='utf8'))
def srgb(v):
 return [round(255*(12.92*x if x<=.0031308 else 1.055*x**(1/2.4)-.055)) for x in v]
def profile_record(row,base):
 maps={key:str((base/row['path']/value['path']).resolve()) for key,value in row['maps'].items()}
 pbr=row['pbr'];return {'id':row['id'],'name':row['name'],'collection':'wood-stage01' if row['id'].startswith('wood.') else 'scanned-pbr-r1','mapset':row.get('source_mapset',row['id']),'patch_mm':row['patch_mm'],'color_srgb':pbr['base_color_srgb'],'metallic':pbr['metallic'],'roughness':pbr['roughness'],'normal_strength':pbr['normal_strength'],'maps':maps,'base_color_mode':'replace','clearcoat':row.get('clearcoat'),'physical_profile_id':row['physical_profile_id'],'source_maps_are_baked':True,'full_optics_supported':True,'qualification':'candidate_not_premium'}
def build(repo,runtime,profiles,baseline=None):
 result=[];catalog=read(repo/'catalog/Catalog.json')['items'];overview={'baseline_catalog_records':len(catalog),'baseline_kind_counts':dict(collections.Counter(x['kind'] for x in catalog)),'non_material_records_not_rendered_as_solid':[]}
 for row in catalog:
  if row['id'].startswith(('MAT-','SELENE-AP-')):
   path=repo/'catalog'/row['path']/'material.json'
   if not path.exists():raise FileNotFoundError(path)
   data=read(path);maps={}
   if row['id'].startswith('SELENE-AP-'):
    projection=data['native_projection'];pbr=projection.get('pbr') or {};color=projection['color']
    if isinstance(color,str):color=[int(color[i:i+2],16) for i in (1,3,5)]
    omissions=data['original_specification']['baseline_projection'].get('omitted_target_features',[])
    result.append({'id':row['id'],'name':row['name'],'collection':'selene-baseline','mapset':row['id'],'patch_mm':[100,100],'color_srgb':color,'metallic':pbr.get('metallic',0),'roughness':pbr.get('roughness',.5),'normal_strength':1,'maps':{},'base_color_mode':'modulate','full_optics_supported':True,'declared_omissions':omissions,'qualification':'opaque_baseline_only_not_advanced_intent','physical_profile_id':None})
    continue
   if baseline:
    for key,value in data.get('maps',{}).items():
     if key in ('base_color','normal_gl','roughness','metallic'):
      target=baseline/row['path']/value['path']
      if not target.is_file():raise FileNotFoundError('Declared baseline channel missing: '+str(target))
      maps[{'normal_gl':'normal_opengl'}.get(key,key)]=str(target.resolve())
   requirements={k:data.get(k,0) for k in ('transmission','anisotropy','iridescence','emission_strength')}
   required=[k for k,v in requirements.items() if v and float(v)>0]
   result.append({'id':row['id'],'name':row['name'],'collection':'catalog-v1','mapset':row['id'],'patch_mm':data['tile_mm'],'color_srgb':[255,255,255],'metallic':data['metallic'],'roughness':data['roughness'],'normal_strength':1,'maps':maps,'base_color_mode':'replace','full_optics_supported':not required,'unsupported_opaque_features':required,'physical_profile_id':None,'qualification':'authored_unmeasured','source_scope':row.get('scope'),'dielectric_ior':data.get('ior',1.5),'clearcoat':({'weight':data['clearcoat'],'roughness':.08,'ior':1.5,'basis':'catalog/tools/materials.py material_gltf authored clearcoat'} if data.get('clearcoat',0)>0 else None)})
  else:overview['non_material_records_not_rendered_as_solid'].append({'id':row['id'],'kind':row['kind']})
 for row in read(profiles/'index.json')['records']:result.append(profile_record(row,profiles))
 stage=repo/'authoring/stage-02-alloys';fin={v['id']:v for v in read(stage/'data/finishes.json')['finishes']}
 for row in read(stage/'data/variants.json')['items']:
  folder=runtime/'stage-02-alloys/build/maps'/row['finish_id']/'runtime-1024'
  result.append({'id':row['id'],'name':row['name'],'collection':'alloys-stage02','mapset':row['finish_id'],'patch_mm':[40,40],'color_srgb':srgb(row['palette_linear']),'metallic':1,'roughness':fin[row['finish_id']]['roughness'],'normal_strength':1,'maps':mapfiles(folder),'base_color_mode':'modulate','full_optics_supported':True,'physical_profile_id':row['physical_profile_id']})
 for dirname,col in [('stage-03-printing','printing-stage03'),('stage-03b-additive','additive-stage03b')]:
  stage=repo/'authoring'/dirname;variants=read(stage/'data/material-variants.json')['items'];phys={x['id']:x for x in read(stage/'data/physical-profiles.json')['profiles']};recipes={x['id']:x for x in read(stage/'data/process-recipes.json')['items']}
  for row in variants:
   pid=row.get('profile_id',row.get('physical_profile_id'));profile=phys[pid];recipe=recipes[row.get('process_id',row.get('recipe_id'))];family=recipe.get('group',recipe.get('family'));folder=runtime/dirname/'build/maps'/family/recipe['id']/'runtime-1024'
   vis=row.get('visual_parameters',{});translucent=bool(profile.get('translucent_intent',False));metal=vis.get('metallic',1 if profile.get('family')=='metal' else 0)
   # Metallic channel, when present, remains authoritative for native shading.
   result.append({'id':row['id'],'name':row['name'],'collection':col,'mapset':family+'/'+recipe['id'],'patch_mm':recipe['patch_mm'],'color_srgb':vis.get('base_color_srgb',profile['appearance_palette_srgb']),'metallic':metal,'roughness':1,'normal_strength':1,'maps':mapfiles(folder),'base_color_mode':'modulate','physical_profile_id':pid,'full_optics_supported':not translucent,'unsupported_opaque_features':['translucency'] if translucent else []})
 stage=repo/'authoring/stage-04-earth-masonry';phys={x['id']:x for x in read(stage/'data/physical-profiles.json')['profiles']};recipes={x['id']:x for x in read(stage/'data/process-recipes.json')['processes']}
 for row in read(stage/'data/material-variants.json')['items']:
  profile=phys[row['physical_profile_id']];recipe=recipes[row['mapset_id']];folder=runtime/'stage-04-earth-masonry/build/maps'/row['family']/row['finish']/'runtime-1024'
  result.append({'id':row['id'],'name':row['name'],'collection':'earth-masonry-stage04','mapset':row['mapset_id'],'patch_mm':recipe['patch_mm'],'color_srgb':profile['appearance_palette_srgb'],'metallic':0,'roughness':1,'normal_strength':1,'maps':mapfiles(folder),'base_color_mode':'modulate','physical_profile_id':profile['id'],'full_optics_supported':True})
 for row in read(repo/'authoring/stage-05-elements/data/element-appearances.json')['items']:
  folder=runtime/'stage-05-elements/build/maps'/('metal' if row['metallic'] else 'mineral')/row['finish']/'runtime-1024'
  result.append({'id':row['id'],'name':row['name'],'collection':'elements-stage05','mapset':row['mapset'],'patch_mm':[30,30],'color_srgb':row['palette_srgb'],'metallic':1 if row['metallic'] else 0,'roughness':1,'normal_strength':1,'maps':mapfiles(folder),'base_color_mode':'modulate','physical_profile_id':row['element_id'],'full_optics_supported':True})
 ids=[x['id'] for x in result]
 if len(ids)!=len(set(ids)):raise ValueError('Duplicate material appearance ID')
 for row in result:
  if any(not math.isfinite(float(v)) or float(v)<=0 for v in row['patch_mm'][:2]):raise ValueError('Invalid material scale '+row['id'])
  missing=[p for p in row['maps'].values() if not pathlib.Path(p).is_file()]
  if missing:raise FileNotFoundError(missing)
  row['native_test_status']='not_run';row['premium_qualified']=False
 overview.update({'material_appearances':len(result),'per_collection':dict(collections.Counter(x['collection'] for x in result)),'opaque_supported_candidates':sum(x['full_optics_supported'] for x in result),'non_opaque_or_advanced_optics':sum(not x['full_optics_supported'] for x in result)})
 return {'summary':overview,'materials':result}
def mapfiles(folder):
 out={}
 for key,choices in [('base_color',('base_color.png','base_color_modulation.png')),('normal_opengl',('normal_opengl.png',)),('roughness',('roughness.png',)),('metallic',('metallic.png',))]:
  for name in choices:
   if (folder/name).is_file():out[key]=str((folder/name).resolve());break
 if len(out)<3:raise FileNotFoundError('Missing required channels '+str(folder))
 return out
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--repo',type=pathlib.Path,required=True);p.add_argument('--runtime',type=pathlib.Path,required=True);p.add_argument('--profiles',type=pathlib.Path,required=True);p.add_argument('--baseline',type=pathlib.Path);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args()
 data=build(a.repo,a.runtime,a.profiles,a.baseline);a.output.write_text(json.dumps(data,indent=2),encoding='utf8');print('MATERIAL_INVENTORY',json.dumps({k:v for k,v in data['summary'].items() if not isinstance(v,list)}),flush=True)
