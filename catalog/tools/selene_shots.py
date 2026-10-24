"""Save all twelve authored SELENE shot intents on the licensed native source.
Semantic sub-part framing that has no reviewed selector remains an explicitly named
whole-rover framing study, never an invented role binding or certified mission scene.
"""
from core import *
from mcp_client import Client
from lighting import build_recipe,sunlight
import shutil,math,time

if __name__=='__main__':
    upstream=Path(r'D:\SolidCraft\source-main-9e6e0b8d');src=upstream/'assets/render/selene'
    for rel in ['SOURCE.md','source-lock.json','source/SELENE-showcase.solidcraft','models/SELENE-functional.solidcraft']:
        p=src/rel
        if p.exists():q=ROOT/'source/assets/render/selene'/rel;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
    shots=load(ROOT/'source/assets/render/selene/scenes/shots.json')['items'];folder=ROOT/'setups/SELENE-SHOTS';folder.mkdir(exist_ok=True);records=[];errors=[]
    with Client(gpu=False) as c:
        c.execute('doc.open',{'path':str(ROOT/'source/assets/render/selene/models/SELENE-functional.solidcraft')})
        targets=c.execute('render.library.targets');lo=np.array(targets['bounds']['min']);hi=np.array(targets['bounds']['max']);center=(lo+hi)/2;extent=float(np.max(hi-lo));corners=np.array([[x,y,z] for x in [lo[0],hi[0]] for y in [lo[1],hi[1]] for z in [lo[2],hi[2]]]);dump(folder/'native-source-bounds.json',targets)
        for shot in shots:
            try:
                sid=shot['id'];cam=shot['camera'];az=cam['view_from_target']['azimuth_rad'];el=cam['view_from_target']['elevation_rad'];target=center+np.array(cam['target_position_mm']['offset_mm']);back=np.array([np.cos(el)*np.cos(az),np.cos(el)*np.sin(az),np.sin(el)]);right=np.array([-np.sin(az),np.cos(az),0]);up=np.cross(back,right);delta=corners-target;fov=cam['vertical_fov_rad'];fill=cam['frame_fill_fraction'];tangent=np.tan(fov/2);aspect=1.5
                distance=float(np.max(delta@back+np.maximum(np.abs(delta@right)/(tangent*aspect*fill),np.abs(delta@up)/(tangent*fill)))+extent*.04)
                solar=sunlight(45+int(sid.rsplit('-',1)[-1])*11,7+int(sid.rsplit('-',1)[-1])*2,14000);lighting={'environment':[0,0,0],'area_lights':[]}
                ownership=shot.get('source_ownership',{});limits=[]
                if ownership.get('sun') not in ('disabled','none',False):lighting['sun']=solar
                role=cam['target_role_id'];fallback=role!='rover_assembly'
                if fallback:limits.append('No reviewed geometry selector for '+role+'; this saved setup is explicitly whole-rover framing, not a semantic close-up.')
                if shot.get('sequence',{}).get('kind') not in ('none',None):limits.append('Static initial shot only. Motion/pose/time sequence remains in the unchanged source recipe.')
                if ownership.get('subject_leds')!='disabled':limits.append('Subject LED roles are not automatically bound; no fabricated photometry or emitter placement is enabled.')
                limits+=['Lunar terrain/stage and material-role assignment are separate assets, not silently inserted into the original rover.','Solar direction is an authored relative lighting choice, not a site ephemeris.']
                name=sid+(' Whole-rover framing study' if fallback else ' '+shot['name'])
                setting={'width':960,'height':640,'background':[0,0,0],'exposure_ev':cam['exposure']['initial_ev'],'camera':{'target':target.tolist(),'yaw':az+np.pi/2,'pitch':el,'roll':cam.get('roll_rad',0),'distance':distance,'fov':fov,'up':'z'},'job':{'method':'gpu_path','options':{'samples':128,'max_depth':12,'seed':610000+int(sid.rsplit('-',1)[-1]),'lighting':lighting,'tone_map':'aces_fitted','linear_exr':True}}}
                c.execute('render.settings.set',{'name':name,'set':setting});p=folder/sid;p.mkdir(exist_ok=True);dump(p/'shot.json',{'id':sid,'name':shot['name'],'original_specification':shot,'native_setup_name':name,'native_setup':setting,'role_binding':'whole_rover_only','limitations':limits,'native_source_sha256':sha(ROOT/'source/assets/render/selene/models/SELENE-functional.solidcraft')});records.append({'id':sid,'name':shot['name'],'kind':'shot','family':'SELENE shots','path':p.relative_to(ROOT).as_posix(),'native':'setups/SELENE-SHOTS/SELENE-catalog-shots.solidcraft','generated':True,'limitations':limits})
            except Exception as e:errors.append({'id':shot['id'],'error':str(e)})
        c.execute('file.save',{'path':str(folder/'SELENE-catalog-shots.solidcraft'),'cache':False,'preview':False})
    dump(folder/'index.json',{'items':records});dump(ROOT/'reports/selene-shots.json',{'status':'PASS' if len(records)==12 and not errors else 'FAIL','count':len(records),'expected':12,'errors':errors,'geometry_and_pose_changed':False,'source_unchanged':True,'scope':'All shot recipes plus saved whole-rover framing studies; sub-role, stage and sequence limitations remain explicit.'});print('SELENE_SHOTS',len(records),'errors',errors,flush=True)
