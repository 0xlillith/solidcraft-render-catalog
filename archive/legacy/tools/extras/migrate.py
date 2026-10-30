"""One-time, non-destructive import of historical resources into individual extras.

This is an editing workspace, not a plugin/package format. Existing releases and
stage generators remain historical inputs. No archive, tag or release is written.
"""
from __future__ import annotations
import argparse, collections, hashlib, html, json, posixpath, re, shutil, subprocess, zipfile
from pathlib import Path, PurePosixPath
from urllib.parse import unquote

REPO = Path(__file__).resolve().parents[2]
BASE_PIN = 'df356e2f277b9bd0d1cc62553dac8208f1aae958'
TAGS = {
 'catalog-v1':'catalog-v1-20261024', 'stage-01-woods':'wood-stage01-20261025',
 'stage-02-alloys':'alloys-stage02-20261025', 'stage-03-printing':'printing-stage03-20261025',
 'stage-03b-additive':'additive-stage03b-20261025', 'stage-04-earth-masonry':'earth-masonry-stage04-20261026',
 'stage-05-elements':'elements-stage05-20261026', 'scanned-pbr-r1':'scanned-pbr-quality-r1-20261026',
}
EXPECTED = {'catalog-v1':1386,'stage-01-woods':400,'stage-02-alloys':216,'stage-03-printing':291,
 'stage-03b-additive':222,'stage-04-earth-masonry':196,'stage-05-elements':272,'scanned-pbr-r1':8}
FONT_EXT = {'.ttf','.otf','.woff','.woff2','.ttc'}
TEXT_EXT = {'.json','.md','.csv','.txt','.py','.cjs','.js','.html','.gltf','.mtl'}

def digest(path: Path) -> str:
 with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p: Path):return json.loads(p.read_text(encoding='utf-8-sig'))
def serialized(obj) -> bytes:return (json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode('utf-8')
def safe_rel(value: str) -> str:
 p=PurePosixPath(value)
 if not value or p.is_absolute() or '..' in p.parts or '\\' in value or ':' in value:
  raise ValueError('Unsafe relative path: '+value)
 return p.as_posix()
def write_once(path: Path, data: bytes):
 path.parent.mkdir(parents=True,exist_ok=True)
 if path.exists():
  if path.read_bytes()!=data:raise FileExistsError('Refuse to overwrite edited file: '+str(path))
 else:path.write_bytes(data)

class ArchiveStore:
 def __init__(self):self.archives={};self.by_stage=collections.defaultdict(dict);self.hashes={}
 def add(self,stage: str,path: Path,expected: str):
  if path.name in self.archives:return
  print('VERIFY HISTORICAL ARCHIVE',path.name,path.stat().st_size,'bytes',flush=True)
  actual=digest(path)
  if actual!=expected:raise ValueError('Archive changed: '+str(path))
  z=zipfile.ZipFile(path)
  self.archives[path.name]=(z,path)
  self.hashes[path.name]={'archive':path.name,'tag':TAGS[stage],'sha256':actual,'bytes':path.stat().st_size,
    'url':f'https://github.com/0xlillith/solidcraft-render-catalog/releases/download/{TAGS[stage]}/{path.name}'}
  for member in z.infolist():
   if member.is_dir():continue
   name=safe_rel(member.filename)
   parts=PurePosixPath(name).parts
   if len(parts)<2:continue
   relative='/'.join(parts[1:])
   if PurePosixPath(relative).suffix.lower() in FONT_EXT:continue
   old=self.by_stage[stage].get(relative)
   if old:
    oz=self.archives[old[0]][0]
    if oz.read(old[1])!=z.read(name):raise ValueError('Conflicting archive member: '+relative)
   else:self.by_stage[stage][relative]=(path.name,name,member.file_size)
 def read(self,stage,relative):
  archive,member,_=self.by_stage[stage][relative]
  return self.archives[archive][0].read(member)
 def prefix(self,stage,path):
  return [p for p in self.by_stage[stage] if p==path or p.startswith(path.rstrip('/')+'/')]
 def close(self):
  for z,_ in self.archives.values():z.close()


def source_records(store: ArchiveStore):
 """Return one independent definition per indexed semantic record."""
 records=[]; sources={}
 def array(stage,rel,key):
  # Current readable source is preferred; archived wood data fill the historic gap.
  file=REPO/('catalog' if stage=='catalog-v1' else 'authoring/'+stage)/rel
  if file.is_file():data=file.read_bytes();where=str(file.relative_to(REPO)).replace('\\','/')
  else:data=store.read(stage,rel);where=f'archive:{TAGS[stage]}/{rel}'
  obj=json.loads(data.decode('utf-8-sig'))
  sources[where]=hashlib.sha256(data).hexdigest()
  return obj[key],where
 def add(stage,raw,kind,where,roots=None,dependencies=None,extra_id=None):
  aliases={('stage-02-alloys','c93200'):'alloy.c93200.reference'}
  rid=extra_id or aliases.get((stage,raw['id']),raw['id'])
  dependencies=[aliases.get((stage,dep),dep) for dep in (dependencies or [])]
  if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*',rid) or rid.upper().split('.')[0] in {'CON','PRN','AUX','NUL','COM1','LPT1'}:
   raise ValueError('Invalid extra ID '+rid)
  records.append({'id':rid,'source_id':raw['id'],'name':raw.get('name',rid),'kind':kind,'stage':stage,
   'source_document':where,'definition':raw,'roots':roots or [],'depends_on':dependencies or []})
 items,where=array('catalog-v1','Catalog.json','items')
 for r in items:add('catalog-v1',r,r['kind'],where,[r['path']])
 for stage in list(TAGS)[1:]:
  if stage=='scanned-pbr-r1':
   values,where=array(stage,'registry/resource-index.json','records')
   for r in values:
    slug=r['id'].removeprefix('scan.')
    add(stage,r,'photo_scanned_PBR',where,['build/materials/'+slug,'build/materials/'+r['id'],'build/maps/'+slug,
        'build/previews/'+slug+'.png'])
   continue
  profile_file='data/element-profiles.json' if stage=='stage-05-elements' else 'data/physical-profiles.json'
  profiles,pwhere=array(stage,profile_file,'profiles')
  profile_ids={p['id'] for p in profiles}
  for r in profiles:
   roots=[r['card_path']] if r.get('card_path') else []
   add(stage,r,'pure_element_reference' if stage=='stage-05-elements' else 'physical_reference',pwhere,roots)
  variant_file={'stage-01-woods':'data/material-variants.json','stage-02-alloys':'data/variants.json',
   'stage-05-elements':'data/element-appearances.json'}.get(stage,'data/material-variants.json')
  variants,vwhere=array(stage,variant_file,'items')
  recipe_table={}
  if stage in ('stage-03-printing','stage-03b-additive'):
   recipe_table={r['id']:r for r in array(stage,'data/process-recipes.json','items')[0]}
  for r in variants:
   rid=r['id']; dep=r.get('physical_profile_id',r.get('profile_id',r.get('element_id')))
   if dep not in profile_ids:raise ValueError('Missing physical identity for '+rid)
   roots=['build/materials/'+rid,'build/appearances/'+rid]
   if stage=='stage-01-woods':
    roots+=['build/maps/'+r['appearance']['mapset'],r['appearance']['preview']]
   elif stage=='stage-02-alloys':roots+=['build/maps/'+r['finish_id']]
   elif stage=='stage-03-printing':
    process=recipe_table[r['process_id']];roots+=['build/maps/'+process['group']+'/'+process['id']]
   elif stage=='stage-03b-additive':
    process=recipe_table[r['recipe_id']];roots+=['build/maps/'+process['family']+'/'+process['id']]
   elif stage=='stage-04-earth-masonry':
    roots+=['build/maps/'+r['mapset_id'].replace('.', '/', 1)]
   elif stage=='stage-05-elements':
    family='metal' if r['finish'].startswith('metal-') else 'mineral'
    roots+=['build/maps/'+family+'/'+r['finish']]
   add(stage,r,'illustrative_element_appearance' if stage=='stage-05-elements' else 'material_appearance',vwhere,roots,[dep])
 counts=collections.Counter(r['stage'] for r in records)
 if dict(counts)!=EXPECTED:raise ValueError('Coverage mismatch '+str(counts))
 ids=[r['id'].casefold() for r in records]
 if len(ids)!=len(set(ids)):
  duplicates={key for key,count in collections.Counter(ids).items() if count>1}
  raise ValueError('Duplicate case-insensitive extra identity: '+str([(r['id'],r['stage'],r['kind']) for r in records if r['id'].casefold() in duplicates]))
 return records,sources


def create_workspace(store: ArchiveStore, records, source_hashes, materialize: bool):
 extras=REPO/'extras'; index=[]; total_files=0; total_bytes=0; unresolved=[]
 for number,r in enumerate(records,1):
  folder=extras/r['id']; stage=r['stage']; selected=set()
  for prefix in r['roots']:selected.update(store.prefix(stage,safe_rel(prefix)))
  # Preserve each old file's relative context inside files/, including shared maps.
  # This keeps glTF sidecars usable, without changing anyone else's assets.
  for rel in list(selected):
   if not rel.endswith('.gltf'):continue
   gltf=json.loads(store.read(stage,rel))
   for item in gltf.get('buffers',[])+gltf.get('images',[]):
    uri=item.get('uri','')
    if not uri or uri.startswith('data:'):continue
    reference=posixpath.normpath(posixpath.join(posixpath.dirname(rel),unquote(uri)))
    safe_rel(reference)
    if reference not in store.by_stage[stage]:unresolved.append({'extra':r['id'],'gltf':rel,'missing':reference})
    else:selected.add(reference)
  manifest=[]
  for rel in sorted(selected):
   archive,member,declared_size=store.by_stage[stage][rel]
   data=store.read(stage,rel)
   if len(data)!=declared_size:raise ValueError('Member length mismatch')
   h=hashlib.sha256(data).hexdigest();output='files/'+rel
   manifest.append({'path':output,'archive':archive,'member':member,'bytes':len(data),'sha256':h})
   if materialize:write_once(folder/output,data)
   total_files+=1;total_bytes+=len(data)
  definitions=serialized(r['definition']);dhash=hashlib.sha256(definitions).hexdigest()
  entrypoints=[f['path'] for f in manifest if f['path'].endswith(('.solidcraft','.glb','.gltf'))]
  previews=[f['path'] for f in manifest if PurePosixPath(f['path']).name in ('preview.png','native-render.png') or '/build/previews/' in f['path'] or '/cards/' in f['path']]
  info={'id':r['id'],'source_id':r['source_id'],'name':r['name'],'kind':r['kind'],'depends_on':r['depends_on'],
    'definition':'definition.json','files':'FILES.json','origin':{'collection':stage,'tag':TAGS[stage],'source_document':r['source_document'],'repository_snapshot':BASE_PIN},
    'migration_definition_sha256':dhash,'entrypoints':entrypoints,'previews':previews,
    'quality_note':'Reorganization only. Source qualification is preserved; no new native, physical or premium acceptance is claimed.',
    'packaging_decision':None}
  write_once(folder/'definition.json',definitions);write_once(folder/'extra.json',serialized(info))
  write_once(folder/'FILES.json',serialized({'files':manifest,'binary_tracking':'restorable working copies; original archives remain immutable backups',
    'original_relative_paths_preserved':True,'hard_links_used':False}))
  links='\n'.join(f'- [{PurePosixPath(p).name}]({p})' for p in entrypoints[:6]) or 'This reference has no standalone native model.'
  preview=('\n![Reference preview]('+previews[0]+')\n') if previews else ''
  readme=f"# {r['name']}\n\n**Extra:** `{r['id']}` · **Kind:** `{r['kind']}`\n\nEdit `definition.json` for this independent resource. Its original source record and scientific qualifiers are retained without changing values. `extra.json` links separate physical references; an appearance edit never assigns physical properties automatically.\n\n## Working files\n\n{links}\n{preview}\n`files/` contains independent editable copies, restored from the file-level checksums in `FILES.json`. Historical relative layouts are retained inside that folder so glTF dependencies do not break. No hard links or symlinks are used. This checkout's working binaries are not automatically uploaded by Git: restore them with `tools/extras/manage.py restore` and use `verify-files` before editing.\n\n## Provenance and status\n\nOriginal collection: `{stage}`. Historical release: `{TAGS[stage]}`. This reorganization is not a new quality pass, a plugin format or a new pack. Previous acceptance and unmeasured/reference-only limits remain exactly those in the definition. The large 2K/4K authoring masters not present in these runtime/source archives remain preserved in their historical releases; do not relabel a 1K/2K runtime copy as a master.\n\nAfter editing, keep the original receipt and record changed files and actual tests in a new `CHANGELOG.md`/`validation/` result. Old generated gallery/stage inputs are historical and must not overwrite this folder. Packaging and final taxonomy are deliberately deferred.\n"
  write_once(folder/'README.md',readme.encode('utf-8'))
  index.append({k:info[k] for k in ('id','name','kind','depends_on') }|{'folder':r['id'],'origin_collection':stage,'files':len(manifest)})
  if number%200==0:print('EXTRAS',number,'/',len(records),'copied_files',total_files,'bytes',total_bytes,flush=True)
 if unresolved:raise ValueError('Unresolved glTF dependencies: '+json.dumps(unresolved[:12]))
 write_once(extras/'INDEX.json',serialized({'purpose':'Editable individual extras, not an installation/pack format','count':len(index),'items':index}))
 write_once(extras/'ARCHIVE-SOURCES.json',serialized({'purpose':'Historical restoration sources only; no new packs','archives':list(store.hashes.values())}))
 report={'date':'2026-10-27','scope':'source and directory reorganization only','historical_resources':2983,'additional_scanned_references':8,
   'total_extras':len(records),'by_origin':dict(collections.Counter(r['stage'] for r in records)),
   'by_kind':dict(collections.Counter(r['kind'] for r in records)),'working_files':total_files,'working_bytes':total_bytes,
   'unresolved_gltf_dependencies':unresolved,'hard_links_or_symlinks':False,'source_inputs_sha256':source_hashes,
   'original_releases_unchanged':True,'existing_quality_worktree_unchanged':True,'premium_acceptance_inferred':False,
   'masters_restoration':'Historical higher-resolution master archives remain intact; this workspace restores published runtime maps plus per-resource sources/models/previews.'}
 write_once(extras/'MIGRATION.json',serialized(report))
 print('MIGRATION COMPLETE',json.dumps({k:v for k,v in report.items() if k!='source_inputs_sha256'}),flush=True)


def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--restoration',type=Path,required=True);ap.add_argument('--previous-cache',type=Path,required=True);ap.add_argument('--materialize',action='store_true');a=ap.parse_args()
 store=ArchiveStore()
 try:
  receipts=load(a.restoration/'historical-source-receipts.json')
  inverse={v:k for k,v in TAGS.items()}
  for receipt in receipts:store.add(inverse[receipt['tag']],Path(receipt['archive_path']),receipt['sha256'])
  for stage,tag in TAGS.items():
   cache=a.previous_cache/tag
   checksum=cache/('RELEASE-SHA256SUMS.txt' if stage=='catalog-v1' else 'SHA256SUMS.txt')
   hashes={}
   for line in checksum.read_text(encoding='utf-8-sig').splitlines():
    parts=line.strip().split(maxsplit=1)
    if len(parts)==2:hashes[parts[1].lstrip('*')]=parts[0]
   for path in cache.glob('*.zip'):
    if 'runtime-maps' in path.name or (stage=='catalog-v1' and '-materials-' in path.name):store.add(stage,path,hashes[path.name])
  records,sources=source_records(store)
  print('IDENTITIES VERIFIED',len(records),dict(collections.Counter(r['stage'] for r in records)),flush=True)
  create_workspace(store,records,sources,a.materialize)
 finally:store.close()
if __name__=='__main__':main()
