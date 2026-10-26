#!/usr/bin/env python3
"""Original deterministic authoring of soil/aggregate/cement/gypsum/paste visual resources.
Physical facts are source and condition attached; visual states do not mutate these facts.
This is not a plugin contract or a native SolidCraft importer.
"""
import argparse, hashlib, json, math, os, pathlib, struct, io
import numpy as np
import cv2
from PIL import Image, ImageDraw
import trimesh

ROOT=pathlib.Path(__file__).resolve().parents[1]
SOURCE={
 'soil-nrcs':('USDA NRCS, Soil Quality Indicators: Bulk Density','https://www.nrcs.usda.gov/sites/default/files/2023-01/Soil%20Quality-Indicators-Bulk%20Density.pdf','Definitions and distinctions of dry bulk and mineral particle density'),
 'soil-mn':('Minnesota Pollution Control Agency, Soil physical properties and processes','https://stormwater.pca.state.mn.us/soil_physical_properties_and_processes','Comparison of undisturbed/urban-condition bulk density ranges, based on Schueler 2000'),
 'cement-aci':('American Concrete Institute, definition of Portland cement','https://www.concrete.org/frequentlyaskedquestions/faqid/671.aspx','Typical Portland cement particle specific gravity, not powder loose bulk density'),
 'quikrete-1101':('QUIKRETE Concrete Mix #1101 product specification','https://www.quikrete.com/pdfs/spec_data-concretemix.pdf','Compressive strength after 7/28-day curing in specified lab context'),
 'quikrete-mortar':('QUIKRETE masonry and mortar selector','https://www.quikrete.com/pdfs/mortarselectorguide.pdf','Type S and N 28-day laboratory compressive strength guidance'),
 'usg-hydrocal':('USG Hydrocal White Gypsum Cement Submittal IG1381','https://www.usg.com/content/dam/USG/pdpmovedocuments/hydrocal-white-gypsum-cement-data-en-IG1381.pdf','Wet and dry density and condition-specific compressive strengths'),
 'usg-gypsum':('USG Industrial Plasters & Gypsum Cements IG504','https://assemblies-tools.usg.com/content/dam/USG_Marketing_Communications/united_states/product_promotional_materials/finished_assets/industrial-plasters-gypsum-cements-brochure-en-IG504.pdf','Ceramical wet/dry density and compressive strengths'),
 'usg-joint':('USG Sheetrock All Purpose Joint Compound','https://www.usg.com/en-US/p/product/sheetrock-brand-all-purpose-joint-compound-380270','Product identity and use, not a material density or certified compressive strength'),
}
# (slug, name, family, RGB sRGB palette, source, state, property specifications)
# Property: (quantity, value or [lower,upper] or None, unit, qualifier, conditions)
P=[
('peat-undisturbed','Peat soil / undisturbed','soil',(61,49,36),'soil-mn','Undisturbed peat; dry bulk density envelope', [('dry_bulk_density',[200,300],'kg/m3','published range','reference condition; not specific site measurement')]),
('sandy-undisturbed','Sandy soil / undisturbed','soil',(165,143,105),'soil-mn','Undisturbed sandy soil, not loose industrial sand',[('dry_bulk_density',[1100,1300],'kg/m3','published range','reference condition; site variation')]),
('silty-sand','Silty sand / reference','soil',(132,115,89),'soil-mn','Undisturbed silty sands',[('dry_bulk_density',1400,'kg/m3','typical example','not a permitted universal value')]),
('silt','Silt / reference','soil',(153,140,112),'soil-mn','Undisturbed silt',[('dry_bulk_density',[1300,1400],'kg/m3','published range','reference condition')]),
('silt-loam','Silt loam / undisturbed','soil',(113,104,77),'soil-mn','Undisturbed silt loam',[('dry_bulk_density',[1200,1500],'kg/m3','published range','reference condition')]),
('organic-silt-clay','Organic silt/clay soil','soil',(64,60,44),'soil-mn','Organic silt or clay, variable organic fraction',[('dry_bulk_density',[1000,1200],'kg/m3','published range','reference condition')]),
('glacial-till','Glacial till / reference','soil',(119,107,92),'soil-mn','Undisturbed glacial till, mixed clasts',[('dry_bulk_density',[1600,2000],'kg/m3','published range','reference condition')]),
('urban-fill','Urban fill / compacted reference','soil',(124,106,82),'soil-mn','Urban fill soil, site and compaction dependent',[('dry_bulk_density',[1800,2000],'kg/m3','published range','reference condition')]),
('clay-loam','Clay loam / visual archetype','soil',(121,88,65),'soil-nrcs','Illustrative clay-loam identity only, no exact site measurement',[('dry_bulk_density',None,'kg/m3','unknown','needs measured specimen at known porosity and water content')]),
('red-earth','Iron-rich red earth / visual archetype','soil',(142,73,52),'soil-nrcs','Color archetype not chemical identification',[('dry_bulk_density',None,'kg/m3','unknown','no source linked to this specific colored soil')]),
('quartz-grains','Quartz-rich sand / mineral grains','aggregate',(198,174,130),'soil-nrcs','Mineral particle reference, not loose granular bulk density',[('mineral_particle_density',2650,'kg/m3','typical reference','mineral solids only; actual grading and mineralogy vary')]),
('washed-river-sand','Washed river sand / visual archetype','aggregate',(189,170,142),'soil-nrcs','Loose aggregate texture, no supplier batch',[('loose_bulk_density',None,'kg/m3','unknown','grain size, gradation and moisture unspecified')]),
('granite-gravel','Crushed granite gravel / visual archetype','aggregate',(141,137,127),'soil-nrcs','Crushed rock texture, no quarry grading or measured density',[('aggregate_bulk_density',None,'kg/m3','unknown','specific stone and packing not established')]),
('limestone-chips','Crushed limestone / visual archetype','aggregate',(191,189,171),'soil-nrcs','Crushed stone texture, no limestone composition certified',[('aggregate_bulk_density',None,'kg/m3','unknown','quarry/product not identified')]),
('compacted-rock-base','Compacted crushed rock base','aggregate',(130,128,119),'soil-mn','Crushed rock parking-lot subbase condition',[('dry_bulk_density',[1500,2000],'kg/m3','published range','particular compacted aggregate application')]),
('portland-cement-powder','Portland cement powder / typical','cement',(167,166,157),'cement-aci','Typical cement mineral particles, not a bulk loose powder sample',[('particle_density',3150,'kg/m3','approximation','specific gravity about 3.15, not sack loose density')]),
('quikrete-concrete-1101','QUIKRETE Concrete Mix #1101','cement',(137,135,126),'quikrete-1101','Product reference with stated lab curing, visually generic concrete',[('compressive_strength_7d',17.2e6,'Pa','typical lab result','ASTM C387 7 days'),('compressive_strength_28d',27.6e6,'Pa','typical lab result','ASTM C387 28 days'),('cured_bulk_density',None,'kg/m3','unknown','no transferable point density in selected sheet')]),
('quikrete-mortar-type-n','QUIKRETE Mortar Mix #1102 Type N','cement',(162,156,139),'quikrete-mortar','Type N 28-day minimum category, sample-specific cure not captured',[('compressive_strength_28d',5.2e6,'Pa','minimum Type N reference','28-day laboratory mortar, not every installed joint'),('cured_bulk_density',None,'kg/m3','unknown','actual mix water and voids missing')]),
('quikrete-mason-type-s','QUIKRETE Mason Mix Type S','cement',(155,151,137),'quikrete-mortar','Type S 28-day minimum category',[('compressive_strength_28d',12.4e6,'Pa','minimum Type S reference','28-day laboratory mortar'),('cured_bulk_density',None,'kg/m3','unknown','not measured')]),
('poured-concrete-generic','Architectural cast concrete / visual archetype','cement',(146,143,136),'quikrete-1101','No identified project mix, visual finish only',[('cured_bulk_density',None,'kg/m3','unknown','concrete density requires specified aggregate/mix/air'),('compressive_strength',None,'Pa','unknown','product-specific result cannot be borrowed')]),
('gypsum-hydrocal-dry','USG Hydrocal White / dry cast','gypsum',(211,209,200),'usg-hydrocal','Dry cast gypsum cement; not loose powder',[('dry_cast_density',1442,'kg/m3','typical lab','dry cast'),('compressive_strength_dry',41.4e6,'Pa','typical lab','dry specimen')]),
('gypsum-hydrocal-green','USG Hydrocal White / 1h after set','gypsum',(220,217,207),'usg-hydrocal','Green cast one hour after setting, not fresh liquid slurry',[('wet_cast_density',1762,'kg/m3','typical lab','wet gypsum casting'),('compressive_strength_1h_after_set',20.7e6,'Pa','typical lab','one hour after set')]),
('gypsum-ceramical-dry','USG Ceramical / dry cast','gypsum',(225,219,209),'usg-gypsum','Dry casting reference, selected USG brochure',[('dry_cast_density',96*16.018463,'kg/m3','converted from lb/ft3','dry cast'),('compressive_strength_dry',10000*6894.7573,'Pa','converted from psi','dry cast')]),
('gypsum-ceramical-wet','USG Ceramical / wet cast','gypsum',(218,215,208),'usg-gypsum','Wet casting reference before drying',[('wet_cast_density',113*16.018463,'kg/m3','converted from lb/ft3','wet casting'),('compressive_strength_1h_after_set',4000*6894.7573,'Pa','converted from psi','one hour after set')]),
('clay-slip','Clay slip / visual archetype','paste',(136,105,78),'soil-nrcs','Water-bearing suspension, formulation unknown',[('wet_mix_density',None,'kg/m3','unknown','solids fraction, mineral mix and water content unspecified')]),
('earthenware-clay','Earthenware forming clay / visual archetype','paste',(160,112,87),'soil-nrcs','Plastic clay under forming, no firing or composition specified',[('wet_mix_density',None,'kg/m3','unknown','formulation not known')]),
('cement-paste','Hydrated cement paste / visual archetype','paste',(155,155,146),'cement-aci','Mixed cement and water, w/c and hydration unknown',[('wet_mix_density',None,'kg/m3','unknown','mix proportion and aeration unspecified')]),
('ready-joint-compound','USG Sheetrock All Purpose / wet paste','paste',(208,206,198),'usg-joint','Ready-mixed drying joint compound; particular published product',[('wet_mix_density',None,'kg/m3','unknown','no density specified in cited manufacturer description')]),
]
# Six variants per family. Decorative states are NOT measured physical conditions.
R={
 'soil':['loose-granular','lightly-tamped','damp-darkened','dry-cracked','wind-rippled','rake-tracked'],
 'aggregate':['loose-granular','graded-spread','wet-surface','rake-tracked','exposed-stones','tumbled-stones'],
 'cement':['as-cast','broom-finished','form-board','trowelled','exposed-stones','weathered-cracks'],
 'gypsum':['smooth-cast','float-finish','tool-scraped','chipped','hand-brushed','fine-sanded'],
 'paste':['fresh-smooth','spatula-lines','swirled','hand-brushed','air-dried','surface-crusted'],
}
FAMILY_SCALE={'soil':(400.0,400.0),'aggregate':(180.,180.),'cement':(240.,240.),'gypsum':(150.,150.),'paste':(120.,120.)}
HEIGHT_MAX={'soil':5.0,'aggregate':6.0,'cement':3.2,'gypsum':1.2,'paste':2.0}
BASE_ROUGH={'soil':.92,'aggregate':.87,'cement':.85,'gypsum':.78,'paste':.76}

def writejson(p,obj):
 p=pathlib.Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n')
def digest(f):
 h=hashlib.sha256();
 with open(f,'rb') as fp:
  for b in iter(lambda: fp.read(1048576),b''):h.update(b)
 return h.hexdigest()
def resized_noise(n,seed,div):
 rng=np.random.default_rng(seed);k=max(3,int(n/div));small=rng.random((k,k),dtype=np.float32)
 return cv2.resize(small,(n,n),interpolation=cv2.INTER_CUBIC).clip(0,1)
def texture(fam,fin,n):
 seed=int(hashlib.sha256(f'{fam}/{fin}/render-04'.encode()).hexdigest()[:8],16)
 a=resized_noise(n,seed,100);b=resized_noise(n,seed+1,25);c=resized_noise(n,seed+2,5);d=resized_noise(n,seed+3,1.4)
 phi=(a-.5)*2
 out=.22*(a-.5)+.17*(b-.5)+.065*(c-.5)+.018*(d-.5)
 yy,xx=np.mgrid[0:n,0:n].astype(np.float32)
 u=xx/n;v=yy/n
 if fam in ('aggregate','soil') or (fam=='cement' and fin=='exposed-stones'):
  rng=np.random.default_rng(seed+11);grains=np.zeros((n,n),np.float32)
  count=int(n*n/(3800 if fam=='aggregate' else (6600 if fam=='soil' else 1800)))
  for _ in range(count):
   x=int(rng.integers(0,n));y=int(rng.integers(0,n));rad=max(1,int(rng.lognormal(np.log(n/160),.43)))
   cv2.ellipse(grains,(x,y),(rad,int(rad*rng.uniform(.5,1.15))),int(rng.integers(0,180)),0,360,float(rng.uniform(.3,1.0)),-1,cv2.LINE_AA)
  out+=.44*grains+.12*(c-.5)
 if fam=='cement':
  out+=.05*(a-.5)+.08*(b-.5)
 if fam in ('paste','gypsum'):
  out+=.12*(b-.5)
 if 'tamp' in fin or 'graded' in fin:out*=.58
 if 'damp' in fin or 'wet' in fin:out=out*.54+.07*(c-.5)
 if 'ripple' in fin:out+=.16*np.sin((v*60+phi*4)*np.pi)
 if 'rake' in fin:out+=.13*np.cos((u*32+phi*2)*np.pi)
 if fin in ('broom-finished','hand-brushed','tool-scraped','spatula-lines'):
  out+=.14*np.cos((u*(130 if 'broom' in fin else 34)+.6*phi)*np.pi)
 if fin=='form-board':out+=.20*np.sin((u*4+phi*.1)*np.pi)+.06*np.cos(v*5*np.pi)
 if fin in ('trowelled','float-finish','smooth-cast','fresh-smooth','fine-sanded'):out*=.35
 if 'swirl' in fin:
  r=np.hypot(u-.5,v-.5);ang=np.arctan2(v-.5,u-.5)
  out+=.19*np.sin(25*r+ang*3+phi)
 if fin in ('dry-cracked','weathered-cracks','surface-crusted','air-dried'):
  image=(cv2.GaussianBlur((b*255).astype(np.uint8),(0,0),1.5))
  edges=cv2.Canny(image,45,70).astype(np.float32)/255
  edges=cv2.GaussianBlur(edges,(0,0),n/2048*1.8)
  out-=.65*edges
 if fin in ('exposed-stones','chipped','tumbled-stones'):out+=.28*(c-.5)+.15*np.maximum(d-.55,0)
 if fin=='fine-sanded':out+=.016*(d-.5)
 lo,hi=float(np.min(out)),float(np.max(out));out=((out-lo)/(max(hi-lo,1e-5))-.5)
 # Patches carry absolute physical height in mm, all within [-HEIGHT_MAX, +HEIGHT_MAX].
 height=(out*HEIGHT_MAX[fam]*.75).astype(np.float32)
 shade=np.clip(.88+.19*(b-.5)+.18*(c-.5),.62,1.12).astype(np.float32)
 rough=np.clip(BASE_ROUGH[fam]+.16*(d-.5),.34,.99).astype(np.float32)
 if fin in ('fine-sanded','trowelled','smooth-cast','fresh-smooth'):rough=np.clip(rough-.18,.2,.95)
 if 'wet' in fin or 'damp' in fin:rough=np.clip(rough-.25,.14,.9)
 return height,shade,rough

def srgb(x):
 return np.where(x<=.0031308,12.92*x,1.055*np.maximum(x,0)**(1/2.4)-.055)
def linear(x):
 return np.where(x<=.04045,x/12.92,((x+.055)/1.055)**2.4)
def save_map(folder,n,height,shade,rough,scale_mm):
 folder.mkdir(parents=True,exist_ok=True)
 # Grayscale albedo modulation encoded in sRGB. Color comes from the linked physical record's illustrative palette.
 albedo=np.uint8(np.round(255*np.clip(srgb(np.clip(shade*.78,0,1)),0,1)))
 bc=np.repeat(albedo[:,:,None],3,axis=2)
 gx=np.gradient(height,scale_mm[0]/n,axis=1);gy=np.gradient(height,scale_mm[1]/n,axis=0)
 normals=np.stack((-gx,gy,np.ones_like(gx)),axis=2)
 normals/=np.linalg.norm(normals,axis=2)[:,:,None]
 ng=np.uint8(np.round(np.clip((normals*.5+.5)*255,0,255)))
 nd=ng.copy();nd[:,:,1]=255-nd[:,:,1]
 r=np.uint8(np.round(255*rough));m=np.zeros_like(r)
 orm=np.stack([np.full_like(r,255),r,m],axis=2)
 height16=np.uint16(np.round(np.clip((height+8)/16,0,1)*65535))
 images={'base_color':bc,'normal_opengl':ng,'normal_directx':nd,'roughness':r,'metallic':m,'orm':orm,'height_mm_u16':height16}
 for k,a in images.items():
  Image.fromarray(a).save(folder/(k+'.png'),compress_level=4)
 os.environ['OPENCV_IO_ENABLE_OPENEXR']='1'
 cv2.imwrite(str(folder/'height_mm.exr'),height)
 return images

def make_gltf(out_dir,color,base,orm,normal,scale_mm,title,prof):
 out_dir.mkdir(parents=True,exist_ok=True)
 # Two separate open coupons: a flat panel and a gently curved segment, geometric units in metres.
 W,H=scale_mm[0]/1000,scale_mm[1]/1000
 verts=np.array([[0,0,0],[W,0,0],[W,H,0],[0,H,0]],float)
 faces=np.array([[0,1,2],[0,2,3]])
 uv=np.array([[0,1],[1,1],[1,0],[0,0]],float)
 mat=trimesh.visual.material.PBRMaterial(name=title,baseColorFactor=[*list(np.uint8(np.round(255*linear(np.array(color,dtype=np.float32)/255)))),255],baseColorTexture=Image.fromarray(base),metallicRoughnessTexture=Image.fromarray(orm),normalTexture=Image.fromarray(normal),metallicFactor=0.0,roughnessFactor=1.0,doubleSided=True)
 plane=trimesh.Trimesh(vertices=verts,faces=faces,process=False)
 plane.visual=trimesh.visual.texture.TextureVisuals(uv=uv,material=mat)
 # Low curvature in local units; separate coupon shifted +X with UV matching top-left mapping.
 v2=[];u2=[];f2=[]
 columns=32;rows=8;radius=.15
 for row in range(rows+1):
  for col in range(columns+1):
   a=(col/columns-.5)*W/radius
   v2.append([W*1.2+radius*np.sin(a),row/rows*H,radius*(1-np.cos(a))])
   u2.append([col/columns,1-row/rows])
 for row in range(rows):
  for col in range(columns):
   a=row*(columns+1)+col;b=a+columns+1
   f2.extend([[a,a+1,b+1],[a,b+1,b]])
 curved=trimesh.Trimesh(vertices=np.array(v2),faces=np.array(f2),process=False)
 curved.visual=trimesh.visual.texture.TextureVisuals(uv=np.array(u2),material=mat)
 scene=trimesh.Scene();scene.add_geometry(plane,node_name='flat-finite-coupon');scene.add_geometry(curved,node_name='curved-finite-coupon')
 glb=trimesh.exchange.gltf.export_glb(scene,include_normals=True)
 (out_dir/'material.glb').write_bytes(glb)
 gltf=trimesh.exchange.gltf.export_gltf(scene,include_normals=True,merge_buffers=True)
 for name,data in gltf.items():
  (out_dir/name).write_bytes(data)
 gltf_name=next(k for k in gltf if k.endswith('.gltf'))
 if gltf_name!='material.gltf':(out_dir/gltf_name).rename(out_dir/'material.gltf')
 writejson(out_dir/'resource.json',{'title':title,'physical_profile_id':prof,'visual_palette_srgb':color,'finite_patch_mm':scale_mm,'app_native_acceptance':'not_run','premium_qualification':'pending','formats':['glb','gltf'],'not_seamless':True,'not_engineering_material_assignment':True})

def preview(path,height,shade,rough,color):
 # Software mockup: normal-derived relief and colored macro swatch; NOT a native renderer image.
 h,w=height.shape
 hh=cv2.resize(height,(300,300),interpolation=cv2.INTER_AREA)
 ss=cv2.resize(shade,(300,300),interpolation=cv2.INTER_AREA)
 rr=cv2.resize(rough,(300,300),interpolation=cv2.INTER_AREA)
 gx,gy=np.gradient(hh)
 light=np.maximum(0.24,(.4-.55*gx+.65*gy)/np.sqrt(1+gx*gx+gy*gy))
 factor=np.stack(color)/255
 patch=np.clip(srgb(linear(factor)[None,None,:]*linear(ss)[:,:,None]*(.55+.6*light[:,:,None]) + (1-rr[:,:,None])*.045),0,1)
 sw=(patch*255).astype('uint8');im=Image.new('RGB',(560,330),(20,23,29));im.paste(Image.fromarray(sw),(15,15))
 strip=Image.fromarray(np.uint8(np.round(np.clip(srgb(linear(factor)[None,None,:]*ss[:,:,None]*.9),0,1)*255)))
 im.paste(strip.resize((215,260)),(330,32))
 dr=ImageDraw.Draw(im);dr.rectangle((326,286,549,310),fill=(30,33,40))
 dr.text((335,291),'Software preview - not native',fill=(205,211,221))
 path.parent.mkdir(parents=True,exist_ok=True);im.save(path)

def main():
 pa=argparse.ArgumentParser();pa.add_argument('--size',type=int,default=2048);args=pa.parse_args()
 n=args.size
 if n not in [256,512,1024,2048]:raise SystemExit('allowed bounded texture resolution: 256,512,1024,2048')
 profiles=[];variants=[]
 for slug,name,fam,col,src,state,prop in P:
  properties=[{'quantity':q,'value':value,'unit':unit,'qualifier':qual,'conditions':cond,'source_id':src,'source_url':SOURCE[src][1],'kind':'range' if isinstance(value,list) else ('missing' if value is None else 'point')} for q,value,unit,qual,cond in prop]
  profiles.append({'id':'earth.'+slug,'name':name,'family':fam,'source_id':src,'identity_state':state,'appearance_palette_srgb':col,'physical_properties':properties,'physical_assignment':'explicit_user_selection_only','visual_finish_not_physical_measurement':True})
  for fin in R[fam]:
   variants.append({'id':'earth.'+slug+'.'+fin,'name':name+' / '+fin,'physical_profile_id':'earth.'+slug,'mapset_id':fam+'.'+fin,'family':fam,'finish':fin,'appearance_status':'generated_authoring_candidate','premium_qualification':'pending'})
 writejson(ROOT/'data/sources.json',{k:{'title':v[0],'url':v[1],'locator':v[2]} for k,v in SOURCE.items()})
 writejson(ROOT/'data/physical-profiles.json',{'profiles':profiles})
 writejson(ROOT/'data/material-variants.json',{'items':variants})
 writejson(ROOT/'data/process-recipes.json',{'processes':[{'id':fam+'.'+fin,'family':fam,'name':fin,'patch_mm':FAMILY_SCALE[fam],'status':'illustrative, not measurement; no mechanical property mutation'} for fam,ls in R.items() for fin in ls]})
 mapindex={}
 for j,(fam,fin) in enumerate((f,t) for f in R for t in R[f]):
  H,S,Q=texture(fam,fin,n)
  if not np.isfinite(H).all():raise RuntimeError('height not finite')
  base=ROOT/'build/maps'/fam/fin
  master=base/('master-%d'%n)
  save_map(master,n,H,S,Q,FAMILY_SCALE[fam]);mapindex[fam+'.'+fin]={'master':master.relative_to(ROOT).as_posix(),'size':n}
  if n>=512:
   # Recompute normals from *downsampled physical height*, not normal-vector averaging.
   runtime=base/('runtime-%d'%(n//2));hh=cv2.resize(H,(n//2,n//2),interpolation=cv2.INTER_AREA);ss=cv2.resize(S,(n//2,n//2),interpolation=cv2.INTER_AREA);rr=cv2.resize(Q,(n//2,n//2),interpolation=cv2.INTER_AREA)
   save_map(runtime,n//2,hh,ss,rr,FAMILY_SCALE[fam]);mapindex[fam+'.'+fin]['runtime']=runtime.relative_to(ROOT).as_posix()
  print('MAPSET',j+1,len(mapindex),fam,fin,flush=True)
 for j,v in enumerate(variants):
  slug=v['physical_profile_id'][len('earth.'):];p=next(x for x in profiles if x['id']==v['physical_profile_id']);fam=p['family'];fin=v['finish'];m=ROOT/mapindex[v['mapset_id']].get('runtime',mapindex[v['mapset_id']]['master']);
  base=np.asarray(Image.open(m/'base_color.png').convert('RGB'));orm=np.asarray(Image.open(m/'orm.png').convert('RGB'));normal=np.asarray(Image.open(m/'normal_directx.png').convert('RGB'))
  out=ROOT/'build/materials'/v['id'];make_gltf(out,p['appearance_palette_srgb'],base,orm,normal,FAMILY_SCALE[fam],v['name'],p['id']);
  height=cv2.imread(str(m/'height_mm.exr'),cv2.IMREAD_UNCHANGED)
  preview(out/'preview.png',height,np.asarray(Image.open(m/'base_color.png').convert('L'),dtype=np.float32)/255,np.asarray(Image.open(m/'roughness.png'),dtype=np.float32)/255,p['appearance_palette_srgb'])
  if (j+1)%30==0:print('APPEARANCES',j+1,len(variants),flush=True)
 writejson(ROOT/'registry/resource-index.json',{'purpose':'internal resource index, not a plugin format','items':variants,'physical_profiles':len(profiles),'mapsets':mapindex,'native_acceptance':'not_run','premium_qualification':'pending'})
 # Browsable offline HTML index with relative images, no online requirements.
 rows=[]
 for v in variants:
  p=next(x for x in profiles if x['id']==v['physical_profile_id']);fname=v['id'];title=v['name'];pic=f'build/materials/{fname}/preview.png'
  rows.append('<article data-group="%s"><img loading="lazy" src="%s"><h3>%s</h3><p>%s</p><a href="%s">GLB sample</a> | <a href="%s">Physical record</a></article>'%(v['family'],pic,title,p['identity_state'],f'build/materials/{fname}/material.glb','data/physical-profiles.json'))
 htm='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Earth & Masonry — Stage 04</title><style>body{background:#101419;color:#e6ecf2;font:14px system-ui;padding:24px}header{position:sticky;top:0;background:#101419;padding:12px 0;z-index:10}h1{font-size:25px}input{background:#26313b;border:1px solid #4b6272;padding:10px;color:white;width:300px}#g{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:15px}article{background:#202832;padding:12px;border-radius:10px}img{width:100%;border-radius:6px}h3{font-size:14px}a{color:#9fc9ef}</style><header><h1>Earth & Masonry | Authoring Stage 04</h1><p>Physical references and illustrated surface treatments are separate. Non-native previews; no premium/native qualification or plugin standard.</p><input id="search" placeholder="Search materials, finishes…" oninput="filter()"> <select id="group" onchange="filter()"><option value="">All families</option>'''+''.join(f'<option>{f}</option>' for f in R)+'''</select></header><main id="g">'''+''.join(rows)+'''</main><script>function filter(){let q=document.getElementById('search').value.toLowerCase(),g=document.getElementById('group').value;document.querySelectorAll('article').forEach(a=>a.hidden=!(a.innerText.toLowerCase().includes(q)&&(!g||a.dataset.group===g)))}</script></html>'''
 (ROOT/'index.html').write_text(htm)
 writejson(ROOT/'reports/summary.json',{'status':'GENERATED','profiles':len(profiles),'variants':len(variants),'mapsets':len(mapindex),'size_master':n,'size_runtime':n//2,'sources':len(SOURCE),'native_acceptance':'not_run','premium_qualification':'pending','plugin_standard':None})
 print('STAGE04_GENERATED',len(profiles),len(variants),len(mapindex),flush=True)
if __name__=='__main__':main()