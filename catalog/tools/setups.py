"""Resolve source setup cross-references into local buildable compositions.
Full quality/role intent stays beside explicitly bounded current-engine projections.
These samples do not mutate, resize or guess semantic roles in a user's design.
"""
from core import *
from lighting import build_recipe,sunlight
import subprocess,shutil,time,traceback
CLI=load(ROOT/'build.json')['native_cli']


def bounded_quality(q):
    original=copy.deepcopy(q);samp=int(q['sampling']['maximum_samples']);depth=int(q['transport']['maximum_depth']);w=int(q['resolution']['width']);h=int(q['resolution']['height']);limits=[]
    if samp>4096:limits.append('Original sample ceiling exceeds native 4096; the separate bounded projection uses 4096.')
    if depth>16:limits.append('Original path depth exceeds native 16; the separate bounded projection uses 16.')
    if q.get('motion',{}).get('enabled'):limits.append('No camera-time integration is installed by this static native projection. Full motion intent is retained.')
    limits+=['Native fixed sampling does not assert the original convergence/error estimator.','Quality specification is a target, not a measured guarantee for every scene.']
    opts={'samples':min(samp,4096),'max_depth':min(depth,16),'seed':q.get('seed',21026),'tone_map':'aces_fitted','denoise':False,'linear_exr':q.get('output',{}).get('master')=='linear_exr'}
    return {'id':q['id'],'name':q['name'],'original_specification':original,'native_projection':{'width':w,'height':h,'format':'png','job':{'method':'gpu_path','options':opts}},'limitations':limits,'authoring_status':'generated_projection_with_explicit_limits','full_quality_acceptance':False}


def command_run(path,commands,out=None):
    dump(path,commands);args=[CLI,'run',str(path),'--quiet']
    if out:args+=['--save',str(out)]
    p=subprocess.run(args,capture_output=True,text=True,encoding='utf-8',timeout=180)
    if p.returncode:raise RuntimeError((p.stdout+p.stderr)[-3000:])


def create_light_native(item):
    rid=item['id'];f=ROOT/'lighting'/rid;r=load(f/'rig.json')
    cmd=[{'command':'file.new','params':{'name':rid+' '+item['name']}},{'command':'document.metadata.set','params':{'values':{'license':LICENSE,'description':'Original relative lighting rig on neutral calibration geometry; no photometric certification.','org.solidcraft.local_catalog':{'id':rid,'unresolved_external_inputs':r['unresolved_external_inputs'],'limitations':r['limitations']}}}},{'command':'solid.sphere','params':{'radius':160,'center':[0,0,0],'body_name':'Reference subject'}},{'command':'appearance.assign','params':{'bodies':['Reference subject'],'color':[155,155,155],'pbr':{'metallic':0,'roughness':.4,'dielectric_ior':1.5}}}]
    base={'width':640,'height':480,'camera':{'target':[0,0,0],'yaw':-.7,'pitch':.35,'roll':0,'distance':1150,'fov':.7,'up':'z'},'background':[30,35,42],'job':{'method':'gpu_path','options':{'samples':128,'max_depth':8,'seed':r['seed'],'tone_map':'aces_fitted'}}}
    if len(r['lights']['area_lights'])<=4:
        base['job']['options']['lighting']=r['lights'];base['stage']=r['passive_stage'];name=rid+' '+item['name'];cmd.append({'command':'render.settings.set','params':{'name':name,'set':base}})
    else:
        name=rid+' [reference-origin HDR projection]';base['job']['options']['lighting']={'environment':[0,0,0],'area_lights':[]}
        cmd.append({'command':'render.settings.capture_hdr','params':{'name':name,'set':base,'path':str(f/'reference-origin.hdr'),'expected_sha256':sha(f/'reference-origin.hdr'),'rotation_rad':float(np.pi),'intensity':1,'assume_linear_srgb':False}})
    command_run(f/'solidcraft-build.json',cmd,f/'rig.solidcraft')
    return {'id':rid,'native':(f/'rig.solidcraft').relative_to(ROOT).as_posix(),'status':'PASS','full_rig_direct':len(r['lights']['area_lights'])<=4,'conditional':r['unresolved_external_inputs']}


def create_scene(item,environment,lighting,quality,source_kind):
    rid=item['id'];f=ROOT/'setups'/rid;f.mkdir(exist_ok=True);envpath=ROOT/'environments'/environment
    deadline=time.monotonic()+1200
    while not (envpath/'environment.json').exists():
        if time.monotonic()>deadline:raise TimeoutError(environment)
        time.sleep(1)
    env=load(envpath/'environment.json');support=env['geometry_summary']['suggested_subject_support_mm'];size=min(500.,env['geometry_summary']['extent_mm']*.08);num=int(rid.rsplit('-',1)[-1]);r=load(ROOT/'lighting'/lighting/'rig.json');q=bounded_quality(quality)
    # A dedicated, explicitly labelled demonstration subject, never a substitute for the user's real role mapping.
    roles=item.get('appearance_bindings',{'product_finish':'MAT-031','reference_metal':'MAT-001','reference_polymer':'MAT-051'});commands=[{'command':'file.new','params':{'name':rid+' '+item['name']}},{'command':'file.insert_mesh','params':{'path':str(envpath/'environment.glb'),'up':'y','name':environment+' Context'}},{'command':'document.metadata.set','params':{'values':{'license':LICENSE,'project':'Original local Render composition','org.solidcraft.local_catalog':{'id':rid,'source_kind':source_kind,'environment':environment,'lighting':lighting,'quality':quality['id'],'original_role_assignments_preserved':True,'demo_subjects_are_not_user_geometry':True}}}}]
    bindings=[]
    for index,(role,mid) in enumerate(roles.items()):
        if index>=8:break
        matpath=ROOT/'materials'/mid/'material.json'
        if not matpath.exists():continue
        native=load(matpath.parent/'native-appearance.json')['params'];body='Demo '+role
        commands.append({'command':'solid.box','params':{'length':size*.65,'width':size*.65,'height':size*.65,'corner':[(index-1)*size*.9,-size/2,support+1],'body_name':body}})
        native['bodies']=[body];commands.append({'command':'appearance.assign','params':native});bindings.append({'role':role,'material':mid,'demo_body':body,'appearance_variant':'uniform_native_projection'})
    opts={'samples':128,'max_depth':8,'seed':910000+num,'tone_map':'aces_fitted','linear_exr':True};bg=[28,33,41];solar=env['radiance']['analytic_sun'];vacuum=int(environment.split('-')[1])>=241
    if vacuum:
        opts['lighting']={'environment':[0,0,0],'area_lights':r['lights'].get('area_lights',[])[:4]}
        if solar:opts['lighting']['sun']=solar
        bg=[0,0,0]
    else:opts['lighting']={'environment':[0,0,0],'area_lights':r['lights']['area_lights'][:4]}
    # If a rig contains more than four emitters, native projection is clearly named and retains the exact complete rig externally.
    limitations=['Demo objects are placeholders for explicit user roles; no user selection is guessed.','Native looks are the uniform projection, not an assertion that custom texture maps persisted.']
    if len(r['lights']['area_lights'])>4:limitations.append('Native demonstration contains the first four explicit emitters; use the complete rig.json or its separately labelled HDR projection for the full source arrangement.')
    # The authored environment is the energy owner for its panorama patches. The native composition
    # deliberately uses the explicit rig and a neutral/black environment rather than double-counting those patches.
    setup={'width':960,'height':640,'background':bg,'exposure_ev':-1 if not vacuum else 0,'camera':{'target':[0,0,support+size*.4],'yaw':-.6,'pitch':.35,'roll':0,'distance':size*4.5,'fov':.7,'up':'z'},'job':{'method':'gpu_path','options':opts}}
    commands.append({'command':'render.settings.set','params':{'name':rid+' Authoring Preview','set':setup}})
    high=copy.deepcopy(setup);high.update(q['native_projection']);high['job']['options']['lighting']=opts['lighting'];high['camera']=setup['camera'];high['background']=bg;high['exposure_ev']=setup['exposure_ev'];commands.append({'command':'render.settings.set','params':{'name':rid+' Bounded Quality','set':high}})
    recipe={'id':rid,'name':item['name'],'source_kind':source_kind,'original_specification':item,'resolved_environment_id':environment,'resolved_lighting_id':lighting,'resolved_quality':q,'demo_role_bindings':bindings,'native_setup':setup,'limits':limitations+q['limitations'],'energy_ownership':'Explicit rig owns illumination in the demo; exported HDR remains an alternative, not an additive duplicate.','full_original_scene_acceptance':False}
    dump(f/'setup.json',recipe);command_run(f/'solidcraft-build.json',commands,f/'setup.solidcraft')
    if (envpath/'preview.png').exists():shutil.copy2(envpath/'preview.png',f/'preview.png')
    return {'id':rid,'name':item['name'],'family':source_kind,'kind':'setup','path':f.relative_to(ROOT).as_posix(),'thumbnail':f.relative_to(ROOT).as_posix()+'/preview.png','generated':True,'native_status':'created','limitations':limitations}


def main():
    quality=load(SOURCE/'quality-presets.json')['items'];qmap={x['id']:x for x in quality};results=[];errors=[]
    for q in quality:
        r=bounded_quality(q);f=ROOT/'quality'/q['id'];f.mkdir(exist_ok=True);dump(f/'quality.json',r);dump(f/'solidcraft-bounded-settings.json',r['native_projection'])
        dump(f/'external-render-target.json',{'samples':q['sampling']['maximum_samples'],'max_bounces':q['transport']['maximum_depth'],'resolution':q['resolution'],'motion':q['motion'],'original_specification':q,'validation':'Not executed; target capability-dependent'})
    dump(ROOT/'quality/index.json',{'items':[{'id':x['id'],'name':x['name'],'kind':'quality','family':'Quality targets','path':'quality/'+x['id'],'generated':True,'native_projection':'explicit bounded variant'} for x in quality]})
    # All lighting files get a native sample even when a conditional source is off by design.
    for i,item in enumerate(load(SOURCE/'lighting.json')['items']):
        try:results.append(create_light_native(item))
        except Exception as e:errors.append({'id':item['id'],'error':str(e),'trace':traceback.format_exc()})
        if (i+1)%40==0:print('NATIVE_LIGHTS',i+1,'errors',len(errors),flush=True)
    dump(ROOT/'reports/native-lighting.json',{'status':'PASS' if not errors else 'FAIL','count':len(results),'expected':280,'results':results,'errors':errors})
    envsets={x['id']:x for x in load(SOURCE/'environment-presets.json')['items']};studios={x['id']:x for x in load(SOURCE/'studio-presets.json')['items']};setups=[]
    collections=[('scene',load(SOURCE/'scene-presets.json')['items']),('studio',list(studios.values())),('environment setup',list(envsets.values()))]
    for kind,items in collections:
        for item in items:
            try:
                if kind=='scene':env=envsets[item['environment_preset_id']]['catalog_id'];light=studios[item['studio_preset_id']]['catalog_id'];q=qmap[item['quality_preset_id']]
                elif kind=='studio':env='ENV-251' if 'lunar' in item.get('mode','') else 'ENV-001';light=item['catalog_id'];q=quality[1]
                else:env=item['catalog_id'];light='LUZ-261' if 'lunar' in item.get('mode','') else 'LUZ-001';q=quality[1]
                setups.append(create_scene(item,env,light,q,kind))
            except Exception as e:errors.append({'id':item['id'],'error':str(e),'trace':traceback.format_exc()})
        print('SETUPS',kind,len(setups),'errors',len(errors),flush=True)
    dump(ROOT/'setups/index.json',{'items':setups});dump(ROOT/'reports/setup-generation.json',{'status':'PASS' if not errors else 'FAIL','count':len(setups),'expected':72,'errors':errors})
    if errors:raise RuntimeError(errors[:3])
if __name__=='__main__':main()
