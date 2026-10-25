"""Create a staged authoring workspace, never a SolidCraft plugin contract."""
from pathlib import Path
import json, hashlib, subprocess, collections
A=Path(__file__).resolve().parents[1]
R=A.parents[1]
for d in ['data','tools','tests','reports','registry','docs']: (A/d).mkdir(parents=True,exist_ok=True)
def put(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
columns=['specific_gravity_g12','bending_mor_kpa','bending_moe_mpa','work_to_max_load_kj_m3','impact_bending_mm','compression_parallel_kpa','compression_perpendicular_proportional_limit_kpa','shear_parallel_kpa','tension_perpendicular_kpa','side_hardness_n']
# Transcribed from the metric, 12-percent-moisture rows, not the green rows.
# Page numbers are the printed chapter pages. Source screenshots were inspected.
rows=[
('red-alder','Red alder','5-4',[.41,68000,9500,58,510,40100,3000,7400,2900,2600],[194,143,96],[121,75,45],'diffuse',2.5,.2),
('white-ash','White ash','5-4',[.60,106000,12000,115,1090,51100,8000,13200,6500,5900],[200,171,120],[113,77,42],'ring',3.4,.35),
('american-basswood','American basswood','5-4',[.37,60000,10100,50,410,32600,2600,6800,2400,1800],[221,201,161],[173,144,99],'diffuse',2.2,.08),
('american-beech','American beech','5-4',[.64,103000,11900,104,1040,50300,7000,13900,7000,5800],[213,172,135],[156,106,77],'diffuse',2.1,.28),
('yellow-birch','Yellow birch','5-4',[.62,114000,13900,143,1400,56300,6700,13000,6300,5600],[216,182,139],[149,104,69],'diffuse',2.1,.12),
('black-cherry','Black cherry','5-4',[.50,85000,10300,79,740,49000,4800,11700,3900,4200],[179,114,77],[102,49,28],'diffuse',2.7,.12),
('american-elm','American elm','5-4',[.50,81000,9200,90,990,38100,4800,10400,4600,3700],[184,144,91],[100,66,35],'ring',3.1,.17),
('shagbark-hickory','Shagbark hickory','5-5',[.72,139000,14900,178,1700,63500,12100,16800,None,8400],[209,175,124],[123,79,45],'ring',3.0,.16),
('sugar-maple','Sugar maple','5-5',[.63,109000,12600,114,990,54000,10100,16100,None,6400],[224,200,154],[174,141,93],'diffuse',1.9,.11),
('northern-red-oak','Northern red oak','5-5',[.63,99000,12500,100,1090,46600,7000,12300,5500,5700],[192,146,102],[113,68,40],'ring',3.6,.72),
('white-oak','White oak','5-6',[.68,105000,12300,102,940,51300,7400,13800,5500,6000],[183,152,105],[103,73,41],'ring',3.2,.95),
('black-walnut','Black walnut','5-6',[.55,101000,11600,74,860,52300,7000,9400,4800,4500],[119,87,61],[58,37,24],'semi-ring',3.1,.2),
('western-redcedar','Western redcedar','5-7',[.32,51700,7700,40,430,31400,3200,6800,1500,1600],[185,122,76],[102,57,31],'softwood',3.0,.08),
('douglas-fir-coast','Douglas-fir (Coast)','5-7',[.48,85000,13400,68,790,49900,5500,7800,2300,3200],[214,169,103],[128,76,35],'softwood',3.9,.08),
('eastern-white-pine','Eastern white pine','5-7',[.35,59000,8500,47,460,33100,3000,6200,2100,1700],[227,202,145],[166,120,61],'softwood',4.4,.06),
('loblolly-pine','Loblolly pine','5-7',[.51,88000,12300,61,760,49200,5400,9600,2300,3100],[215,179,109],[132,83,35],'softwood',3.7,.06)]
sources={
'usda-fpl-2021-ch5':{'title':'Wood Handbook, FPL-GTR-282, Chapter 5: Mechanical Properties of Wood','authors':['C. Adam Senalik','Benjamin Farber'],'year':2021,'url':'https://research.fs.usda.gov/download/treesearch/62244.pdf','landing_page':'https://research.fs.usda.gov/treesearch/62244','locator':'Table 5-3a, metric rows at 12% moisture, printed pages 5-4 through 5-7; footnotes on 5-8','source_kind':'primary_government_handbook','reviewed_on':'2026-10-25','review':'Original metric table pages inspected as images. White-ash MOR is 106000 kPa, not the superseded 103000 value.','rights':'Numerical factual transcription; no source figures or publisher artwork redistributed.'},
'usda-fpl-2021-ch4':{'title':'Wood Handbook, FPL-GTR-282, Chapter 4: Moisture Relations and Physical Properties of Wood','authors':['Samuel V. Glass','Samuel L. Zelinka'],'year':2021,'url':'https://research.fs.usda.gov/download/treesearch/62243.pdf','landing_page':'https://research.fs.usda.gov/treesearch/62243','locator':'Specific gravity and density definitions, printed page 4-11; Equation (4-14), printed page 4-12','source_kind':'primary_government_handbook','reviewed_on':'2026-10-25','rights':'Factual formula and numerical conversion; no source figures redistributed.'}}
units={'specific_gravity_g12':'1','bending_mor_kpa':'kPa','bending_moe_mpa':'MPa','work_to_max_load_kj_m3':'kJ/m3','impact_bending_mm':'mm','compression_parallel_kpa':'kPa','compression_perpendicular_proportional_limit_kpa':'kPa','shear_parallel_kpa':'kPa','tension_perpendicular_kpa':'kPa','side_hardness_n':'N'}
profiles=[]; woods=[]
for i,(slug,name,page,values,early,late,pores,ring,rays) in enumerate(rows):
    raw=dict(zip(columns,values)); props=[]
    for key,value in raw.items():
        factor=1000 if key.endswith('_kpa') or key.endswith('_kj_m3') else 1e6 if key.endswith('_mpa') else .001 if key.endswith('_mm') else 1
        unit='Pa' if key.endswith(('_kpa','_mpa')) else 'J/m3' if key.endswith('_kj_m3') else 'm' if key.endswith('_mm') else units[key]
        props.append({'quantity':key,'value':None if value is None else value*factor,'unit':unit,'status':'not_reported' if value is None else 'tabulated_average','source_id':'usda-fpl-2021-ch5','locator':f'Table 5-3a, {name}, 12% row, printed page {page}','original':{'value':value,'unit':units[key]},'conditions':{'moisture_dry_basis_kg_kg':.12,'temperature_k':None,'specimen':'clear straight-grained wood','structural_design_allowable':False},'uncertainty':None})
    rho=round(1000*raw['specific_gravity_g12']*1.12,6)
    props.append({'quantity':'density_at_12_percent_moisture','value':rho,'unit':'kg/m3','status':'derived_reference_estimate','source_ids':['usda-fpl-2021-ch5','usda-fpl-2021-ch4'],'locator':'Chapter 4 Equation (4-14), using the tabulated G12 directly','derivation':'1000 kg/m3 * G12 * (1 + 0.12)','inputs':{'G12':raw['specific_gravity_g12'],'moisture_dry_basis_kg_kg':.12,'water_reference_density_kg_m3':1000},'conditions':{'mass_basis':'wood including water at 12% dry-basis moisture','volume_basis':'volume at 12% moisture','temperature_k':None},'uncertainty':None})
    pid='wood.usda2021.'+slug
    profiles.append({'id':pid,'name':name,'family':'wood','phase':'solid','source_identity':name,'moisture_dry_basis_kg_kg':.12,'model':'orthotropic_reference_data_not_complete_constitutive_model','properties':props,'unknowns':['complete consistent orthotropic elasticity tensor','thermal properties not transcribed in this stage','coating mass and mechanical contribution','specimen-specific variability','exact product grade and botanical identification beyond handbook common-name scope'],'limitations':['Species averages for clear straight-grained specimens, not structural design allowables.','Bending MOE includes shear deflection; do not silently use it as an isotropic Young modulus.','G12 uses oven-dry mass and 12%-moisture volume; density is separately derived, not G12 times 1000.','Finish and grain-view changes do not modify this substrate record.','No physical material is assigned automatically.']})
    woods.append({'id':slug,'name':name,'physical_profile_id':pid,'seed':250100+i*971,'early_srgb':early,'late_srgb':late,'pore_style':pores,'ring_pitch_mm':ring,'ray_strength':rays,'appearance_basis':'original illustrative authoring, not measured reflectance or a botanical micrograph'})
put(A/'data/sources.json',sources)
put(A/'data/wood-table-transcription.json',{'source_id':'usda-fpl-2021-ch5','columns':columns,'rows':[{'id':r[0],'name':r[1],'printed_page':r[2],'values':r[3]} for r in rows]})
put(A/'data/physical-profiles.json',{'internal_authoring_revision':1,'plugin_standard':None,'profiles':profiles})
put(A/'data/woods.json',{'internal_authoring_revision':1,'woods':woods,'cuts':['plain-sawn','quarter-sawn','rift-sawn','end-grain'],'finite_patch_mm':[100,250],'end_grain_patch_mm':[100,100],'wrap':'clamp_to_edge','not_seamless':True})
finishes=[
{'id':'raw','name':'Raw / uncoated','color_multiplier_linear':[1,1,1],'roughness_factor':1.,'normal_scale':1.,'clearcoat':0.,'clearcoat_roughness':.4},
{'id':'fine-sanded','name':'Fine-sanded','color_multiplier_linear':[1,1,1],'roughness_factor':.83,'normal_scale':.58,'clearcoat':0.,'clearcoat_roughness':.4},
{'id':'oiled','name':'Oiled appearance','color_multiplier_linear':[.82,.76,.68],'roughness_factor':.62,'normal_scale':.75,'clearcoat':.12,'clearcoat_roughness':.32},
{'id':'waxed','name':'Waxed appearance','color_multiplier_linear':[.94,.91,.86],'roughness_factor':.55,'normal_scale':.45,'clearcoat':.25,'clearcoat_roughness':.26},
{'id':'satin-varnish','name':'Satin clear varnish appearance','color_multiplier_linear':[.91,.86,.77],'roughness_factor':.46,'normal_scale':.3,'clearcoat':.7,'clearcoat_roughness':.3},
{'id':'gloss-varnish','name':'Gloss clear varnish appearance','color_multiplier_linear':[.88,.83,.75],'roughness_factor':.22,'normal_scale':.15,'clearcoat':1.,'clearcoat_roughness':.075}]
put(A/'data/finishes.json',{'finishes':finishes,'basis':'Original optical authoring values, not measured coatings. Coating chemistry, density and thickness remain unspecified.','physical_policy':'Retain substrate reference; do not claim coated-composite properties or mass.'})
print('PREPARED',A,'species',len(woods),'looks',len(woods)*4*len(finishes))
