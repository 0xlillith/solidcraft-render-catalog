"""Build native scalar-look samples and genuine v2 libraries with the installed CLI.
Texture maps and advanced optics remain explicit external resources/recipes: a v2
appearance library cannot encode them, and no false persistence claim is made.
"""
from core import *
import subprocess,time,traceback
CLI=Path(load(ROOT/'build.json')['native_cli'])

def run_script(path,commands,save=None):
    dump(path,commands);args=[str(CLI),'run',str(path),'--quiet']
    if save:args+=['--save',str(save)]
    p=subprocess.run(args,capture_output=True,text=True,encoding='utf-8',timeout=120)
    if p.returncode:raise RuntimeError((p.stdout+p.stderr)[-4000:])
    return p

def look_params(r,body):
    p=load(ROOT/'materials'/r['id']/'native-appearance.json')['params'];p['bodies']=[body];return p

def sample_commands(r):
    folder=ROOT/'materials'/r['id'];p=look_params(r,'Specimen')
    limitations=r['limitations']+['This native sample stores the uniform PBR approximation only. Use the portable glTF and external runtime-map request for richer fields.','The displayed Default material is not a measured density assigned by this catalogue.']
    return [{'command':'file.new','params':{'name':r['id']+' '+r['name']}},{'command':'document.metadata.set','params':{'values':{'project':'Local render resource catalog','license':LICENSE,'description':'Uniform native appearance specimen; richer authored maps/optics stored beside it.','org.solidcraft.local_catalog':{'id':r['id'],'recipe':'material.json','limitations':limitations,'physical_material_assigned':False}}}},{'command':'solid.box','params':{'body_name':'Specimen','length':80,'width':80,'height':8,'corner':[-40,-40,-4]}},{'command':'appearance.assign','params':p},{'command':'render.settings.set','params':{'name':'Uniform material preview','set':{'width':640,'height':480,'camera':{'target':[0,0,0],'yaw':-.75,'pitch':.55,'roll':0,'distance':180,'fov':.6,'up':'z'},'job':{'method':'gpu_path','options':{'samples':64,'max_depth':8,'seed':r['seed'],'tone_map':'aces_fitted'}}}}}]

def main():
    rows=load(ROOT/'materials/index.json')['items'];assert len(rows)==600
    out=[];errors=[];start=time.time()
    for group_start in range(0,600,10):
        group=rows[group_start:group_start+10];batch=[]
        for row in group:
            r=load(ROOT/row['path']/'material.json');cmd=sample_commands(r);dump(ROOT/row['path']/'solidcraft-build.json',cmd)
            batch+=cmd+[{'command':'file.save','params':{'path':str(ROOT/row['path']/'material.solidcraft'),'cache':False,'preview':False}}]
        path=ROOT/'native'/('material-batch-%02d.json'%(group_start//10+1))
        try:run_script(path,batch)
        except Exception as e:errors.append({'batch':group_start//10+1,'error':str(e)});print('NATIVE_MATERIAL_ERROR',str(e),flush=True);continue
        commands=[{'command':'file.new','params':{'name':'Material family '+group[0]['family']}},{'command':'document.metadata.set','params':{'values':{'license':LICENSE,'description':'Original visual appearances only. Uniform fallbacks are named; no physical densities are assigned.'}}}]
        for j,row in enumerate(group):
            r=load(ROOT/row['path']/'material.json');commands +=[{'command':'solid.box','params':{'body_name':r['id'],'length':30,'width':30,'height':6,'corner':[j*40,0,0]}},{'command':'appearance.assign','params':look_params(r,r['id'])}]
        dest=ROOT/'libraries'/('materials-family-%02d.json'%(group_start//10+1))
        commands +=[{'command':'library.export','params':{'path':str(dest),'id':'local.materials.family%02d'%(group_start//10+1),'name':group[0]['family'],'provenance':{'license':LICENSE,'author':'Original SolidCraft contributors; local catalog authoring','source_url':'https://github.com/tangency-labs/solidcraft'},'format':'solidcraft-library/2'}}]
        try:
            run_script(ROOT/'native'/('library-batch-%02d.json'%(group_start//10+1)),commands)
            catalog=load(dest);out.append({'family':group[0]['family'],'library':dest.relative_to(ROOT).as_posix(),'count':len(group),'native_samples':len(group),'format':catalog['format']})
        except Exception as e:errors.append({'family':group[0]['family'],'error':str(e)})
        if len(out)%5==0:dump(ROOT/'reports/native-material-progress.json',{'families':len(out),'samples':len(out)*10,'errors':errors});print('NATIVE_MATERIALS',len(out)*10,'errors',len(errors),flush=True)
    dump(ROOT/'libraries/index.json',{'items':out});dump(ROOT/'reports/native-materials.json',{'status':'PASS' if not errors else 'FAIL','families':len(out),'samples':sum(x['native_samples'] for x in out),'errors':errors,'seconds':time.time()-start,'scope':'Native creation and v2 export; uniform-PBR fields only, no claim of advanced texture persistence.'})
    if errors:raise RuntimeError(errors[:3])
if __name__=='__main__':main()
