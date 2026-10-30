"""Inspect, validate and safely restore individual extra folders (no packaging).

Examples:
  python tools/extras/manage.py validate
  python tools/extras/manage.py verify-files --id element.029.cu.metal-brushed
  python tools/extras/manage.py restore --id MAT-001 --cache-root /path/to/cache
"""
from __future__ import annotations
import argparse, hashlib, json, os, re, sys, tempfile, urllib.request, zipfile
from pathlib import Path, PurePosixPath

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/library'))
from common import archive_sources, asset_directory, metadata, path_map

# Retain the old argument name for callers; the default is now the repository.
EXTRAS=ROOT

def read_json(path):
 def reject(value):raise ValueError('Nonfinite JSON number: '+value)
 return json.loads(path.read_text(encoding='utf-8'),parse_constant=reject)
def sha(path):
 with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def confined(root: Path,relative: str) -> Path:
 value=PurePosixPath(relative)
 if not relative or value.is_absolute() or '..' in value.parts or '\\' in relative or ':' in relative:
  raise ValueError('Unsafe relative path '+relative)
 result=root.joinpath(*value.parts)
 if not result.resolve().is_relative_to(root.resolve()):raise ValueError('Path leaves its extra folder')
 return result

def library_layout(root):
 return (root/'catalog/paths.json').is_file() or (root/'assets').is_dir()

def legacy_root(root):
 if (root/'INDEX.json').is_file():return root
 if (root/'extras/INDEX.json').is_file():return root/'extras'
 raise FileNotFoundError('No asset catalog or legacy index at '+str(root))

def archive_inventory(root):
 root=Path(root)
 return archive_sources(root) if library_layout(root) else legacy_root(root)/'ARCHIVE-SOURCES.json'

def entries(ids=None, root=EXTRAS):
 root=Path(root);selected=set(ids or [])
 if library_layout(root):
  mapping=path_map(root)
  if selected-set(mapping):raise ValueError('Unknown requested ID(s)')
  # Read the catalog once, including when validating the full library.
  return [{'id':identity,'folder':asset_directory(identity,root,mapping=mapping).relative_to(root).as_posix()}
          for identity in sorted(mapping,key=str.casefold) if not selected or identity in selected]
 original=legacy_root(root);index=read_json(original/'INDEX.json');items=index['items']
 if len(items)!=index['count']:raise ValueError('Index count mismatch')
 if selected-set(x['id'] for x in items):raise ValueError('Unknown requested ID(s)')
 return [dict(item,folder=confined(original,item['folder']).relative_to(root).as_posix())
         for item in items if not selected or item['id'] in selected]

def validate_authored(folder,identity,meta,original_paths):
 count=0
 for relative in (set(meta['entrypoints'])|set(meta['previews']))-original_paths:
  if not relative.startswith('authored/') or not relative.endswith('.png'):
   raise ValueError('Unresolved advertised file '+identity)
  image=confined(folder,relative);receipt=read_json(image.with_name('receipt.json'))
  if receipt.get('id')!=identity or not image.is_file() or sha(image)!=receipt.get('png_sha256'):
   raise ValueError('Authored preview identity/integrity mismatch '+identity)
  count+=1
 active=meta.get('active_appearance')
 if active is not None:
  if not active.startswith('authored/') or not active.endswith('/material.json'):
   raise ValueError('Invalid active per-extra appearance path')
  path=confined(folder,active);appearance=read_json(path)
  if appearance.get('id')!=identity:raise ValueError('Active appearance belongs to another extra')
  if appearance.get('auto_assign_physical_material') is not False:
   raise ValueError('An appearance may not auto-assign physical reference values')
  for role,record in appearance['maps'].items():
   source=confined(path.parent,record['path'])
   if not source.is_file() or source.stat().st_size!=record['bytes'] or sha(source)!=record['sha256']:
    raise ValueError('Authored map failed its own source receipt '+identity+' '+role)
   count+=1
 return count

def validate(root=EXTRAS):
 items=entries(root=root); seen=set();known={x['id'] for x in items};files=0;authored_files=0
 archives={x['archive']:x for x in read_json(archive_inventory(root))['archives']}
 for item in items:
  identity=item['id']
  if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*',identity):raise ValueError('Unsafe ID '+identity)
  if identity.casefold() in seen:raise ValueError('Duplicate case-insensitive ID')
  seen.add(identity.casefold());folder=confined(root,item['folder'])
  meta=metadata(folder);definition=read_json(folder/'definition.json')
  if meta['id']!=identity or meta['source_id']!=definition['id']:raise ValueError('Definition identity mismatch '+identity)
  if set(meta['depends_on'])-known:raise ValueError('Unresolved physical reference '+identity)
  if meta['packaging_decision'] is not None:raise ValueError('Packaging was explicitly deferred')
  for readable in meta.get('editable_recipes',[])+meta.get('historical_evidence',[]):
   source=confined(folder,readable)
   if not source.is_file():raise ValueError('Missing readable per-extra source '+str(source))
   read_json(source)
  paths=set()
  for member in read_json(folder/'FILES.json')['files']:
   confined(folder,member['path']);confined(Path('.'),member['member'])
   if member['path'] in paths:raise ValueError('Duplicate file destination '+identity)
   paths.add(member['path']);files+=1
   if member['archive'] not in archives:raise ValueError('Missing original archive receipt')
   if not re.fullmatch('[0-9a-f]{64}',member['sha256']):raise ValueError('Invalid SHA-256')
   if member['bytes']<0 or member['bytes']>512*1024*1024:raise ValueError('Invalid restored file size')
  authored_files+=validate_authored(folder,identity,meta,paths)
 return {'status':'PASS','extras':len(items),'file_entries':files,'authored_files_verified':authored_files,'scope':'identity/dependencies/paths/receipts and authored file hashes; not native rendering quality'}

def verify(ids=None,root=EXTRAS):
 count=0;size=0;missing=[];changed=[]
 for item in entries(ids,root):
  folder=confined(root,item['folder'])
  for member in read_json(folder/'FILES.json')['files']:
   path=confined(folder,member['path'])
   if not path.is_file():missing.append(str(path.relative_to(root)));continue
   if path.stat().st_size!=member['bytes'] or sha(path)!=member['sha256']:
    changed.append(str(path.relative_to(root)));continue
   count+=1;size+=member['bytes']
 return {'status':'PASS' if not missing and not changed else 'DIFFERENCES','verified_files':count,
   'verified_bytes':size,'missing':missing,'changed':changed,'scope':'original file identities only; edited files need their own new acceptance'}

def restore(ids, cache_roots, allow_download, root=EXTRAS):
 items=entries(ids,root)
 if not cache_roots:raise ValueError('Supply an explicit --cache-root')
 sources={x['archive']:x for x in read_json(archive_inventory(root))['archives']}
 needed=set()
 for item in items:
  needed.update(x['archive'] for x in read_json(confined(root,item['folder'])/'FILES.json')['files'])
 archive_paths={}
 for cache in cache_roots:
  for path in cache.rglob('*.zip'):
   if path.name in needed and path.name not in archive_paths:archive_paths[path.name]=path
 opened={};copied=0;unchanged=0
 try:
  for name in sorted(needed):
   spec=sources[name];path=archive_paths.get(name)
   if path is None:
    if not allow_download:raise FileNotFoundError('Historical input absent from cache: '+name+'; use --download explicitly')
    url=spec['url']
    if not url.startswith('https://github.com/0xlillith/solidcraft-render-catalog/releases/download/'):
     raise ValueError('Unexpected restoration origin')
    cache_roots[0].mkdir(parents=True,exist_ok=True);path=confined(cache_roots[0],name)
    if path.exists():raise FileExistsError(path)
    partial=path.with_name(path.name+'.partial')
    if partial.exists():raise FileExistsError('Inspect unfinished download before retrying '+str(partial))
    total=0
    with urllib.request.urlopen(url,timeout=60) as src,partial.open('xb') as dst:
     while block:=src.read(1024*1024):
      total+=len(block)
      if total>spec['bytes']:raise ValueError('Download exceeds declared size')
      dst.write(block)
    if total!=spec['bytes'] or sha(partial)!=spec['sha256']:raise ValueError('Downloaded historical archive failed integrity')
    partial.replace(path)
   if path.stat().st_size!=spec['bytes'] or sha(path)!=spec['sha256']:raise ValueError('Historical input changed '+name)
   opened[name]=zipfile.ZipFile(path)
  for item in items:
   folder=confined(root,item['folder'])
   for member in read_json(folder/'FILES.json')['files']:
    dest=confined(folder,member['path'])
    if dest.exists():
     if dest.stat().st_size!=member['bytes'] or sha(dest)!=member['sha256']:
      raise FileExistsError('Refuse to overwrite your edited working file '+str(dest))
     unchanged+=1;continue
    archive=opened[member['archive']];info=archive.getinfo(member['member'])
    if info.file_size!=member['bytes']:raise ValueError('Archive member size mismatch')
    data=archive.read(info)
    if hashlib.sha256(data).hexdigest()!=member['sha256']:raise ValueError('Archive member hash mismatch')
    dest.parent.mkdir(parents=True,exist_ok=True)
    # Create-only, regular files: never share mutable inodes with another extra.
    with dest.open('xb') as output:output.write(data)
    copied+=1
  return {'status':'PASS','copied':copied,'already_identical':unchanged,'hard_links':False,'new_packs':False}
 finally:
  for archive in opened.values():archive.close()

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('action',choices=['validate','verify-files','restore'])
 parser.add_argument('--id',action='append',default=[])
 parser.add_argument('--cache-root',action='append',type=Path,default=[])
 parser.add_argument('--download',action='store_true',help='Explicitly permit restoring old archive inputs; never publishes a new pack')
 parser.add_argument('--report',type=Path)
 args=parser.parse_args()
 if args.action=='validate':result=validate()
 elif args.action=='verify-files':result=verify(args.id)
 else:result=restore(args.id,args.cache_root,args.download)
 text=json.dumps(result,indent=2,ensure_ascii=False)
 if args.report:
  if args.report.exists():raise FileExistsError('Report already exists')
  args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(text+'\n',encoding='utf-8')
 print(text[:18000])
 if result['status']!='PASS':raise SystemExit(1)
if __name__=='__main__':main()
