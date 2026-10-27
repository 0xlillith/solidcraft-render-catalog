"""Actual SolidCraft MCP rendering matrix, exact native maps, flat/curved coupons.

Each image is a native GPU export, not a software swatch. Results demonstrate only
the explicitly executed opaque projection; advanced optics remain independently open.
"""
from __future__ import annotations
import argparse,collections,hashlib,json,math,pathlib,time
import numpy as np
from PIL import Image
from native_mcp import NativeMCP

def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def relative(value,root):
 if isinstance(value,dict):return {k:relative(v,root) for k,v in value.items()}
 if isinstance(value,list):return [relative(v,root) for v in value]
 if isinstance(value,str):
  try:
   p=pathlib.Path(value)
   if p.is_absolute() and p.is_relative_to(root):return p.relative_to(root).as_posix()
  except (ValueError,OSError):pass
 return value

def batch_fingerprint(rows,samples,cli_sha):
    files={p:digest(pathlib.Path(p)) for row in rows for p in row['maps'].values()}
    protocol={p.name:digest(p) for p in [pathlib.Path(__file__),pathlib.Path(__file__).with_name('native_mcp.py')]}
    payload={'rows':rows,'samples':samples,'cli_sha256':cli_sha,'inputs':files,'protocol':protocol}
    return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def prepare(m,rows):
 m.tool('new_design',{'name':'Native material quality - '+rows[0]['id']})
 w=max(float(r['patch_mm'][0]) for r in rows);h=max(float(r['patch_mm'][1]) for r in rows)
 scale=max(w,h);targets=[];columns=min(4,len(rows));grid_rows=math.ceil(len(rows)/columns)
 for i,row in enumerate(rows):
  width,height=map(float,row['patch_mm'][:2]);x=(i%columns-(columns-1)/2)*w*1.3;z=((grid_rows-1)/2-i//columns)*h*1.25
  depth=min(width,height)*.025;radius=min(width,height)*.19
  flat=f'{i+1:02d} {row["id"]} flat';curved=f'{i+1:02d} {row["id"]} curved'
  m.execute('solid.box',{'length':width*.94,'width':depth,'height':height*.94,'center':[x,depth/2,z],'operation':'new','body_name':flat})
  m.execute('solid.sphere',{'radius':radius,'center':[x+width*.19,-radius*1.35,z+height*.06],'operation':'new','body_name':curved})
  metal=float(row['metallic']);scalar_rough=float(row['roughness']);maps=dict(row['maps'])
  # Lossless constant-channel elimination: no quality reduction, exact metadata.
  constant_metallic=None
  if 'metallic' in maps:
   with Image.open(maps['metallic']) as im:
    a=np.asarray(im);lo,hi=int(a.min()),int(a.max())
   if lo==hi:constant_metallic=lo/255;metal=constant_metallic;del maps['metallic']
  m.execute('appearance.assign',{'bodies':[flat,curved],'color':row['color_srgb'],'pbr':{'metallic':metal,'roughness':min(1,max(.045,scalar_rough)),'dielectric_ior':row.get('dielectric_ior',1.5)}})
  targets.append({'record':row,'names':[flat,curved],'maps':maps,'constant_metallic':constant_metallic,'frame':{'origin':[x-width/2,-.001,z-height/2],'u':[width,0,0],'v':[0,0,height]}})
 scene=m.execute('render.scene',{});indices={b['name']:i for i,b in enumerate(scene['bodies'])}
 tex=[];coats=[]
 for target in targets:
  row=target['record']
  for name in target['names']:
   if target['maps']:
    t={'body_index':indices[name],'body_name':name,'frame':target['frame'],'normal_strength':row.get('normal_strength',1),'base_color_mode':row.get('base_color_mode','modulate'),'flip_v':True}
    for key,field in [('base_color','base_color_srgb'),('normal_opengl','normal_opengl'),('roughness','roughness_linear'),('metallic','metallic_linear')]:
     if key in target['maps']:t[field]=target['maps'][key]
    tex.append(t)
   coat=row.get('clearcoat')
   if coat and coat.get('weight',0)>0:coats.append({'body_index':indices[name],'body_name':name,'weight':coat['weight'],'roughness':coat['roughness'],'ior':coat['ior']})
 span=w*(1+1.3*(columns-1));scene_h=h*(1+1.25*(grid_rows-1));height_extent=max(scene_h*1.35,span*768/1024*1.13)
 camera={'target':[0,-scale*.02,0],'yaw':0,'pitch':.085,'distance':height_extent/.828427,'fov':0}
 lighting={'environment':[.36,.39,.45],'area_lights':[
  {'center':[-height_extent*1024/768/2-span*.35,-span*.65,h*.8],'u':[span*.19,0,0],'v':[0,0,-h*.5],'radiance':[20,20,20]},
  {'center':[height_extent*1024/768/2+span*.35,-span*.7,-h*.25],'u':[span*.19,0,0],'v':[0,0,-h*.5],'radiance':[14,12,10]},
  {'center':[0,-span*.5,height_extent*1.2],'u':[span*.4,0,0],'v':[0,0,-height_extent*.14],'radiance':[12,13,15]}]}
 params={'settings':{'width':1024,'height':768,'background':[22,25,32],'camera':camera,'exposure_ev':0},'progressive':True,'samples':16,'max_depth':6,'seed':270118,'lighting':lighting,'tone_map':'aces_fitted','denoise':False}
 if tex or coats:
  params['raytrace']={}
  if tex:params['raytrace']['textures']=tex
  if coats:params['raytrace']['clear_coats']=coats
 return params,targets

def check_batch(m,rows,out,index,samples):
 label=f'{index:04d}-{rows[0]["collection"]}';file=out/(label+'.png');receipt=out/(label+'.json');model=out/(label+'.solidcraft')
 fingerprint=batch_fingerprint(rows,samples,m.executable_sha256)
 if receipt.exists():
  old=json.loads(receipt.read_text(encoding='utf8'))
  if file.exists() and model.exists() and old.get('recipe_fingerprint')==fingerprint and old.get('model_sha256')==digest(model) and old.get('png_sha256')==digest(file) and old.get('ids')==[r['id'] for r in rows]:return old
  raise RuntimeError('Inconsistent existing QA receipt '+label)
 params,targets=prepare(m,rows);params['samples']=samples
 before=m.tool('measure',{});result=m.render(params,file,timeout=600)
 after=m.tool('measure',{})
 if before!=after:raise RuntimeError('Image rendering changed physical measurements')
 m.execute('render.settings.set',{'name':'Native QA','set':params['settings']|{'job':{'method':'gpu_path','options':{'samples':samples,'max_depth':6,'seed':270118,'tone_map':'aces_fitted','denoise':False,'lighting':params['lighting']}}}})
 m.tool('save',{'path':str(model)})
 # Reopen the native container and validate the exact external map recipe again.
 m.tool('open',{'path':str(model)})
 reopened=m.tool('measure',{})
 if reopened!=before:raise RuntimeError('Save/reopen changed physical measurements')
 m.execute('render.scene',{});again=m.execute('render.preflight',params)
 result.update({'recipe_fingerprint':fingerprint,'ids':[r['id'] for r in rows],'collection':rows[0]['collection'],'physical_measurements_unchanged':True,'native_container_reopen':True,'external_map_rebinding_preflight':True,'native_texture_persistence_claimed':False,'input_hashes':{path:digest(pathlib.Path(path)) for t in targets for path in t['maps'].values()},'source_appearance_projections':[{'id':r['id'],'full_optics_supported':r['full_optics_supported'],'declared_omissions':r.get('declared_omissions',[])} for r in rows],'model_sha256':digest(model),'profile':'opaque flat and curved coupons; native runtime 1K maps; not calibrated optics or UI acceptance','premium_qualified':False})
 sanitized=relative(result,m.workspace);receipt.write_text(json.dumps(sanitized,indent=2)+'\n',encoding='utf8')
 print('NATIVE_BATCH_PASS',index,len(rows),','.join(r['id'] for r in rows),result['elapsed_s'],flush=True)
 return sanitized

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--cli',type=pathlib.Path,required=True);ap.add_argument('--workspace',type=pathlib.Path,required=True);ap.add_argument('--inventory',type=pathlib.Path,required=True);ap.add_argument('--collections',required=True);ap.add_argument('--samples',type=int,default=16);ap.add_argument('--limit',type=int);ap.add_argument('--output-name',default='native-matrix');args=ap.parse_args()
 allrows=json.loads(args.inventory.read_text(encoding='utf8'))['materials'];selected=set(args.collections.split(','));rows=[r for r in allrows if r['collection'] in selected and r['full_optics_supported']]
 missing=[r['id'] for r in rows if r['collection']!='selene-baseline' and not r['maps']]
 if missing:raise SystemExit('Missing material maps: '+','.join(missing[:10]))
 rows.sort(key=lambda r:(r['collection'],tuple(r['patch_mm']),r['mapset'],r['id']))
 if args.limit:rows=rows[:args.limit]
 groups=[]
 def mapkeys(group):
  return {path for item in group for role,path in item['maps'].items() if role in ('base_color','normal_opengl','roughness')}
 for row in rows:
  key=(row['collection'],tuple(row['patch_mm']))
  # Exact map sharing permits more appearances without dropping channels or
  # reducing resolution. Six unique 1K RGBA-float maps meet the 96 MiB cap.
  can_join=bool(groups) and len(groups[-1])<12 and (groups[-1][0]['collection'],tuple(groups[-1][0]['patch_mm']))==key
  if can_join and len(mapkeys(groups[-1]+[row]))<=6:groups[-1].append(row)
  else:groups.append([row])
 out=args.workspace/args.output_name;out.mkdir(exist_ok=True)
 run={'cli_version':subprocess_version(args.cli),'cli_sha256':digest(args.cli),'samples':args.samples,'requested_materials':len(rows),'groups':len(groups),'receipts':[],'failures':[]}
 print('NATIVE_MATRIX_BEGIN',run['cli_version'],len(rows),len(groups),flush=True)
 with NativeMCP(args.cli,args.workspace) as m:
  print('NATIVE_MCP_READY',m.server,flush=True)
  for i,group in enumerate(groups):
   try:run['receipts'].append(check_batch(m,group,out,i,args.samples))
   except Exception as error:
    failure={'group':i,'ids':[r['id'] for r in group],'error':str(error)};run['failures'].append(failure)
    print('NATIVE_BATCH_FAIL',json.dumps(failure)[:1200],flush=True)
    if len(run['failures'])>=3:break
   checkpoint={'cli_version':run['cli_version'],'cli_sha256':run['cli_sha256'],'requested':run['requested_materials'],'passed':sum(len(r['ids']) for r in run['receipts']),'failed':sum(len(f['ids']) for f in run['failures']),'batch_count':len(run['receipts']),'failures':run['failures']}
   (out/'progress.json').write_text(json.dumps(checkpoint,indent=2),encoding='utf8')
  (out/'summary.json').write_text(json.dumps({'cli_version':run['cli_version'],'cli_sha256':run['cli_sha256'],'requested':len(rows),'passed_ids':[identity for r in run['receipts'] for identity in r['ids']],'failures':run['failures'],'premium_qualified':False,'executed_scope':'GPU flat/curved opaque images + native container reopen + measurement invariance + exact map recapture preflight'},indent=2),encoding='utf8')
 print('NATIVE_MATRIX_DONE',len(rows),sum(len(r['ids']) for r in run['receipts']),'passed',len(run['failures']),'failed groups',flush=True)
 if run['failures'] or sum(len(r['ids']) for r in run['receipts'])!=len(rows):raise SystemExit(1)
def subprocess_version(cli):
 import subprocess
 return subprocess.check_output([str(cli),'--version'],text=True).strip()
if __name__=='__main__':main()
