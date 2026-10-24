"""Generate every MAT entry as an explicitly authored material asset, not a measured sample.
Family recipes and semantic overrides are editable. Original source specifications remain immutable.
"""
from __future__ import annotations
from core import *
import importlib.util, concurrent.futures, traceback, time
spec=importlib.util.spec_from_file_location('starter_original',ROOT/'source/assets/render/starter/tools/materials.py')
STARTER=importlib.util.module_from_spec(spec);spec.loader.exec_module(STARTER)
# One tuple per original family: pattern, sRGB authoring color, roughness, metalness,
# physical repeat in mm, authored height span in mm. These are visual choices only.
FAMILIES=[
('brushed','a7adb3',.24,1,100,.018),('milled','bcc4cb',.27,1,100,.02),('brushed','b8763d',.26,1,100,.018),
('powder','335574',.48,0,100,.06),('polymer','303b47',.4,0,100,.03),('polymer','d4e6e8',.13,0,100,.004),
('rubber','24272a',.72,0,60,.16),('polymer','dcece9',.045,0,100,.001),('ceramic','d9d4c5',.22,0,100,.05),
('aggregate','9b9688',.82,0,200,1.0),('marble','c4c0b5',.3,0,300,.10),('wood','a57d4a',.45,0,160,.35),
('plywood','bfa06e',.62,0,120,.25),('weave','6b6770',.87,0,60,.45),('grain','67665d',.82,0,200,1.2),
('weave_twill','30343a',.34,0,80,.20),('pcb','26754d',.34,0,80,.04),('fdm','638fba',.5,0,25,.18),
('water','c4dfe0',.06,0,160,.25),('iridescent','8d66a0',.22,0,100,.02),('powder','3e5f7b',.22,0,100,.04),
('polymer','2c3038',.28,0,100,.04),('turned','72767b',.38,1,100,.055),('grip','1c1d20',.82,0,80,.65),
('polymer','c3d5db',.08,0,100,.01),('leather','3a3431',.78,0,100,.25),('milled','a5adb4',.27,1,100,.035),
('powder','717781',.4,.35,100,.06),('overlay','7b5942',.65,0,100,.08),('weave','3b3e40',.7,0,50,.35),
('pcb','215c3a',.35,0,60,.055),('grain','a3a9ac',.35,.8,50,.018),('polymer','292c32',.5,0,50,.025),
('fibre','b38c41',.48,0,70,.12),('foil','73777b',.36,.6,100,.10),('fdm','5d8ea2',.45,0,20,.25),
('fdm','608cb0',.48,0,25,.22),('polymer','919ca5',.45,0,35,.065),('powder','878e96',.76,.35,40,.23),
('milled','a69c75',.3,.7,70,.035),('wood','a37f4f',.55,0,160,.3),('wood','ac8854',.5,0,200,.35),
('wood','a37c43',.32,0,160,.2),('grain','aa9473',.65,0,80,.35),('led','ecd083',.3,0,15,.005),
('prism','dce6eb',.35,0,30,.18),('polymer','d5e5ec',.12,0,60,.02),('weave_twill','31363d',.4,0,80,.18),
('honeycomb','a6a3a0',.68,.4,70,1.0),('grain','9c9a91',.6,0,100,.3),('foil','b9a676',.25,.85,120,1.2),
('solar','24386a',.18,.15,120,.035),('weave','a79152',.5,.3,50,.25),('regolith','565458',.96,0,60,1.1),
('regolith','9a9892',.93,0,70,1.3),('overlay','75716a',.95,0,80,.08),('milled','9d9fa3',.38,.85,70,.04),
('brushed','8b909a',.32,.75,70,.04),('polymer','d9e8ec',.06,0,40,.004),('brushed','9c9fa4',.32,.8,80,.045)]
EXISTING=load(ROOT/'source/assets/render/starter/materials/source/recipes.json')['items']
OLD_BY_CONCEPT={cid:x for x in EXISTING for cid in x.get('catalog_ids',[])}


def recipe(item):
    num=int(item['id'].split('-')[1]);fam=(num-1)//10;variant=(num-1)%10;n=item['name'].lower()
    pat,color,rough,metal,tile,height=FAMILIES[fam]
    rough=float(np.clip(rough+(.018*(variant-4)),.045,1));cu,cv=12,32
    # Explicit semantic selections override the family starter, rather than cloning the same map.
    for keys,k in [(['brushed','ground bearing','surface-ground','lapped'],'brushed'),(['cross-satin','crosshatch'],'cross_brushed'),(['milled','machined'],'milled'),(['turned','rotor','brake track'],'turned'),(['powder','blasted','sls','mjf','sintered','granular'],'powder'),(['knurl','grip','tread','pedal'],'grip'),(['hammer'],'hammered'),(['galvanized'],'galvanized'),(['plywood','laminate edge','lamination','stack','corrugated'],'plywood'),(['wood','timber','oak','walnut','maple','pine','birch','teak','cedar','ash','elm','cherry','sapele','fir ','spruce','larch','acacia','wenge','bamboo','veneer'],'wood'),(['end-grain','butcher'],'endgrain'),(['twill','carbon-pattern'],'weave_twill'),(['woven','weave','braid','mesh','seat-belt','textile','canvas','ripstop'],'weave'),(['fdm','printed layer','filament','monotonic'],'fdm'),(['concentric'],'fdm_top'),(['marble','onyx'],'marble'),(['terrazzo','granite','aggregate','particleboard','osb'],'aggregate'),(['foam','porous','pore travertine'],'foam'),(['honeycomb','hexagonal','isogrid','lattice'],'honeycomb'),(['foil','blanket','crumpled','polyimide'],'foil'),(['solar-cell','solar cell'],'solar'),(['pcb','circuit','solder mask'],'pcb'),(['leather','skin','suede'],'leather'),(['prismatic','reeded','fresnel','lenticular'],'prism'),(['water','liquid','gel'],'water'),(['regolith','breccia','basalt','rubble','lunar block'],'regolith'),(['dust','smear','fingerprint','deposit','abrasion overlay'],'overlay'),(['iridescent','pearlescent','nacre','holographic','heat-tint'],'iridescent')]:
        if any(t in n for t in keys):pat=k
    colors={'copper':'b97848','brass':'c2a34d','bronze':'9c793f','gold':'d0ac4a','silver':'c8cacc','tin':'b7bbc0','nickel':'adb4b8','titanium':'989ba0','aluminium':'c0c6cd','aluminum':'c0c6cd','steel':'9ea5ad','rust':'9b4a27','patina':'47836c','terracotta':'b36c46','brick':'995b44','walnut':'795131','oak':'aa804b','maple':'d4b98b','beech':'c7a277','pine':'cbb275','birch':'d9c398','teak':'9b743c','cedar':'af7654','wenge':'543728','cherry':'ac7551','cork':'ad9467','aramid':'c1a443','carbon':'252b31','black':'171c23','white':'e6e3d9','dark':'2b2f36','amber':'b97d24','red':'973c32','green':'346c51','blue':'375a86','gray':'898e94','grey':'83898e','gold-finished':'d1ad51'}
    for key,c in colors.items():
        if key in n:color=c
    if 'polished' in n or 'mirror' in n:rough=.055
    if any(k in n for k in ['gloss','clear-coated','lacquer']):rough=.13
    if 'matte' in n or 'sanded' in n:rough=max(.61,rough)
    if any(k in n for k in ['rough','dust','foam','regolith','rubber','powder']):rough=max(.72,rough)
    if any(k in n for k in ['glass','acrylic','polycarbonate','silicone','polymer','rubber','wood','epoxy','ceramic','paint','paper','resin','nylon','polyimide','leather','fibreglass','porcelain']):metal=0.
    if any(k in n for k in ['brass','copper','silver','tin-plated','nickel','gold','steel','aluminium','aluminum','titanium','chromium','metallic','metal-facing']):
        metal=1. if not any(k in n for k in ['paint','primer','coating','coated','anodized','patina','oxide','rust','filled','metallic paint']) else .2
    if any(k in n for k in ['pcb','solder mask','circuit']):color='27623d';metal=0.
    if 'solder' in n and 'mask' not in n:color='b5b9c0';metal=.95
    trans=any(k in n for k in ['clear ','transparent','glass','translucent','optical lens','water','liquid','gel','sapphire','silica','light guide','light-guide','light pipe','light-pipe','diffuser','diffusion','opal acrylic']) and not any(k in n for k in ['glass-fibre','glass-fiber','glass-epoxy','glass fibre','opaque','glass with exposed','mirror','back-silver','contact','glass shard field'])
    ior=1.5
    if 'water' in n:ior=1.333
    if 'acrylic' in n:ior=1.49
    if 'polycarbonate' in n:ior=1.585
    if 'silica' in n:ior=1.46
    if 'sapphire' in n:ior=1.76
    if 'borosilicate' in n:ior=1.47
    if 'silicone' in n:ior=1.41
    if trans:metal=0.;rough=.045 if not any(k in n for k in ['frost','translucent','scattering','milky','opal','diffus','turbid','gel']) else .35
    emission=any(k in n for k in ['active display','active phosphor','direct-emitting','micro-emitter']) and 'unpowered' not in n
    thin=any(k in n for k in ['sheet','film','window','coverglass','glazing','windscreen','cover','foil'])
    coat=0.7 if any(k in n for k in ['coat','varnish','lacquer','candy','paint-protection','clear-finished','epoxy-sealed']) else 0.
    aniso=.65 if any(k in n for k in ['brushed','ground','turned','longitudinal','fibre','fiber','woven','twill']) else 0.
    irid=any(k in n for k in ['iridescent','pearlescent','nacre','antireflection','heat-tint'])
    if pat in ['weave','weave_twill']:cu=cv=16
    if pat in ['fdm','fdm_top']:tile=12.8;cv=64;height=.16
    if pat=='wood':cu=8+variant;cv=16
    if pat=='foil':cu=6+variant;cv=8+variant
    limitations=['Illustrative authored RGB material; no measured optical/engineering certification.','Bump/height is not automatically geometric displacement.','Full original specification retained; generated realization is not every required physical capability.']
    if any(k in n for k in ['diffraction','diffractive','holograph','retroreflect','fluores','phosphores','lenticular','spectral','variable-transmittance','variable-dimming']):limitations+=['Wave/spectral/time-dependent phenomenon is not simulated; static RGB authoring fallback and intended-model metadata are explicit.']
    if any(k in n for k in ['void','hole','core','mesh','foam','perforat','lattice','sipe','edge','section','joint','thread','grouser','serrat','dovetail','mortise']):limitations+=['Topology, openings and assembled geometry require matching geometry; the texture coupon does not manufacture them.']
    if trans and rough>.1:limitations+=['Rough transmission/scattering intent is represented in portable material; native smooth-transmission fallback is separately named.']
    if aniso:limitations+=['Directional normal map is not proof of anisotropic transport; portable material declares anisotropy explicitly.']
    if emission:limitations+=['Emissive radiance is authored; no measured lumens, spectrum or electrical/thermal behavior.']
    orig=OLD_BY_CONCEPT.get(item['id'])
    low=np.array(rgbhex(color))*.67;high=np.minimum(np.array(rgbhex(color))*1.22+.008,1)
    if orig and not trans:
        pat=orig['pattern'];low=np.array(orig['base_linear_low']);high=np.array(orig['base_linear_high']);rough=max(.045,orig['roughness']);metal=orig['metallic'];tile=orig['tile_mm'];height=orig['height_span_mm'];cu=orig['cycles_u'];cv=orig['cycles_v']
    else:tile=[tile,tile]
    return {'id':item['id'],'name':item['name'],'family':item['family'],'version':VERSION,'seed':6200000+num*7919,'pattern':pat,'base_linear_low':low.tolist(),'base_linear_high':high.tolist(),'roughness':rough,'roughness_variation':.06 if rough>.1 else .008,'metallic':metal,'height_span_mm':height,'tile_mm':tile,'cycles_u':cu,'cycles_v':cv,'ior':ior,'transmission':1. if trans else 0.,'thin_walled':thin,'thickness_mm':1. if thin else 10.,'clearcoat':coat,'anisotropy':aniso,'iridescence':float(irid),'emission_strength':3. if emission else 0.,'authoring_license':LICENSE,'measurement_status':'authored_not_measured','original_specification':item,'source_surface_id':orig['id'] if orig else None,'limitations':limitations}


def fields(r,size):
    u=(np.arange(size,dtype=np.float32)[None,:]+.5)/size;v=1-(np.arange(size,dtype=np.float32)[:,None]+.5)/size
    if r['pattern'] in STARTER.KINDS:return STARTER.fields(r,u,v)
    coarse=STARTER.noise(u,v,r['seed'],1);fine=STARTER.noise(u,v,r['seed']+9,12);p=r['pattern'];h=.5+.2*coarse+.1*fine;t=.5+.25*coarse
    if p=='marble':
        wave=np.sin(2*np.pi*(3*u+2*v+.32*coarse));vein=np.exp(-90*wave**2);t=.88-.68*vein+.06*fine;h=.5+.025*fine
    elif p=='aggregate':
        cell=np.sin(2*np.pi*(23*u+.1*coarse))*np.cos(2*np.pi*(21*v+.12*coarse));t=.45+.3*np.tanh(4*cell)+.16*fine;h=.5+.24*cell+.12*fine
    elif p=='foam':
        cells=(np.sin(2*np.pi*(19*u+.2*coarse))*np.sin(2*np.pi*(17*v+.2*coarse)))**2;h=.7-.55*np.exp(-12*cells);t=.42+.35*h
    elif p=='honeycomb':
        x=u*12;y=v*14;dx=(x+(.5*(np.floor(y)%2)))%1-.5;dy=y%1-.5;edge=np.maximum(np.abs(dx)*.866+np.abs(dy)*.5,np.abs(dy));wall=np.clip((edge-.35)*18,0,1);h=.12+.8*wall;t=.12+.7*wall
    elif p=='endgrain':
        x=(u*4)%1-.5;y=(v*4)%1-.5;rad=np.sqrt(x*x+y*y);ring=.5+.5*np.cos(2*np.pi*(rad*12+.12*coarse));t=.18+.65*ring+.05*fine;h=.6-.2*ring**8
    elif p=='ceramic':h=.5+.15*fine+.06*coarse;t=.6+.12*coarse
    elif p=='leather':
        crease=np.abs(np.sin(2*np.pi*(18*u+2*coarse))*np.sin(2*np.pi*(17*v+2*coarse)));h=.3+.55*np.sqrt(crease);t=.4+.35*h
    elif p=='overlay':
        patch=np.clip((coarse+.18)*2.5,0,1);h=.25+.65*patch+.05*fine;t=.2+.65*patch
    elif p=='iridescent':h=.5+.04*fine;t=.5+.4*np.sin(2*np.pi*(u+v+.15*coarse))
    elif p=='prism':h=(v*32)%1;h=1-np.abs(2*h-1);t=.5+.04*fine
    elif p=='solar':
        grid=((u*12)%1<.025)|((v*12)%1<.025);bus=((u*3)%1<.018);t=np.where(bus,.95,np.where(grid,.12,.55+.08*fine));h=np.where(bus,.7,np.where(grid,.3,.5))
    elif p=='water':h=.5+.18*np.sin(2*np.pi*(3*u+2*v))+.1*np.sin(2*np.pi*(7*u-5*v+.15*coarse));t=.5+.03*fine
    elif p=='led':h=.5+.02*fine;t=.65+.15*coarse
    rough=np.clip(r['roughness']+r['roughness_variation']*(2*h-1),.045,1)
    return np.broadcast_to(np.clip(h,0,1),(size,size)).copy(),np.broadcast_to(np.clip(t,0,1),(size,size)).copy(),np.broadcast_to(rough,(size,size)).copy()


def material_gltf(r):
    ext={};m={'name':r['id']+' '+r['name'],'pbrMetallicRoughness':{'baseColorFactor':[1,1,1,1],'metallicFactor':1.,'roughnessFactor':1.},'normalTexture':{'index':0},'_textures':{'base':'maps/base_color.png','mr':'maps/orm.png','normal':'maps/normal_gl.png'},'doubleSided':r['thin_walled'],'extras':{'catalog_id':r['id'],'tile_mm':r['tile_mm'],'limitations':r['limitations']}}
    ext['KHR_materials_ior']={'ior':r['ior']}
    if r['transmission']:
        ext['KHR_materials_transmission']={'transmissionFactor':r['transmission']}
        if not r['thin_walled']:
            col=(np.array(r['base_linear_low'])+r['base_linear_high'])/2
            ext['KHR_materials_volume']={'thicknessFactor':r['thickness_mm']*.001,'attenuationDistance':.01,'attenuationColor':np.clip(col,.05,1).tolist()}
    if r['clearcoat']:ext['KHR_materials_clearcoat']={'clearcoatFactor':r['clearcoat'],'clearcoatRoughnessFactor':.08}
    if r['anisotropy']:ext['KHR_materials_anisotropy']={'anisotropyStrength':r['anisotropy'],'anisotropyRotation':0.}
    if r['iridescence']:ext['KHR_materials_iridescence']={'iridescenceFactor':1.,'iridescenceIor':1.3,'iridescenceThicknessMinimum':100.,'iridescenceThicknessMaximum':400.}
    if r['pattern'] in ('weave','leather','fibre'):ext['KHR_materials_sheen']={'sheenColorFactor':[.15,.15,.15],'sheenRoughnessFactor':.7}
    if r['emission_strength']:
        m['emissiveFactor']=[1.,1.,1.];m['_textures']['emissive']='maps/emission.png';ext['KHR_materials_emissive_strength']={'emissiveStrength':r['emission_strength']}
    m['extensions']=ext;return m


def swatch(r,maps,size=256):
    """Original approximate authoring sphere, not a SolidCraft screenshot or transport acceptance."""
    xy=np.linspace(-1.16,1.16,size);x,y=np.meshgrid(xy,-xy);inside=x*x+y*y<1;z=np.sqrt(np.maximum(1-x*x-y*y,0));N=np.stack([x,y,z],axis=-1)
    u=(np.arctan2(y,x)/(2*np.pi)+.5)%1;v=np.arccos(np.clip(z,-1,1))/np.pi
    row=np.minimum((v*maps['base_color'].shape[0]).astype(int),maps['base_color'].shape[0]-1);col=np.minimum((u*maps['base_color'].shape[1]).astype(int),maps['base_color'].shape[1]-1)
    base=linear(maps['base_color'][row,col]/255);rough=maps['roughness'][row,col]/255;metal=maps['metallic'][row,col]/255
    normal=maps['normal_gl'][row,col]/127.5-1;tangent=unit(np.stack([-y,x,np.zeros_like(x)],-1));bitangent=unit(np.cross(N,tangent));N=unit(tangent*normal[:,:,0,None]+bitangent*normal[:,:,1,None]+N*normal[:,:,2,None])
    V=np.array([0,0,1.]);f0=.04*(1-metal[:,:,None])+base*metal[:,:,None];out=base*.06*(1-metal[:,:,None])
    for L,power in [(unit([-1,1,1]),2.4),(unit([1,.2,.6]),1.4),(unit([0,-1,.8]),.55)]:
        H=unit(L+V);ndl=np.clip(N@L,0,1);ndv=np.maximum(N[:,:,2],.02);ndh=np.clip(N@H,0,1);vdh=float(V@H);a2=np.maximum(rough,.08)**4;D=a2/(np.pi*(ndh*ndh*(a2-1)+1)**2+1e-8);k=(rough+1)**2/8;G=ndl/(ndl*(1-k)+k+1e-8)*ndv/(ndv*(1-k)+k);F=f0+(1-f0)*(1-vdh)**5
        spec=D[:,:,None]*G[:,:,None]*F/np.maximum(4*ndl*ndv,1e-5)[:,:,None];out+=(base/np.pi*(1-metal[:,:,None])*(1-F)+spec)*ndl[:,:,None]*power
    if r['transmission']:
        checker=(np.floor((x+1.2)*8)+np.floor((y+1.2)*8))%2;bg=.2+.45*checker
        out=out*.5+bg[:,:,None]*np.clip(base+.25,0,1)*(.8-.5*(1-np.maximum(N[:,:,2],0))[:,:,None])
    if r['emission_strength']:out+=base*r['emission_strength']
    out=srgb(out/(1+out));background=np.full_like(out,.105);out=np.where(inside[:,:,None],out,background)
    return np.rint(np.clip(out,0,1)*255).astype(np.uint8)


def build_one(item,size=1024):
    rid=item['id'];folder=ROOT/'materials'/rid;folder.mkdir(exist_ok=True);mapsdir=folder/'maps';mapsdir.mkdir(exist_ok=True)
    r=recipe(item);h,t,rough=fields(r,size);h16=np.rint(h*65535).astype(np.uint16);disp=(h16.astype(np.float32)/65535-.5)*r['height_span_mm'];normal=STARTER.normal_from_height(disp,r['tile_mm']);base=np.array(r['base_linear_low'])+(np.array(r['base_linear_high'])-r['base_linear_low'])*t[:,:,None]
    if r['pattern']=='iridescent':
        u=(np.arange(size)[None,:]+.5)/size;v=(np.arange(size)[:,None]+.5)/size
        rainbow=np.stack([.5+.5*np.sin(2*np.pi*(u+v)+p) for p in (0,2.1,4.2)],axis=-1);base=np.clip(.55*base+.18*rainbow,0,1)
    maps={'base_color':np.rint(srgb(base)*255).astype(np.uint8),'normal_gl':np.rint((normal*.5+.5)*255).astype(np.uint8),'roughness':np.rint(rough*255).astype(np.uint8),'metallic':np.full((size,size),round(r['metallic']*255),np.uint8),'height16':h16}
    maps['normal_dx']=maps['normal_gl'].copy();maps['normal_dx'][:,:,1]=255-maps['normal_dx'][:,:,1]
    maps['orm']=np.stack([np.full((size,size),255,np.uint8),maps['roughness'],maps['metallic']],-1)
    if r['transmission']:maps['transmission']=np.full((size,size),255,np.uint8)
    if r['clearcoat']:maps['clearcoat']=np.full((size,size),round(255*r['clearcoat']),np.uint8)
    if r['emission_strength']:maps['emission']=maps['base_color']
    if r['pattern']=='overlay':maps['mask']=np.rint(np.clip((h-.25)/.65,0,1)*255).astype(np.uint8)
    for role,a in maps.items():png(mapsdir/(role+'.png'),a,'srgb' if role in ('base_color','emission') else 'linear_data')
    exr(mapsdir/'height_mm.exr',{'Y':disp},'Signed millimetre height about zero; not automatically geometric displacement')
    exr(mapsdir/'base_color_linear.exr',{'RGB':base},'Linear sRGB authored reflectance; no illumination baked in')
    png(folder/'preview.png',swatch(r,maps),'srgb')
    r['maps']={role:{'path':'maps/'+role+'.png','sha256':sha(mapsdir/(role+'.png')),'encoding':'srgb' if role in ('base_color','emission') else 'linear_data','bit_depth':16 if role=='height16' else 8,'size':[size,size]} for role in maps}
    r['maps'].update(height_mm={'path':'maps/height_mm.exr','sha256':sha(mapsdir/'height_mm.exr'),'units':'mm','zero':0},base_color_linear={'path':'maps/base_color_linear.exr','sha256':sha(mapsdir/'base_color_linear.exr'),'encoding':'linear_srgb'})
    r['preview_contract']='Original approximate authoring swatch, not a SolidCraft render or optical validation.'
    r['normal_convention']='normal_gl: +Y tangent-space, V image-up; normal_dx flips green. glTF UV0 V image-down, tangent basis supplied.'
    r['height_decoding']='(height16/65535 - 0.5) * height_span_mm'
    r['ao_contract']='ORM red is constant 1; no fictitious cavity occlusion baked in.'
    r['native_contract']={'uniform_look':'supported; textures/advanced optics are not encoded in an appearance-library entry','runtime_texture_request':'opaque planar fields only; explicit file capture and exact target required','persistent_new_texture_binding':'not installed in the application built-in catalog; requires future importer','full_optical_intent':'portable material and recipe; native support is capability dependent'}
    dump(folder/'material.json',r)
    export_gltf(folder,'material',[{'name':rid+' material sphere','mesh':sphere_mesh(),'material':0}],[material_gltf(r)],{'catalog_id':rid,'scope':'portable material sample; underlying geometry is a sphere, not manufactured structure','millimetre_repeat':r['tile_mm'],'license':LICENSE})
    mean=np.mean(base,axis=(0,1)); color=np.rint(np.clip(srgb(mean),0,1)*255).astype(int).tolist()
    uniform={'bodies':['Specimen'],'color':color,'name':rid+' '+r['name']+(' [uniform fallback]' if r['transmission'] or r['emission_strength'] or r['pattern']=='overlay' else ''),'opacity':1.0,'pbr':{'metallic':r['metallic'],'roughness':float(r['roughness']),'dielectric_ior':r['ior']}}
    dump(folder/'native-appearance.json',{'command':'appearance.assign','params':uniform})
    frame={'origin':[-20,-20,0],'u':[r['tile_mm'][0],0,0],'v':[0,r['tile_mm'][1],0]}
    texture={'body_index':0,'body_name':'Specimen','frame':frame,'base_color_mode':'replace','flip_v':True,'normal_strength':1.,'base_color_srgb':str(mapsdir/'base_color.png'),'normal_opengl':str(mapsdir/'normal_gl.png'),'roughness_linear':str(mapsdir/'roughness.png'),'metallic_linear':str(mapsdir/'metallic.png')}
    dump(folder/'native-runtime-texture-request.json',{'progressive':True,'samples':64,'max_depth':8,'raytrace':{'textures':[texture]}})
    return {'id':rid,'name':r['name'],'family':r['family'],'path':folder.relative_to(ROOT).as_posix(),'thumbnail':folder.relative_to(ROOT).as_posix()+'/preview.png','kind':'material','pattern':r['pattern'],'transmission':r['transmission'],'limitations':r['limitations'],'full_source_requirements_validated':False,'generated':True}


def main():
    items=load(SOURCE/'materials.json')['items'];records=[];errors=[];start=time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        jobs={pool.submit(build_one,item):item for item in items}
        for f in concurrent.futures.as_completed(jobs):
            item=jobs[f]
            try:records.append(f.result())
            except Exception as e:errors.append({'id':item['id'],'error':str(e),'trace':traceback.format_exc()})
            if (len(records)+len(errors))%20==0:
                dump(ROOT/'reports/material-progress.json',{'complete':len(records),'errors':errors,'total':len(items),'seconds':round(time.time()-start,1)});print('MATERIALS',len(records),'errors',len(errors),flush=True)
    records.sort(key=lambda x:x['id']);dump(ROOT/'materials/index.json',{'items':records});dump(ROOT/'reports/material-generation.json',{'status':'PASS' if not errors else 'FAIL','count':len(records),'expected':600,'errors':errors,'seconds':time.time()-start})
    if errors:raise RuntimeError(errors[:3])
if __name__=='__main__':main()
