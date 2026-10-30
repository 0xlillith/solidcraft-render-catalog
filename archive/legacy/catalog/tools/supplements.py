"""Native optional collections, optical studies and conserved physical references.
All native authoring goes through the actual headless command registry in a private session.
"""
from core import *
from mcp_client import Client
import shutil,subprocess,importlib.util,time,traceback


def save(c,path):return c.execute('file.save',{'path':str(path),'cache':False,'preview':False})
def box(c,name='Specimen'):
    c.execute('solid.box',{'body_name':name,'length':80,'width':80,'height':8,'corner':[-40,-40,-4]})
def setup(c,name='Studio'):
    c.execute('render.settings.set',{'name':name,'set':{'width':640,'height':480,'camera':{'target':[0,0,0],'yaw':-.7,'pitch':.4,'roll':0,'distance':200,'fov':.7,'up':'z'},'job':{'method':'gpu_path','options':{'samples':128,'max_depth':8,'seed':21026,'tone_map':'aces_fitted'}}}})


def physical_export():
    tools=ROOT/'source/assets/render/physical/tools';sys.path.insert(0,str(tools));spec=importlib.util.spec_from_file_location('physical_export_original',tools/'export_library.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    plan=mod.selection(None,True);folder=ROOT/'libraries/physical-references';folder.mkdir(exist_ok=True);dump(folder/'export-plan.json',plan)
    cmds=[{'command':'file.new','params':{'name':'Physical references - choose identity and conditions'}}]+[row['command'] for row in plan['materials']]+[mod.library_command(folder/'physical-reference-library.json')]
    dump(folder/'create.json',cmds);cli=load(ROOT/'build.json')['native_cli'];p=subprocess.run([cli,'run',str(folder/'create.json'),'--save',str(folder/'reference-materials.solidcraft'),'--quiet'],capture_output=True,text=True)
    if p.returncode:raise RuntimeError(p.stderr[-3000:])
    catalog=load(folder/'physical-reference-library.json');mod.verify_catalog(catalog,plan)
    command=mod.library_command(folder/'cold-reopened-library.json');dump(folder/'reopen.json',[command]);p=subprocess.run([cli,'run',str(folder/'reopen.json'),'--in',str(folder/'reference-materials.solidcraft'),'--quiet'],capture_output=True,text=True)
    if p.returncode:raise RuntimeError(p.stderr[-3000:])
    cold=load(folder/'cold-reopened-library.json');mod.verify_catalog(cold,plan);assert cold==catalog
    cards=load(ROOT/'source/assets/render/physical/exports/native-cards.json')['items'];reference_rows=[]
    for card in cards:
        path=folder/'cards'/card['profile_id'];path.mkdir(parents=True,exist_ok=True);dump(path/'native-card.json',card['card']);dump(path/'projection-record.json',card)
        reference_rows.append({'id':card['profile_id'],'name':card['card']['designation'],'family':card['card']['family'],'kind':'physical_reference','path':path.relative_to(ROOT).as_posix(),'native_supported_properties':len(card['card']['properties']),'reference_selection_required':True})
    dump(folder/'index.json',{'items':reference_rows});return {'native_materials':len(plan['materials']),'reference_profiles':len(cards),'cold_reopen_equal':True,'omitted':plan['omitted'],'no_appearance_or_body_assignment':True}


def main():
    results={'optical_studies':[],'native_studios':[],'selene_appearances':[],'quality':[]};errors=[];start=time.time()
    # Complete 600-entry library from exact native-exported definitions/revisions.
    master={'format':'solidcraft-library/2','id':'local.complete-materials','name':'Complete 600 visual appearances - uniform native projections','entries':[]}
    for p in sorted((ROOT/'libraries').glob('materials-family-*.json')):
        for entry in load(p)['entries']:
            entry=copy.deepcopy(entry);entry['id']=master['id']+'/'+entry['id'].split('/')[-1];master['entries'].append(entry)
    assert len(master['entries'])==600 and len({x['id'] for x in master['entries']})==600;dump(ROOT/'libraries/all-600-native-appearances.json',master)
    with Client(gpu=False) as c:
        inspected=c.execute('library.inspect',{'path':str(ROOT/'libraries/all-600-native-appearances.json')});assert inspected['catalog']==master
        results['master_library']={'entries':600,'native_inspection':True,'revisions':'retained verbatim from actual native family exports'}
        # Exact stable targeting via the engine, not guessed ordinals/revisions.
        for row in load(ROOT/'materials/index.json')['items']:
            r=load(ROOT/row['path']/'material.json')
            if not r['transmission']:continue
            try:
                f=ROOT/row['path'];c.execute('doc.open',{'path':str(f/'material.solidcraft')});targets=c.execute('render.library.targets');assert targets['total']==1 and targets['items'][0]['name']=='Specimen'
                col=np.clip((np.array(r['base_linear_low'])+r['base_linear_high'])/2,.005,1);trans=np.clip(col/max(float(col.max()),.01)*.96,.01,.999);sigma=(-np.log(trans)/10).tolist()
                params={'name':'Uniform material preview','body_index':targets['items'][0]['ordinal'],'body_name':'Specimen','expected_revision':targets['revision'],'optics':{'ior':r['ior'],'absorption_per_mm':sigma,'boundary':'closed_box','thickness_mm':0.,'shadow_transmission':True}}
                c.execute('render.optics.bind',params)
                c.execute('document.metadata.set',{'values':{'description':'Smooth closed-slab optical study, not the full rough/thin/spectral material.','org.solidcraft.optical_study':{'physical_geometry':'80 x 80 x 8 mm closed slab','ior':r['ior'],'absorption_per_mm':sigma,'basis':'authored RGB transmission at 10 mm, not measured','omitted':['rough transmission','wave/spectral effects','thin-film interference','geometry-specific surface structure']}}})
                save(c,f/'optical-study.solidcraft');dump(f/'native-optics-binding-example.json',{'command':'render.optics.bind','params':params,'replay_note':'Expected revision/body identity must be resolved again in the destination design.'});results['optical_studies'].append(r['id'])
            except Exception as e:errors.append({'id':r['id'],'stage':'native optics','error':str(e)})
        print('OPTICAL_STUDIES',len(results['optical_studies']),'errors',len(errors),flush=True)
        entries=c.execute('render.library.list',{'kind':'native_scenes','limit':128})['items']
        for item in entries:
            rid=item['id'];f=ROOT/'setups'/rid;f.mkdir(exist_ok=True)
            try:
                c.execute('file.new',{'name':rid+' '+item['name']});box(c);setup(c);rev=c.execute('render.library.targets')['revision'];plan=c.execute('render.preset.resolve',{'id':rid,'name':'Studio','expected_revision':rev});c.execute('render.preset.apply',{'id':rid,'name':'Studio','expected_revision':rev,'replace_lighting_and_environment':True});save(c,f/'setup.solidcraft');dump(f/'native-preset.json',{'entry':item,'resolved_plan':plan})
                results['native_studios'].append({'id':rid,'name':item['name'],'family':'Original native studios','kind':'setup','path':f.relative_to(ROOT).as_posix(),'generated':True,'native_status':'builtin resolve/apply/save executed'})
            except Exception as e:errors.append({'id':rid,'stage':'native studio','error':str(e)})
        print('ORIGINAL_NATIVE_STUDIOS',len(results['native_studios']),'errors',len(errors),flush=True)
        c.execute('file.new',{'name':'SELENE uniform appearance library'})
        ap=load(ROOT/'source/assets/render/selene/materials/appearance-pack.json')['items']
        for i,item in enumerate(ap):
            rid=item['id'];f=ROOT/'materials'/rid;f.mkdir(exist_ok=True)
            try:
                values=copy.deepcopy(item['baseline_projection']['runtime_parameters']);label=values.pop('appearance',rid+' '+item['name']);values['name']=label;values['bodies']=[rid]
                c.execute('solid.box',{'body_name':rid,'length':30,'width':30,'height':6,'corner':[i*40,0,0]});c.execute('appearance.assign',values);dump(f/'material.json',{'id':rid,'name':item['name'],'original_specification':item,'native_projection':values,'scope':'Exact original opaque baseline; advanced source intent remains explicit.'})
                color=values['color'];rgb=rgbhex(color.lstrip('#')) if isinstance(color,str) else linear(np.array(color)/255).tolist();mat=simple_material(rid+' '+item['name'],rgb,values['pbr']['roughness'],values['pbr']['metallic']);export_gltf(f,'material',[{'name':rid,'mesh':sphere_mesh(),'material':0}],[mat],{'scope':'Original uniform opaque baseline, not full advanced_target'})
                base=item.get('source_catalog_ids',[])
                if base and (ROOT/'materials'/base[0]/'preview.png').exists():shutil.copy2(ROOT/'materials'/base[0]/'preview.png',f/'related-material-preview.png')
                results['selene_appearances'].append({'id':rid,'name':item['name'],'family':item['family'],'kind':'material','path':f.relative_to(ROOT).as_posix(),'generated':True,'scope':'original opaque baseline'})
            except Exception as e:errors.append({'id':rid,'stage':'selene appearance','error':str(e)})
        c.execute('library.export',{'path':str(ROOT/'libraries/selene-48-appearances.json'),'id':'local.selene','name':'SELENE - 48 original opaque baselines','format':'solidcraft-library/2','provenance':{'license':LICENSE,'author':'Original SolidCraft contributors'}});save(c,ROOT/'native/SELENE-48-appearance-coupons.solidcraft')
        # Each quality configuration is an executable saved native variant plus unchanged target.
        for q in load(ROOT/'quality/index.json')['items']:
            try:
                f=ROOT/q['path'];recipe=load(f/'quality.json');c.execute('file.new',{'name':q['id']+' '+q['name']});box(c);value=copy.deepcopy(recipe['native_projection']);value['camera']={'target':[0,0,0],'yaw':-.7,'pitch':.45,'roll':0,'distance':200,'fov':.7,'up':'z'};c.execute('render.settings.set',{'name':q['id']+' Bounded projection','set':value});save(c,f/'quality.solidcraft');results['quality'].append(q['id'])
            except Exception as e:errors.append({'id':q['id'],'stage':'quality native','error':str(e)})
    try:results['physical_references']=physical_export()
    except Exception as e:errors.append({'stage':'physical references','error':str(e),'trace':traceback.format_exc()})
    s=load(ROOT/'setups/index.json');s['items']+=results['native_studios'];dump(ROOT/'setups/index.json',s);dump(ROOT/'materials/selene-index.json',{'items':results['selene_appearances']})
    dump(ROOT/'reports/supplements.json',{'status':'PASS' if not errors else 'FAIL','results':results,'errors':errors,'seconds':time.time()-start});print('SUPPLEMENTS_FINISHED', {k:len(v) if isinstance(v,list) else v for k,v in results.items()},'errors',errors,flush=True)
if __name__=='__main__':main()
