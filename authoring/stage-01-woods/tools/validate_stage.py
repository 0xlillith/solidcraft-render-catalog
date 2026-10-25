"""Validate authoring records and generated files, not native or physical fidelity."""
from pathlib import Path
import hashlib, json, math, struct, zlib
A=Path(__file__).resolve().parents[1]
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''): h.update(b)
 return h.hexdigest()
def check_png(p):
 b=p.read_bytes()
 if b[:8]!=b'\x89PNG\r\n\x1a\n': raise ValueError('PNG signature')
 pos=8;head=None;parts=[];srgb=False;ended=False
 while pos<len(b):
  if pos+12>len(b): raise ValueError('truncated chunk')
  n=struct.unpack('>I',b[pos:pos+4])[0];t=b[pos+4:pos+8];v=b[pos+8:pos+8+n]
  if pos+12+n>len(b): raise ValueError('truncated payload')
  if zlib.crc32(t+v)&0xffffffff != struct.unpack('>I',b[pos+8+n:pos+12+n])[0]: raise ValueError('CRC')
  if t==b'IHDR':
   if head is not None or pos!=8 or n!=13: raise ValueError('IHDR')
   head=struct.unpack('>IIBBBBB',v)
  elif t==b'IDAT': parts.append(v)
  elif t==b'sRGB': srgb=True
  elif t==b'IEND':
   if n or pos+12!=len(b): raise ValueError('IEND')
   ended=True
  pos+=n+12
 if head is None or not ended: raise ValueError('incomplete PNG')
 w,h,depth,color,compression,filter_method,interlace=head
 if depth not in (8,16) or color not in (0,2) or compression or filter_method or interlace: raise ValueError('PNG representation')
 channels=1 if color==0 else 3;stride=w*channels*depth//8
 raw=zlib.decompress(b''.join(parts))
 if len(raw)!=(stride+1)*h or any(raw[y*(stride+1)]!=1 for y in range(h)): raise ValueError('PNG decompression/filters')
 return dict(width=w,height=h,channels=channels,bit_depth=depth,color_space='sRGB' if srgb else 'linear_data',bytes=len(b))
def main():
 profiles=read(A/'data/physical-profiles.json')['profiles'];woods=read(A/'data/woods.json');finishes=read(A/'data/finishes.json')['finishes'];variants=read(A/'data/material-variants.json')['items'];table=read(A/'data/wood-table-transcription.json');sources=read(A/'data/sources.json')
 assert len(profiles)==16 and len(variants)==384
 ids={p['id'] for p in profiles};assert len(ids)==16 and len({v['id'] for v in variants})==384
 raw={r['name']:dict(zip(table['columns'],r['values'])) for r in table['rows']};missing=0
 for p in profiles:
  assert p['moisture_dry_basis_kg_kg']==.12 and 'not_complete_constitutive_model' in p['model']
  for prop in p['properties'][:-1]:
   q=prop['quantity'];v=raw[p['name']][q];assert prop['original']['value']==v and prop['source_id'] in sources
   factor=1e6 if q.endswith('_mpa') else 1000 if q.endswith(('_kpa','_kj_m3')) else .001 if q.endswith('_mm') else 1
   assert prop['value']==(None if v is None else v*factor)
   assert prop['conditions']['structural_design_allowable'] is False and prop['uncertainty'] is None
   if v is None: missing+=1;assert prop['status']=='not_reported'
  assert math.isclose(p['properties'][-1]['value'],1120*raw[p['name']]['specific_gravity_g12'],abs_tol=1e-6)
 assert missing==2 and raw['White ash']['bending_mor_kpa']==106000
 for v in variants:
  assert v['physical_profile_id'] in ids and v['appearance']['wrap']=='clamp_to_edge' and v['appearance']['seamless'] is False
  assert v['plugin_contract'] is None and v['auto_assign_physical_material'] is False
  assert v['quality']['native_visual_acceptance']=='not_run' and v['quality']['physical_model_certified'] is False
  assert all(0<=x<=1 for x in v['appearance']['color_multiplier_linear'])
 index=read(A/'build/map-index.json');assert index['resolution']==2048 and index['mapsets']==64
 expected={(w['id'],cut) for w in woods['woods'] for cut in woods['cuts']};seen=set();maps=0;previews=0;hashes=[]
 for r in index['records']:
  species,cut=r['id'].split('/');seen.add((species,cut));folder=A/'build/maps'/species/cut
  assert read(folder/'map-contract.json')==r and r['wrap']=='clamp_to_edge' and r['seamless'] is False
  for tier,size in [('master-2048',2048),('runtime-1024',1024)]:
   assert set(r['sets'][tier])=={'base_color','normal_opengl','normal_directx','orm','roughness','height_mm_u16'}
   for role,receipt in r['sets'][tier].items():
    p=folder/tier/(role+'.png');facts=check_png(p);h=digest(p)
    assert h==receipt['sha256'] and facts['width']==facts['height']==size
    assert all(receipt[k]==v for k,v in facts.items())
    assert (role=='height_mm_u16')==(facts['bit_depth']==16) and (role=='base_color')==(facts['color_space']=='sRGB')
    maps+=1;hashes.append((p.relative_to(A).as_posix(),h))
  for finish in finishes:
   p=A/'build/previews'/species/cut/(finish['id']+'.png');f=check_png(p)
   assert f['width']==240 and f['height']==(240 if cut=='end-grain' else 360) and f['color_space']=='sRGB'
   previews+=1;hashes.append((p.relative_to(A).as_posix(),digest(p)))
 assert seen==expected and maps==768 and previews==384
 assert len({h for p,h in hashes if p.endswith('/master-2048/base_color.png')})==64
 result={'status':'PASS','species':16,'material_variants':384,'mapsets':64,'map_images_checked':maps,'preview_images_checked':previews,'native_acceptance':'NOT_RUN','premium_qualification':'NOT_QUALIFIED','plugin_standard_defined':False,'scope':'Source-table/SI/density/identity checks, independent PNG CRC/decompression, file hashes, dimensions, color roles and complete coverage.'}
 (A/'reports').mkdir(exist_ok=True)
 (A/'reports/validation.json').write_text(json.dumps(result,indent=2)+'\n')
 (A/'reports/generated-images.sha256').write_text(''.join(h+'  '+p+'\n' for p,h in sorted(hashes)))
 print(json.dumps(result))
if __name__=='__main__': main()
