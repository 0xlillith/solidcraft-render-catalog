"""Build a self-contained, searchable local gallery. No CDN, telemetry or network.
Native render receipts and authored previews remain explicitly distinguished.
"""
from core import *
import csv,html,zipfile,collections,datetime,shutil,subprocess

HTML='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>SolidCraft · Local Render Catalog</title><style>
:root{color-scheme:dark;--bg:#10141a;--panel:#191f28;--muted:#a5b1c2;--line:#303c4c;--accent:#91d8cb}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:#eef2f7;font:15px/1.5 system-ui,Segoe UI,sans-serif}header{padding:32px 4vw 22px;border-bottom:1px solid var(--line);background:linear-gradient(120deg,#1b2932,#141a24)}.eyebrow{font-size:12px;letter-spacing:2px;text-transform:uppercase;color:var(--accent)}h1{font-size:clamp(29px,4vw,48px);margin:6px 0 8px;letter-spacing:-1px}header p{max-width:1100px;color:var(--muted);margin:0 0 18px}.links{display:flex;gap:10px;flex-wrap:wrap}a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}.button,button,select,input{background:#202936;color:#eef2f7;border:1px solid #445269;border-radius:8px;padding:10px 12px;font:inherit}.button:hover,button:hover{background:#2b3745;text-decoration:none}main{padding:22px 4vw 40px}.controls{display:flex;gap:10px;flex-wrap:wrap;position:sticky;top:0;background:#10141af2;padding:12px 0;z-index:2}input{flex:1;min-width:220px}select{max-width:330px}.stats{color:var(--muted);margin:10px 0 24px}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:18px}.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;overflow:hidden;cursor:pointer;transition:border-color .15s,transform .15s}.card:hover{border-color:var(--accent);transform:translateY(-2px)}.image{height:185px;background:#202730;display:flex;align-items:center;justify-content:center;overflow:hidden}.image img{width:100%;height:100%;object-fit:contain}.placeholder{font-size:25px;letter-spacing:1px;color:#91d8cb;text-align:center}.body{padding:14px}.id{font-size:11px;letter-spacing:1px;color:var(--muted)}h3{font-size:16px;margin:4px 0 6px}.family{font-size:12px;color:var(--muted)}.badge{font-size:11px;display:inline-block;border:1px solid #425466;padding:3px 6px;border-radius:5px;margin-top:10px;color:#bdcfdf}.pager{text-align:center;margin:28px}dialog{background:#171e27;color:#f3f5f7;border:1px solid #52657a;border-radius:14px;width:min(1100px,94vw);max-height:92vh;padding:0}dialog::backdrop{background:#000b}.modal-top{position:sticky;top:0;background:#171e27;z-index:3;padding:18px 24px;border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;gap:20px}.modal-content{padding:24px;display:grid;grid-template-columns:minmax(260px,1fr) minmax(260px,1fr);gap:28px}.modal-content img{width:100%;background:#222b35;border-radius:9px}.description{color:#d0d8e4}.note{background:#26323d;border-left:3px solid var(--accent);padding:12px;margin:14px 0;font-size:13px}.warning{border-left-color:#dfb675;background:#342d24}.file-links{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0}h2{margin:0;font-size:23px}h4{margin:20px 0 8px}ul{padding-left:20px;color:#bac7d6;font-size:13px}footer{margin-top:40px;color:#8291a5;font-size:12px;max-width:1000px}.summary{display:flex;gap:25px;flex-wrap:wrap;margin-bottom:16px}.summary strong{font-size:24px;color:#f3f7f9}.summary span{color:var(--muted);font-size:12px}code{font-size:12px;color:#b3c7e4;overflow-wrap:anywhere}@media(max-width:720px){.modal-content{grid-template-columns:1fr}.controls{position:static}.image{height:220px}}
</style></head><body><header><div class="eyebrow">SolidCraft · Local authoring collection · v1</div><h1>The complete render catalog</h1><p>Every source concept has a generated local realization. Rich portable materials, native authoring samples, original geometry and lighting are separated from physical references and capability-dependent intent. Nothing here changes your installed application or downloads resources.</p><div id="summary" class="summary"></div><div class="links"><a class="button" href="libraries/all-600-native-appearances.json" download>600-appearance native library</a><a class="button" href="libraries/selene-48-appearances.json" download>48 SELENE baselines</a><a class="button" href="README.md">Read the format & import guide</a><a class="button" href="reports/catalog-summary.json">Inventory and verification</a><a class="button" href="Resource-Index.csv" download>CSV index</a></div></header><main><div class="controls"><input id="search" type="search" placeholder="Search names, catalog IDs, families or use cases…" aria-label="Search catalog"><select id="kind" aria-label="Resource type"><option value="all">All resource types</option><option value="material">Materials / appearances</option><option value="lighting">Lighting rigs</option><option value="environment">Environments & backplates</option><option value="setup">Scene / studio / environment setups</option><option value="quality">Quality targets</option><option value="shot">SELENE shots</option><option value="physical_reference">Physical reference cards</option></select><select id="family" aria-label="Family"><option value="all">All families</option></select></div><div id="stats" class="stats"></div><div id="grid" class="grid"></div><div class="pager"><button id="more">Show more</button></div><footer>Original authored assets and tooling: MIT OR Apache-2.0. Existing physical-reference records preserve their individual sources, conditions and unknowns; they are not material certification. Native GPU thumbnails use a small 64-sample denoised budget. Environment model snapshots are not the HDR lighting result. View each entry's scope before applying it.</footer></main><dialog id="detail"><div class="modal-top"><div><div class="id" id="did"></div><h2 id="dtitle"></h2></div><button id="close">Close</button></div><div class="modal-content"><div><img id="dimage" alt="Resource preview"><div class="note" id="dimageNote"></div><div class="file-links" id="dimages"></div></div><div><div class="family" id="dfamily"></div><p class="description" id="ddesc"></p><h4>Open / import</h4><div class="file-links" id="dfiles"></div><div class="note warning" id="dscope"></div><h4>Limits and source intent</h4><ul id="dlimits"></ul><h4>Local folder</h4><code id="dpath"></code></div></div></dialog><script>
const DATA=__DATA__;const SUMMARY=__SUMMARY__;let limit=80,filtered=[];const $=id=>document.getElementById(id);const kindNames={material:'Appearances',lighting:'Light rigs',environment:'Environments',setup:'Setups',quality:'Quality targets',shot:'Shots',physical_reference:'References'};
for(const [key,count] of Object.entries(SUMMARY)){const e=document.createElement('div');const n=document.createElement('strong');n.textContent=count;const t=document.createElement('span');t.textContent=' '+key;e.append(n,t);$('summary').append(e)}
function link(container,file,label){const a=document.createElement('a');a.className='button';a.href=file;a.textContent=label;container.append(a)}
function apply(){const q=$('search').value.trim().toLowerCase(),k=$('kind').value,f=$('family').value;filtered=DATA.filter(r=>(k==='all'||r.kind===k)&&(f==='all'||r.family===f)&&(!q||(r.id+' '+r.name+' '+r.family+' '+r.description).toLowerCase().includes(q)));$('stats').textContent=filtered.length+' matching entries · '+DATA.length+' total records · local files only';$('grid').replaceChildren();for(const r of filtered.slice(0,limit)){const card=document.createElement('article');card.className='card';card.tabIndex=0;const picture=document.createElement('div');picture.className='image';if(r.thumbnail){const im=document.createElement('img');im.src=r.thumbnail;im.loading='lazy';im.alt=r.name;picture.append(im)}else{const ph=document.createElement('div');ph.className='placeholder';ph.textContent=r.id;picture.append(ph)}const body=document.createElement('div');body.className='body';const id=document.createElement('div');id.className='id';id.textContent=r.id+' · '+kindNames[r.kind];const title=document.createElement('h3');title.textContent=r.name;const family=document.createElement('div');family.className='family';family.textContent=r.family;const badge=document.createElement('div');badge.className='badge';badge.textContent=r.badge;body.append(id,title,family,badge);card.append(picture,body);card.onclick=()=>show(r);card.onkeydown=e=>{if(e.key==='Enter')show(r)};$('grid').append(card)}$('more').hidden=limit>=filtered.length}
function families(){const old=$('family').value,k=$('kind').value;const names=[...new Set(DATA.filter(r=>k==='all'||r.kind===k).map(r=>r.family))].sort();$('family').replaceChildren(new Option('All families','all'));for(const name of names)$('family').add(new Option(name,name));if(names.includes(old))$('family').value=old}
function show(r){$('did').textContent=r.id;$('dtitle').textContent=r.name;$('dfamily').textContent=r.family;$('ddesc').textContent=r.description;$('dpath').textContent=r.path;$('dscope').textContent=r.scope;$('dimage').hidden=!r.thumbnail;if(r.thumbnail)$('dimage').src=r.thumbnail;$('dimageNote').textContent=r.preview_scope;$('dimages').replaceChildren();for(const x of r.images)link($('dimages'),x.path,x.label);$('dfiles').replaceChildren();for(const x of r.files)link($('dfiles'),x.path,x.label);$('dlimits').replaceChildren();for(const text of r.limitations){const li=document.createElement('li');li.textContent=text;$('dlimits').append(li)}$('detail').showModal()}
$('close').onclick=()=>$('detail').close();$('detail').onclick=e=>{if(e.target===$('detail'))$('detail').close()};let timer;$('search').oninput=()=>{clearTimeout(timer);timer=setTimeout(()=>{limit=80;apply()},140)};$('kind').onchange=()=>{limit=80;families();apply()};$('family').onchange=()=>{limit=80;apply()};$('more').onclick=()=>{limit+=80;apply()};families();apply();
</script></body></html>'''


def build_records():
    rows=[]
    for path in ['materials/index.json','materials/selene-index.json','lighting/index.json','environments/index.json','setups/index.json','quality/index.json','setups/SELENE-SHOTS/index.json','libraries/physical-references/index.json']:
        rows+=load(ROOT/path)['items']
    assert len({r['id'] for r in rows})==len(rows)
    records=[]
    for row in rows:
        f=ROOT/row['path'];kind=row['kind'];r=copy.deepcopy(row);r.update(files=[],images=[],description='',limitations=list(row.get('limitations',[])),scope='',preview_scope='',badge='Generated authoring resource',thumbnail=None)
        def add(filename,label):
            p=f/filename
            if p.is_file():r['files'].append({'path':p.relative_to(ROOT).as_posix(),'label':label})
        if kind=='material':
            data=load(f/'material.json');source=data.get('original_specification',{});r['description']=source.get('description',source.get('purpose',row['name']));r['limitations']=data.get('limitations',source.get('baseline_projection',{}).get('omitted_target_features',[]));r['scope']='Native v2 appearance libraries store uniform PBR values. The GLB carries the richer authored portable material; new image maps are external runtime resources, not automatically installed in SolidCraft.';r['badge']='Portable PBR + native sample'
            for name,label in [('material.solidcraft','Native uniform sample'),('optical-study.solidcraft','Native smooth optical study'),('material.glb','Self-contained GLB'),('material.gltf','Editable glTF'),('material.json','Material recipe'),('native-runtime-texture-request.json','GPU map request'),('maps/base_color.png','Base color PNG'),('maps/normal_gl.png','Normal GL PNG'),('maps/normal_dx.png','Normal DX PNG'),('maps/orm.png','Packed ORM PNG'),('maps/height16.png','16-bit height PNG'),('maps/height_mm.exr','Signed height EXR'),('maps/base_color_linear.exr','Linear color EXR')]:add(name,label)
        elif kind=='environment':
            data=load(f/'environment.json');r['description']=data['original_specification'].get('description',row['name']);r['limitations']=data['limitations'];r['scope']='Finite original context geometry, a separate HDR/EXR illumination field and a camera-only authored backplate. Sun energy is kept outside the HDR to prevent duplicate solar illumination.';r['badge']='Native scene + geometry + HDR'
            for name,label in [('environment.solidcraft','Native environment'),('environment.glb','Self-contained GLB'),('environment.gltf','Editable glTF'),('environment.obj','OBJ geometry'),('illumination.hdr','Radiance HDR'),('illumination.exr','Float EXR'),('backplate.png','Authored backplate PNG'),('environment.json','Environment recipe')]:add(name,label)
        elif kind=='lighting':
            data=load(f/'rig.json');r['description']=data['original_specification'].get('description',row['name']);r['limitations']=data['limitations']+data['unresolved_external_inputs'];r['scope']='Original finite-emitter authoring realization, not measured photometry. The complete JSON rig is authoritative; reference-origin HDR loses finite-source parallax and is a separately labelled projection.';r['badge']='Numeric rig + native sample'
            for name,label in [('rig.solidcraft','Native rig sample'),('rig.json','Full rig definition'),('lighting-full.json','Lighting parameters'),('rig.glb','Rig geometry GLB'),('reference-origin.hdr','Reference-origin HDR'),('reference-origin.exr','Reference-origin EXR')]:add(name,label)
        elif kind=='setup':
            p=f/'setup.json';data=load(p) if p.exists() else load(f/'native-preset.json');source=data.get('original_specification',data.get('entry',{}));r['description']=source.get('description',row['name']);r['limitations']=data.get('limits',row.get('limitations',[]));r['scope']='A saved authoring composition with explicit demo objects/quality bounds. Source role and capability requirements remain in the recipe; it is not a promise of every original simulation feature.';r['badge']='Saved native composition'
            for name,label in [('setup.solidcraft','Open native setup'),('setup.json','Composition recipe'),('native-preset.json','Original preset resolution'),('solidcraft-build.json','Rebuild commands')]:add(name,label)
        elif kind=='quality':
            data=load(f/'quality.json');r['description']=data['original_specification'].get('purpose',row['name']);r['limitations']=data['limitations'];r['scope']='The original resolution/sampling/motion target is preserved. The native variant is explicitly bounded to supported samples/depth and does not claim convergence or shutter integration.';r['badge']='Original target + bounded native variant'
            for name,label in [('quality.solidcraft','Native quality sample'),('quality.json','Quality contract'),('external-render-target.json','Full external target'),('solidcraft-bounded-settings.json','Native bounded parameters')]:add(name,label)
        elif kind=='shot':
            data=load(f/'shot.json');r['description']=data['original_specification'].get('name',row['name']);r['limitations']=data['limitations'];r['scope']='All twelve saved views share the licensed native SELENE model. Unreviewed sub-part selectors are explicitly whole-rover framing studies; no model geometry, joints or pose were altered.';r['badge']='Saved camera / lighting study';r['files'].append({'path':row['native'],'label':'Native SELENE with all 12 shots'});add('shot.json','Complete shot contract')
        else:
            data=load(f/'projection-record.json');r['description']=data['card']['designation'];r['limitations']=['Choose the correct grade, process, temperature and specimen conditions.','Unrepresented quantities remain in the original extended profiles; missing values are not zero.','No appearance or mass assignment is implied by viewing this reference.'];r['scope']='Conserved existing physical-reference data, not newly generated engineering measurements. The native reference library includes only 46 profiles with a supported point density; all 59 extended/card records are retained.';r['badge']='Source-qualified reference, not a visual look';add('native-card.json','Native card JSON');add('projection-record.json','Coverage and omissions');r['files'].append({'path':'libraries/physical-references/physical-reference-library.json','label':'46 supported native references'})
        for name,label,scope in [('native-render.png','Actual GPU sample','Actual SolidCraft GPU image; 64 samples, denoised. Read the receipt/variant; this is not a convergence or full-physics claim.'),('native-model-preview.png','Native model snapshot','Actual SolidCraft modelling/product viewport snapshot. It does not apply the saved HDR/path-traced lighting.'),('preview.png','Authored preview','Original approximate authoring preview or rig diagram, not a native renderer result.'),('panorama.png','Tone-mapped panorama','Display conversion of the authored radiance source, not a measured photograph.'),('backplate.png','Authored background','Camera-only shaded geometry authoring view. Not an illumination source.')]:
            p=f/name
            if p.exists():
                r['images'].append({'path':p.relative_to(ROOT).as_posix(),'label':label})
                if not r['thumbnail']:r['thumbnail']=p.relative_to(ROOT).as_posix();r['preview_scope']=scope
        add('native-render-receipt.json','Native render receipt')
        records.append({k:r[k] for k in ['id','name','kind','family','path','thumbnail','description','scope','preview_scope','badge','limitations','files','images']})
    return records


def main():
    records=build_records();summary={'Materials':600,'SELENE looks':48,'Light rigs':280,'Environments':280,'Setups':97,'Quality profiles':10,'SELENE shots':12,'Physical references':59};assert len(records)==sum(summary.values())
    data=json.dumps(records,ensure_ascii=False,separators=(',',':')).replace('</','<\\/');page=HTML.replace('__DATA__',data).replace('__SUMMARY__',json.dumps(summary))
    (ROOT/'index.html').write_text(page,encoding='utf-8');dump(ROOT/'Catalog.json',{'version':VERSION,'source_commit':load(ROOT/'build.json')['source_commit'],'local_only':True,'collections':summary,'items':records})
    with (ROOT/'Resource-Index.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(['ID','Name','Type','Family','Folder','Preview type','Scope']);w.writerows([r['id'],r['name'],r['kind'],r['family'],r['path'],r['preview_scope'],r['scope']] for r in records)
    (ROOT/'Open-Catalog.cmd').write_text('@echo off\r\ncd /d "%~dp0"\r\nstart "" "%~dp0index.html"\r\n',encoding='ascii')
    readme='''# SolidCraft complete local render catalog — authoring v1

This is a local resource library, not a software release or a change to the installed application.
Open **index.html** or **Open-Catalog.cmd**. No web server or Internet connection is required.

## Delivered coverage

| Collection | Entries |
|---|---:|
| Original material concepts realized as procedural assets | 600 |
| Conserved SELENE opaque appearances | 48 |
| Authored lighting rig realizations | 280 |
| Finite environment/context realizations | 280 |
| Scene, studio and environment compositions, plus original native studios | 97 |
| Original quality profiles with separate bounded native variants | 10 |
| SELENE shot recipes and saved camera/lighting studies | 12 |
| Existing physical reference profiles retained | 59 |

Every main material has 1024 × 1024 lossless PBR maps, OpenGL and DirectX normals, packed ORM,
16-bit normalized height, signed millimetre-height EXR and linear-color EXR. Role-specific
transmission, coating, emission or masks are supplied where authored. The sphere GLB/glTF is
an interchange material sample; the physical repeat and projection authority is material.json.
The sample UV parameterization is not a global CAD manufacturing/texture-coordinate contract.

Environments include actual GLB/glTF/OBJ geometry, an authored HDR/EXR illumination field, a
separate camera-only background and a native `.solidcraft` document with embedded HDR.
Lighting includes the full numeric rig, layout geometry, a native example and a reference-origin
HDR/EXR projection. Do not combine an analytic emitter with the HDR image of the same emitter.

## Use with the current SolidCraft build

1. **Browse visually** in index.html. Each card links the real files and explains its representation.
2. **Uniform native appearances:** open `libraries/all-600-native-appearances.json` through the
   existing Appearance local-library controls. All 600 entries have native-validated revisions.
   Sixty family libraries and `selene-48-appearances.json` are alternatives.
3. **Richer image maps:** use a material's GLB/glTF in a capable external renderer, or its explicit
   `native-runtime-texture-request.json` against its native Specimen body through SolidCraft's
   GPU image API. Arbitrary new image maps are not magically installed in the application's
   compiled built-in catalog. A v2 appearance library stores uniform PBR, not image textures.
4. **Native scenes/rigs/setups:** open the `.solidcraft` resource in a new document, keeping your
   original project intact. Build scripts construct their own examples; do not run them against
   an unsaved working document. Retained images in the current app are not automatic live preview.
5. **Physical references:** `libraries/physical-references/physical-reference-library.json` contains
   46 supported point-density profiles. All 59 original extended profiles/cards are retained.
   Select the actual material, grade, processing and conditions deliberately; never infer a
   physical material from its appearance. No new mechanical or thermal properties were invented.

The 57 `optical-study.solidcraft` files are smooth closed-slab native studies with explicitly
recorded authored RGB absorption. They are not proof of rough, spectral, thin-film, diffractive,
fluorescent, subsurface or geometry-specific behavior. Rich glTF material intent and the unchanged
original specification remain beside the native variant.

## Coverage is not scientific certification

The full source catalog is covered by generated files. This is a **first complete procedural
realization**, not a claim that every high-level concept now has a measured or physically complete
implementation in SolidCraft. The definitions explicitly distinguish portable material intent,
current-native variants, unresolved external inputs and unsupported phenomena.

Specialized optical phenomena, measured photometry/IES, source-dependent calibration, precise
manufacturing topology, atmosphere/ephemerides, motion studies and semantic SELENE sub-part roles
must not be inferred from a thumbnail. Lunar/vacuum presets contain no invented atmosphere or
undeclared sky fill. The original source constraints and calibration blockers remain unchanged.

Native GPU thumbnails are actual 64-sample denoised images of the recorded variant, not final
convergence tests. Environment model snapshots are actual native viewport images, not saved-HDR
renderings. Mathematical authoring swatches and layout diagrams are explicitly labelled.

## Formats and ownership

- `material.json`, `rig.json`, `environment.json`, `setup.json`, `quality.json`, `shot.json`: editable
  authority for new realizations, with the full unchanged source specification.
- PNG: sRGB color; linear-data normals/scalars/ORM; 16-bit height. ORM R is 1 (no invented AO).
- EXR: linear sRGB color/radiance and signed height in mm; lossless ZIP scanlines.
- HDR: bounded Radiance RGBE, linear sRGB/D65 primaries, Z-up equirectangular source orientation.
- GLB/glTF: metres, Y-up; portable PBR and optional material extensions. Reader support varies.
- OBJ/MTL: millimetres, Z-up, deliberately simpler scalar fallback.
- `.solidcraft`: generated by the real pinned native CLI, not hand-written container guesses.
- `solidcraft-library/2`: native-exported/validated definitions, not a renamed planning JSON file.

External native command paths refer to this output directory. Keep the folder at its current
location, or update those explicit paths before replaying build/request files. GLB is self-contained;
glTF uses adjacent relative images/buffers. The generated native environment files retain HDR bytes
and their imported geometry without needing the original GLB/HDR path at reopen.

## Reproduction and verification

Source application commit: `9e6e0b8df130f342e15ebe988b7211d1482a44c2`.
The authoring scripts are in `tools/`; the unmodified source catalogs and original starter/physical
resources are in `source/`. `reports/` contains native receipts, failures from superseded attempts
and final validation results. `SHA256SUMS.txt` identifies the delivered bytes.

Primary generators: `materials.py`, `lighting.py`, `environments.py`, `setups.py`.
Native writers: `native_materials.py`, `native_environments.py`, `supplements.py`, `selene_shots.py`.
Validation: `validate_assets.py` uses the official offline Khronos glTF validator plus image,
normal, packing, EXR/HDR and native-container checks. Native generation and cold-reopen checks
are separate from photometric correctness and full original-specification acceptance.

The original generators/maps/rigs and reference sources remain archived. New code/assets are
original authoring under MIT OR Apache-2.0. Third-party tool dependencies retain their own licences;
physical-source claims retain their original metadata. No commercial CAD content or font files
were copied. Nothing was published to GitHub and the application source/install was not edited.
'''
    (ROOT/'README.md').write_text(readme,encoding='utf-8',newline='\n')
    # A convenient small import bundle; the large textures stay in their own folders.
    with zipfile.ZipFile(ROOT/'Native-Appearance-Libraries.zip','w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted((ROOT/'libraries').glob('*.json')):z.write(p,'libraries/'+p.name)
        p=ROOT/'libraries/physical-references/physical-reference-library.json';z.write(p,'libraries/physical-reference-library.json');z.write(ROOT/'README.md','README.md')
    for r in records:
        for a in r['files']+r['images']:assert (ROOT/a['path']).is_file(),a
    dump(ROOT/'reports/catalog-summary.json',{'version':VERSION,'source_commit':load(ROOT/'build.json')['source_commit'],'collections':summary,'indexed_records':len(records),'local_only':True,'all_gallery_file_links_exist':True,'native_library_master_entries':600,'full_original_physical_requirements_certified':False})
    print('CATALOG_READY',len(records),'records',flush=True)
if __name__=='__main__':main()
