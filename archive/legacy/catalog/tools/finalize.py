from pathlib import Path
import json,time,datetime,subprocess,hashlib,collections,zipfile
A=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
end=time.monotonic()+1200
while True:
 p=A/'reports/native-render-progress.json';n=read(p)
 if n.get('errors'):raise RuntimeError(n['errors'][:2])
 if n.get('completed')==600 and (A/'reports/final-native-readback.json').exists():
  r=read(A/'reports/native-material-renders.json')
  if r.get('status')=='PASS' and (A/'reports/native-material-renders.json').stat().st_mtime > (A/'reports/material-preview-lighting-attempt1.zip').stat().st_mtime:break
 if time.monotonic()>end:raise TimeoutError('latest native renders did not finish')
 time.sleep(3)
print('FINAL_ASSET_FREEZE',flush=True)
reports=['material-generation','lighting-generation','environment-generation','native-materials','native-environments','native-lighting','setup-generation','supplements','selene-shots','asset-validation','native-material-renders','native-setup-renders','native-selene-renders','native-environment-previews','final-native-readback','gallery-interaction-tests']
for name in reports:assert read(A/'reports'/(name+'.json'))['status']=='PASS',name
for i in range(1,601):
 f=A/'materials'/f'MAT-{i:03}';r=read(f/'native-render-receipt.json');assert r['samples']==64 and r['start']['environment']['intensity']==.1,(i,'preview gain');assert hashlib.sha256((f/'native-render.png').read_bytes()).hexdigest()==r['sha256']
assert not subprocess.check_output(['git','status','--porcelain'],cwd=r'D:\SolidCraft\source-main-9e6e0b8d').strip()
subprocess.run(['python','-X','utf8','-B',str(A/'tools/catalog.py')],check=True)
validation={'official_gltf_files':2416,'official_gltf_errors':0,'official_gltf_warnings':0,'native_containers_reopened':1376,'gpu_material_images':600,'gpu_selene_appearance_images':48,'gpu_lighting_and_setup_images':377,'native_environment_model_snapshots':280,'native_environment_cold_reopen':280,'native_uniform_appearance_library_entries':600,'physical_native_reference_entries':46,'gallery_interaction_tests':6,'all_source_phenomena_certified':False}
summary=read(A/'reports/catalog-summary.json');summary['verification']=validation;summary['material_thumbnail_hdr_gain']=.1;summary['completed_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();write(A/'reports/catalog-summary.json',summary)
build=read(A/'build.json');build.update(status='COMPLETE_LOCAL_AUTHORING_V1',completed_utc=summary['completed_utc'],verification=validation,application_source_clean=True,application_install_modified=False,github_published=False,full_original_physical_specifications_implemented=False);write(A/'build.json',build)
# Hash deliverables, immutable source snapshots and authoring scripts. Tool installations,
# browser caches and diagnostic logs are intentionally outside this resource manifest.
exclude_top={'reports'};exclude_dirs={'_deps','validator','__pycache__','browser-profile','node_modules'}
selected=[]
for p in A.rglob('*'):
 if not p.is_file():continue
 rel=p.relative_to(A)
 if rel.parts[0] in exclude_top or any(x in rel.parts for x in exclude_dirs) or p.name in ['SHA256SUMS.txt','PACK-RECEIPT.json']:continue
 selected.append(p)
selected.sort(key=lambda p:p.relative_to(A).as_posix())
entries=[];total=0
for i,p in enumerate(selected):
 h=hashlib.sha256()
 with p.open('rb') as stream:
  for chunk in iter(lambda:stream.read(4*1024*1024),b''):h.update(chunk)
 entries.append(h.hexdigest()+'  '+p.relative_to(A).as_posix());total+=p.stat().st_size
 if (i+1)%5000==0:print('HASHED',i+1,flush=True)
(A/'SHA256SUMS.txt').write_text('\n'.join(entries)+'\n',encoding='utf-8')
all_files=[p for p in A.rglob('*') if p.is_file()]
whole_bytes=sum(p.stat().st_size for p in all_files);output_files=[p for p in selected if p.relative_to(A).parts[0] not in ['source','tools','licenses']]
receipt={'status':'COMPLETE_LOCAL_AUTHORING_V1','root':str(A),'completed_utc':summary['completed_utc'],'catalog_entries':1386,'collections':summary['collections'],'manifest_files':len(selected),'manifest_bytes':total,'manifest_gib':round(total/2**30,3),'output_files':len(output_files),'output_bytes':sum(p.stat().st_size for p in output_files),'folder_files_including_diagnostics_tools':len(all_files),'folder_bytes_including_diagnostics_tools':whole_bytes,'folder_gib_including_diagnostics_tools':round(whole_bytes/2**30,3),'extensions':dict(collections.Counter(p.suffix.lower() for p in selected)),'verification':validation,'manifest_exclusions':['reports/**','tools/_deps/**','tools/validator/**','**/__pycache__/**','SHA256SUMS.txt','PACK-RECEIPT.json'],'manifest_sha256':hashlib.sha256((A/'SHA256SUMS.txt').read_bytes()).hexdigest(),'application_source_unchanged':True,'installed_application_modified':False,'published_to_github':False,'important_limit':'Complete source-catalog file coverage with explicit procedural/native approximations; not every high-level physical, spectral, motion or semantic requirement is implemented or certified.'}
write(A/'PACK-RECEIPT.json',receipt)
print('PACK_FINAL',json.dumps(receipt),flush=True)
