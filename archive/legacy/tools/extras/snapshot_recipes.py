"""Retain editable per-extra JSON recipes and original evidence in ordinary Git.

Large binary baseline copies stay in files/. No old quality claim is promoted.
Run once after migrate.py, before editing imported recipes; existing changes refuse.
"""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2];EXTRAS=ROOT/'extras'
def load(path):return json.loads(path.read_text(encoding='utf-8'))
def dump(obj):return (json.dumps(obj,indent=2,ensure_ascii=False)+'\n').encode('utf-8')
def main():
 total=0;proofs=0
 for row in load(EXTRAS/'INDEX.json')['items']:
  folder=EXTRAS/row['folder'];meta=load(folder/'extra.json');recipes=[];evidence=[]
  for member in load(folder/'FILES.json')['files']:
   relative=Path(member['path'])
   if relative.suffix!='.json' or relative.name=='reopened.json':continue
   original=folder/relative;data=original.read_bytes()
   if hashlib.sha256(data).hexdigest()!=member['sha256']:raise ValueError('Do not import an unreviewed edited baseline: '+str(original))
   data=b'\n'.join(line.rstrip(b'\r \t') for line in data.split(b'\n'))
   if not data.endswith(b'\n'):data+=b'\n'
   historical=any(word in relative.name.lower() for word in ('receipt','validation','acceptance','checksum'))
   destination=Path('provenance' if historical else 'recipes').joinpath(*relative.parts[1:])
   target=folder/destination;target.parent.mkdir(parents=True,exist_ok=True)
   if target.exists() and target.read_bytes()!=data:raise FileExistsError('Preserve edited recipe '+str(target))
   if not target.exists():target.write_bytes(data)
   (evidence if historical else recipes).append(destination.as_posix())
  meta['editable_recipes']=recipes;meta['historical_evidence']=evidence
  (folder/'extra.json').write_bytes(dump(meta));total+=len(recipes);proofs+=len(evidence)
 report={'editable_recipe_files':total,'historical_evidence_files':proofs,'scope':'original readable per-extra sources; no quality upgrade claimed'}
 (EXTRAS/'RECIPE-IMPORT.json').write_bytes(dump(report));print(json.dumps(report),flush=True)
if __name__=='__main__':main()
