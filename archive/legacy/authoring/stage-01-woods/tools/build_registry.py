"""Internal authoring index and gallery, not a SolidCraft plugin standard."""
from pathlib import Path
import collections,csv,hashlib,html,json
A=Path(__file__).resolve().parents[1]; R=A.parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,v):
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
def main():
 woods=read(A/'data/woods.json');finishes=read(A/'data/finishes.json')['finishes'];profiles=read(A/'data/physical-profiles.json')['profiles'];profile_ids={p['id'] for p in profiles};variants=[]
 for wood in woods['woods']:
  if wood['physical_profile_id'] not in profile_ids:raise ValueError('missing physical reference')
  for cut in woods['cuts']:
   for finish in finishes:
    variants.append({'id':f"wood.{wood['id']}.{cut}.{finish['id']}",'name':f"{wood['name']} / {cut} / {finish['name']}",'kind':'material_variant','family':'Wood','species_id':wood['id'],'cut':cut,'finish_id':finish['id'],'physical_profile_id':wood['physical_profile_id'],'physical_scope':'uncoated clear-wood substrate at 12% dry-basis moisture; coating contribution unknown','appearance':{'mapset':wood['id']+'/'+cut,'color_multiplier_linear':finish['color_multiplier_linear'],'roughness_factor':finish['roughness_factor'],'normal_scale':finish['normal_scale'],'clearcoat':finish['clearcoat'],'clearcoat_roughness':finish['clearcoat_roughness'],'metallic':0,'dielectric_ior':1.5,'ior_basis':'illustrative authoring value, not measured species optics','patch_mm':woods['end_grain_patch_mm'] if cut=='end-grain' else woods['finite_patch_mm'],'wrap':'clamp_to_edge','seamless':False,'preview':'build/previews/'+wood['id']+'/'+cut+'/'+finish['id']+'.png'},'quality':{'target':'premium','status':'procedural_candidate','native_visual_acceptance':'not_run','measured_appearance':False,'physical_model_certified':False},'plugin_contract':None,'auto_assign_physical_material':False})
 if len(variants)!=384 or len({v['id'] for v in variants})!=384:raise ValueError('incorrect variant coverage')
 write(A/'data/material-variants.json',{'internal_authoring_revision':1,'not_an_installable_plugin':True,'items':variants})
 prefix='authoring/stage-01-woods/'
 datasets=[{'path':'catalog/Catalog.json','items_key':'items','count':1386,'origin':'catalog-v1-20261024','source_commit':'c146917376ed214adf5aeb7e3999f18321788b8e'},{'path':prefix+'data/material-variants.json','items_key':'items','count':384},{'path':prefix+'data/physical-profiles.json','items_key':'profiles','id_prefix':'physical.','count':16}]
 write(A/'registry/global-index.json',{'purpose':'federated authoring inventory; paths relative to repository root','plugin_contract':None,'total_resources':1786,'datasets':datasets,'quality':'No blanket premium or native-ready status is implied.'})
 with (A/'registry/wood-variants.csv').open('w',newline='',encoding='utf-8') as f:
  w=csv.writer(f);w.writerow(['id','name','species','cut','finish','physical_profile','mapset','native_status'])
  for v in variants:w.writerow([v['id'],v['name'],v['species_id'],v['cut'],v['finish_id'],v['physical_profile_id'],v['appearance']['mapset'],'not_run'])
 # Expand the complete global inventory when run in the repository; never fabricate legacy rows.
 baseline=R/'catalog/Catalog.json'
 if baseline.exists():
  old=read(baseline)['items'];source=R/'catalog/source/assets/render';bindings=read(source/'physical/bindings.json')['catalog'];refs={x['catalog_id']:x for x in bindings};known={x['id'] for x in read(source/'physical/profiles.json')['profiles']};selene={x['id']:x for x in read(source/'selene/materials/appearance-pack.json')['items']};audit=[]
  for row in old:
   if not row['id'].startswith(('MAT-','SELENE-AP-')):continue
   ids=[row['id']] if row['id'].startswith('MAT-') else selene[row['id']].get('source_catalog_ids',[])
   links=[{'catalog_id':cid,**p} for cid in ids for p in refs.get(cid,{}).get('references',[])]
   if any(x['profile_id'] not in known for x in links):raise ValueError('dangling legacy physical reference')
   audit.append({'id':row['id'],'name':row['name'],'status':'reference_candidates_require_selection' if links else 'missing_specific_physical_reference','candidate_links':links,'auto_assign':False})
  counts=dict(collections.Counter(x['status'] for x in audit))
  write(A/'reports/legacy-physical-coverage.json',{'status':'audited_not_completed','source_catalog_sha256':hashlib.sha256(baseline.read_bytes()).hexdigest(),'material_looks':len(audit),'counts':counts,'items':audit})
  combined=old+variants+[{'id':'physical.'+p['id'],'name':p['name'],'kind':'physical_profile','profile_id':p['id']} for p in profiles]
  if len({x['id'] for x in combined})!=len(combined):raise ValueError('global ID collision')
  write(A/'registry/expanded-index.json',{'plugin_contract':None,'count':len(combined),'items':combined})
  print('LEGACY_AUDIT',len(audit),counts)
 payload=json.dumps(variants,ensure_ascii=False).replace('</','<\\/')
 page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Stage 01 wood authoring</title><style>body{margin:0;background:#101820;color:#edf5fa;font:16px system-ui}header,main{max-width:1440px;padding:28px;margin:auto}p{line-height:1.6;color:#bfccd6}a{color:#8ad7ee}input,select{padding:12px;margin:4px;background:#23323f;color:white;border:1px solid #587080;font:inherit}#grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:16px}article{padding:14px;border:1px solid #405365;border-radius:10px;background:#1b2732}img{width:100%;height:270px;object-fit:contain}h3{font-size:16px}small{color:#b7cad5}</style><header><small>PRIVATE AUTHORING · NO PLUGIN STANDARD</small><h1>Wood: grain, finish and physical identity</h1><p>16 source-backed species · 4 grain views · 6 authored finishes · 384 variants. Properties refer to uncoated clear wood at 12% dry-basis moisture. Images are software swatches, not SolidCraft renders. Premium/native acceptance is pending.</p><p><a href="data/physical-profiles.json">Physical profiles</a> · <a href="registry/global-index.json">Global inventory</a> · <a href="registry/wood-variants.csv">Variant index</a></p><input id="q" placeholder="Search wood, cut or finish"><select id="cut"><option value="">All grain views</option>'''+''.join('<option>'+html.escape(c)+'</option>' for c in woods['cuts'])+'''</select><select id="finish"><option value="">All finishes</option>'''+''.join('<option value="'+f['id']+'">'+html.escape(f['name'])+'</option>' for f in finishes)+'''</select><p id="counter"></p></header><main id="grid"></main><script>const rows='''+payload+''';const el=id=>document.getElementById(id);function draw(){const rows2=rows.filter(r=>r.name.toLowerCase().includes(el('q').value.toLowerCase())&&(!el('cut').value||r.cut===el('cut').value)&&(!el('finish').value||r.finish_id===el('finish').value));el('counter').textContent=rows2.length+' matching variants';el('grid').replaceChildren();for(const r of rows2){const box=document.createElement('article'),im=document.createElement('img'),h=document.createElement('h3'),p=document.createElement('small');im.src=r.appearance.preview;im.loading='lazy';im.alt=r.name;h.textContent=r.name;p.textContent=r.physical_profile_id+' · native validation pending';box.append(im,h,p);el('grid').append(box);}}for(const id of ['q','cut','finish'])el(id).addEventListener('input',draw);draw();</script></html>'''
 (A/'index.html').write_text(page,encoding='utf-8')
 print('STAGE_INDEX',len(variants),'variants',len(profiles),'physical profiles; federated total',1786)
if __name__=='__main__':main()
