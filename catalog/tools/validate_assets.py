"""Independent structural/data verification plus the official Khronos validator.
Does not claim measured material accuracy or complete scene-level visual acceptance.
"""
from core import *
import subprocess,time,traceback,zipfile

def main():
    start=time.time();errors=[];counts={};gltf_results=[]
    for category,expected in [('materials',600),('lighting',280),('environments',280)]:
        index=load(ROOT/category/'index.json')['items'];assert len(index)==expected;assert len({x['id'] for x in index})==expected;counts[category]=len(index)
    for i,row in enumerate(load(ROOT/'materials/index.json')['items']):
        f=ROOT/row['path'];r=load(f/'material.json')
        try:
            maps={}
            for role,info in r['maps'].items():
                p=f/info['path'];assert sha(p)==info['sha256'],(r['id'],role,'digest')
                if p.suffix=='.png':
                    with Image.open(p) as im:a=np.array(im)
                    assert a.shape[:2]==(1024,1024),(r['id'],role,a.shape);maps[role]=a
            assert maps['height16'].dtype==np.uint16 or maps['height16'].dtype==np.int32
            n=maps['normal_gl'].astype(np.float32)/127.5-1;err=float(np.max(np.abs(np.linalg.norm(n,axis=-1)-1)));assert err<.009,(r['id'],'normal length',err)
            assert np.array_equal(maps['normal_dx'][:,:,1],255-maps['normal_gl'][:,:,1]);assert np.array_equal(maps['orm'][:,:,1],maps['roughness']);assert np.array_equal(maps['orm'][:,:,2],maps['metallic']);assert (maps['orm'][:,:,0]==255).all()
            with OpenEXR.File(str(f/'maps/height_mm.exr')) as ex:
                a=ex.channels()['Y'].pixels;expect=(maps['height16'].astype(np.float32)/65535-.5)*r['height_span_mm'];assert np.allclose(a,expect,atol=1e-6);assert np.isfinite(a).all()
            with OpenEXR.File(str(f/'maps/base_color_linear.exr')) as ex:
                a=ex.channels()['RGB'].pixels;assert a.shape==(1024,1024,3) and np.isfinite(a).all() and a.min()>=0 and a.max()<=1.0001
            assert (f/'material.solidcraft').is_file()
        except Exception as e:errors.append({'id':r['id'],'error':str(e),'trace':traceback.format_exc()})
        if (i+1)%100==0:print('VALIDATED_MATERIAL_MAPS',i+1,'errors',len(errors),flush=True)
    for category,stem in [('lighting','reference-origin'),('environments','illumination')]:
        for row in load(ROOT/category/'index.json')['items']:
            f=ROOT/row['path']
            try:
                rgb=decode_hdr(f/(stem+'.hdr'))
                with OpenEXR.File(str(f/(stem+'.exr'))) as ex:linear_pixels=ex.channels()['RGB'].pixels
                assert rgb.shape==linear_pixels.shape;peak=max(1.,float(linear_pixels.max()));assert float(np.max(np.abs(rgb-linear_pixels)))/peak<.0081
                assert np.isfinite(rgb).all() and rgb.min()>=0
                if category=='environments':
                    r=load(f/'environment.json')
                    if int(row['id'].split('-')[1])>=241 and not any(k in row['name'].lower() for k in ['led']):assert float(rgb.max())==0,'vacuum sky must remain dark'
            except Exception as e:errors.append({'id':row['id'],'error':str(e),'trace':traceback.format_exc()})
        print('VALIDATED_HDR_EXR',category,'errors',len(errors),flush=True)
    # Both the portable self-contained and directory variants are exercised.
    paths=[]
    for category in ['materials','lighting','environments']:
        paths += [p.relative_to(ROOT).as_posix() for p in (ROOT/category).rglob('*.glb')]
        paths += [p.relative_to(ROOT).as_posix() for p in (ROOT/category).rglob('*.gltf')]
    for start_index in range(0,len(paths),50):
        batch=paths[start_index:start_index+50];p=subprocess.run(['node',str(ROOT/'tools/validate_gltf.js'),str(ROOT),*batch],capture_output=True,text=True,encoding='utf-8',timeout=180)
        try:report=json.loads(p.stdout);gltf_results.extend(report['results'])
        except Exception:errors.append({'batch':start_index,'error':'validator failed','stderr':p.stderr[-2000:],'stdout':p.stdout[-1000:]});continue
        if p.returncode:errors += [{'file':x['file'],'error':'glTF validation errors','messages':x['messages']} for x in report['results'] if x['errors']]
        if start_index%200==0:dump(ROOT/'reports/validation-progress.json',{'gltf_checked':len(gltf_results),'errors':errors});print('GLTF_VALIDATED',len(gltf_results),'errors',len(errors),flush=True)
    dump(ROOT/'reports/gltf-validation.json',{'validator':'Khronos gltf-validator 2.0.0-dev.3.10','files':len(gltf_results),'total_errors':sum(x['errors'] for x in gltf_results),'total_warnings':sum(x['warnings'] for x in gltf_results),'results':gltf_results})
    containers=list((ROOT/'materials').rglob('*.solidcraft'))+list((ROOT/'lighting').rglob('*.solidcraft'))+list((ROOT/'environments').rglob('*.solidcraft'))+list((ROOT/'setups').rglob('*.solidcraft'))
    for p in containers:
        try:
            with zipfile.ZipFile(p) as z:
                assert z.testzip() is None;assert 'document.json' in z.namelist();d=json.loads(z.read('document.json'));assert str(d.get('format','')).startswith('solidcraft/')
        except Exception as e:errors.append({'file':str(p.relative_to(ROOT)),'error':str(e)})
    result={'status':'PASS' if not errors else 'FAIL','inventory':counts,'gltf_files_checked':len(gltf_results),'native_containers_crc_checked':len(containers),'errors':errors,'seconds':time.time()-start,'scope':'Map digests/dimensions/normals/packing, HDR/EXR numeric agreement, glTF official validation, container checks; not universal renderer/physical correctness.'}
    dump(ROOT/'reports/asset-validation.json',result);print('ASSET_VALIDATION',json.dumps({k:v for k,v in result.items() if k!='errors'}),'errors',len(errors),flush=True)
    if errors:raise RuntimeError(errors[:3])
if __name__=='__main__':main()
