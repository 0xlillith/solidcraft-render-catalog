"""Source-backed FFF reference inputs; original texture choices are separate.
Values are factual transcriptions, not copies of manufacturer prose or artwork.
"""
from pathlib import Path
import json
ROOT = Path(__file__).resolve().parents[1]
VERSION = '0.1.0'
DATE = '2026-10-25'
BASE = 'https://storage.googleapis.com/prusa3d-content-prod-14e8-wordpress-prusament-prod/'
# name, chemistry, texture class, illustrative sRGB, source URL, version/date,
# density, HDT (.45/1.8 MPa), moisture (24h/7d), hardness D,
# filament yield, interlayer, printed yield H/V, tensile modulus H/V,
# flexural strength H/V, flexural modulus H/V, elongation at yield H/V.
ROWS = [
 ('pla','Prusament PLA','PLA','smooth',[198,80,48],'https://prusament.com/wp-content/uploads/2022/10/PLA_Prusament_TDS_2021_10_EN.pdf','1.1','2022-02-16',1.24,[55,55],[.13,.19],81,[57,1],[17,3],[[51,3],[59,2]],[[2.3,.1],[2.4,.1]],[[83,6],[99,1]],[[3.1,.1],[3.2,.1]],[[2.9,.3],[3.2,1.0]]),
 ('petg','Prusament PETG','PETG','smooth',[50,112,151],BASE+'2023/10/9f8d2165-tds_prusament-petg_n_en.pdf','1.1','2022-02-16',1.27,[68,68],[.07,.10],74,[46,1],[18,4],[[47,2],[50,1]],[[1.5,.1],[1.6,.1]],[[66,2],[70,1]],[[1.7,.1],[1.6,.1]],[[5.1,.1],[5.1,.1]]),
 ('asa','Prusament ASA','ASA','smooth',[185,189,191],BASE+'2024/05/bc8551ef-tds_prusament-asa_2024_en.pdf','1.1','2024-05-20',1.07,[93,86],[.16,.17],78,[40,1],[11,1],[[42,1],[45,2]],[[1.6,.1],[1.7,.1]],[[64,1],[69,1]],[[2.0,.1],[1.9,.1]],[[3.4,.2],[3.8,.2]]),
 ('pc-blend','Prusament PC Blend','PC blend','smooth',[68,77,86],'https://prusament.com/wp-content/uploads/2022/10/PCBlend_Prusament_TDS_2022_16_EN.pdf','1.1','2022-02-16',1.22,[113,93],[.13,.15],79,[58,1],[21,2],[[63,1],[63,1]],[[1.9,.1],[2.0,.1]],[[88,1],[94,2]],[[2.1,.1],[2.2,.1]],[[5.8,.3],[5.8,.2]]),
 ('pc-cf','Prusament PC Blend Carbon Fiber','PC blend + carbon fiber','fiber',[43,47,50],'https://prusament.com/wp-content/uploads/2023/04/TDS_Prusament-PCCF_2023_EN.pdf','2.0-OY','2023-04-19',1.22,[114,106],[.09,.11],83,[76,3],[23,2],[[64,3],[70,3]],[[2.6,.1],[3.2,.1]],[[94,3],[130,2]],[[3.5,.2],[4.2,.3]],[[4.6,.4],[3.7,.5]]),
 ('pa11-cf','Prusament PA11 Carbon Fiber','PA11 + carbon fiber','fiber',[48,49,47],'https://prusament.com/wp-content/uploads/2022/08/TDS_PA11CFB.pdf','1.0','2022-06-29',1.11,[192,152],[.20,.50],77,[61,3],[20,5],[[42,1],[49,2]],[[2.5,.1],[3.3,.1]],[[63,2],[103,3]],[[3.0,.1],[6.2,.3]],[[3.3,.2],[2.6,.3]]),
 ('pp-gf','Prusament PP Glass Fiber','PP + glass fiber','fiber',[151,154,146],BASE+'2025/07/512923fd-tds_pp_glass_fiber_en.pdf','1.0','2024-11-15',1.12,[138.3,112.6],[.11,.11],[68.5,.6],[46.6,1.3],[18,1],[[40.3,2.9],[48.8,2.8]],[[2.1,.1],[2.5,.1]],[[50.2,3.3],[70.4,5.3]],[[2.1,.1],[2.7,.5]],[[4.5,.1],[4.1,.2]]),
 ('pp-cf','Prusament PP Carbon Fiber','PP + carbon fiber','fiber',[44,47,48],BASE+'2025/01/b4ef2bf6-technical-data-sheet-1.pdf','1.0','2024-11-15',.91,[158,115],[.03,.04],62,[21,.4],[13,1],[[27.3,.7],[30.7,.3]],[[2.1,.1],[2.5,.1]],[[27.5,.7],[41.7,1.5]],[[1.8,.1],[3.4,.3]],[[3.4,.1],[3.2,.1]]),
 ('pvb','Prusament PVB','PVB','smooth',[117,157,142],'https://prusament.com/wp-content/uploads/2022/10/PVB_Prusament_TDS_2021_10_EN.pdf','1.1','2022-02-16',1.10,[63,58],[.18,.35],77,[57,1],[9,1],[[50,5],[49,5]],[[1.7,.1],[1.7,.1]],[[72,1],[73,3]],[[2.2,.1],[2.3,.1]],[[4.6,.7],[4.4,.7]]),
 ('woodfill','Prusament Woodfill Linden Light','Biobased polymer blend + wood','wood',[177,134,82],BASE+'2024/07/286c3bc0-tds_prusament_woodfill-linden-light_en.pdf','1.0','2024-07-24',1.16,[62.6,58.2],[.45,.82],67,[30,1],[7,1],[[21,1],[23,1]],[[.9,.1],[.8,.2]],[[30,1],[37,1]],[[1.4,.1],[1.9,.1]],[[4.3,.1],[4.1,.2]])
]
TPU_URL = BASE+'2025/05/80316f6d-tds-prusament_tpu_95a_en-1.pdf'
# Test settings below are measured-specimen context, NOT proposed slicing presets.
TEST_CONTEXT = {
 'pla':['Original Prusa i3 MK3','Slic3r Prusa Edition 1.40.0',215,60,200],
 'petg':['Original Prusa i3 MK3','Slic3r Prusa Edition 1.40.0',250,80,200],
 'asa':['Original Prusa i3 MK3S','Slic3r Prusa Edition 2.0.0',265,110,200],
 'pc-blend':['Original Prusa i3 MK3S','PrusaSlicer 2.1.1',275,115,200],
 'pc-cf':['Original Prusa i3 MK3S','PrusaSlicer 2.6.0',285,115,200],
 'pa11-cf':['Original Prusa i3 MK3S/S+','Slic3r Prusa Edition 2.4.2 (source label)',285,110,100],
 'pp-gf':['Original Prusa MK4S','PrusaSlicer 2.8.0',245,95,50],
 'pp-cf':['Original Prusa MK4','PrusaSlicer 2.7.4',270,85,40],
 'pvb':['Original Prusa i3 MK3S','PrusaSlicer 2.2.0',215,75,200],
 'woodfill':['Original Prusa i3 MK3S+','PrusaSlicer 2.7.4',195,60,200],
 'tpu-95a':['Original Prusa i3 MK4S','PrusaSlicer 2.8.1',220,75,36]
}
ADDITIONAL_CONTEXT = {
 'pc-blend':{'extrusion_multiplier':1.034,'cooling_percent':0},
 'pc-cf':{'extrusion_multiplier':1.07,'cooling_percent':0},
 'pp-gf':{'extrusion_multiplier':1.03,'infill_perimeter_overlap_percent':15,'cooling_percent':0},
 'pp-cf':{'extrusion_multiplier':1.09,'infill_perimeter_overlap_percent':40,'cooling_percent':0},
 'pvb':{'extrusion_multiplier':1.05,'cooling_percent':0,'drying_temperature_k':333.15,'drying_duration_h':8},
 'tpu-95a':{'nozzle_diameter_mm':.4,'nozzle_material':'brass','extrusion_multiplier':1.08,'cooling_percent':50,'source_additional_retraction_and_overhang_settings':'See TDS p.3; not reduced to a mechanical model.'}
}
COMMON_LIMITS = [
 'Manufacturer typical reference data, not engineering design allowables or identification of a printed part.',
 'Source orientation labels are preserved; Vertical xz is not silently mapped to build-Z tensile loading.',
 'A 0.20 mm / 100 percent infill test does not establish properties of every authored visual layer, infill or postprocess.',
 'The source +/- spread is retained; its statistical meaning is not assumed.',
 'HDT and Vicat are test results, not maximum continuous service temperatures.',
 'Palette, roughness and bump detail are original illustrative authoring, not measured optical constants.',
 'No printer compatibility, safety, chemical resistance or manufacturer endorsement is certified.'
]
def dump(path, value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
def context(key):
    machine,slicer,nozzle,bed,speed=TEST_CONTEXT[key]
    return {'printer':machine,'slicer':slicer,'layer_height_mm':.20,'infill_percent':100,'infill_pattern':'rectilinear','perimeters':2,'solid_top_layers':0,'solid_bottom_layers':0,'nozzle_temperature_k':nozzle+273.15,'bed_temperature_k':bed+273.15,'source_print_speed_mm_s':speed,'nozzle_diameter_mm':None,'source_locator':'p.3 specimen footnote','not_a_general_slicing_profile':True,**ADDITIONAL_CONTEXT.get(key,{})}
def prop(key, quantity, value, unit, method, scale=1, offset=0, **conditions):
    number,spread=(value if isinstance(value,list) else (value,None))
    return {'id':key,'quantity':quantity,'value':round(number*scale+offset,12),'unit':unit,
      'source_value':number,'source_spread':spread,'converted_spread':None if spread is None else spread*scale,
      'conversion':{'scale':scale,'offset':offset},'qualifier':'manufacturer_typical','method':method,
      'source_locator':'p.2 property table; p.3 for printed-specimen context','conditions':conditions,
      'statistical_interpretation_of_spread':None}
def profiles():
    out=[]
    for row in ROWS:
        key,name,chem,grain,color,url,version,date,density,hdt,moist,hard,fil,inter,yield_,mod,flex,fmod,elong=row
        sid='prusament-'+key+'-tds'
        P=[prop('density','material_density',density,'kg/m3','Prusa Polymers' if key in ('pc-blend','pc-cf','pvb') else 'ISO 1183',1000,source_unit='g/cm3',temperature_k=None,specimen_basis='material reference; not effective printed bulk density')]
        for i,hours in enumerate((24,168)):
            P.append(prop('uptake-'+str(hours),'moisture_absorption',moist[i],'kg/kg','Prusa Polymers',.01,source_unit='percent',duration_h=hours,temperature_k=298.15 if key in ('pp-cf','pp-gf') else 297.15,relative_humidity=.30 if key in ('pp-cf','pp-gf') else .22))
        for i,load in enumerate((.45,1.80)):
            P.append(prop('hdt-'+str(load),'heat_deflection_temperature',hdt[i],'K','ISO 75',1,273.15,source_unit='degC',bending_stress_pa=load*1e6))
        P.extend([prop('filament-yield','tensile_yield_strength',fil,'Pa','ISO 527',1e6,source_unit='MPa',specimen='filament'),prop('hardness-d','hardness_shore_d',hard,'Shore D','Prusa Polymers'),prop('interlayer','interlayer_adhesion',inter,'Pa','Prusa Polymers',1e6,source_unit='MPa',protocol_detail='Source internal method; not a full constitutive tensor')])
        for code,quantity,values,unit,scale,method,srcunit in [('printed-yield','tensile_yield_strength',yield_,'Pa',1e6,'ISO 527-1','MPa'),('printed-modulus','tensile_modulus',mod,'Pa',1e9,'ISO 527-1','GPa'),('printed-flexural-strength','flexural_strength',flex,'Pa',1e6,'ISO 178','MPa'),('printed-flexural-modulus','flexural_modulus',fmod,'Pa',1e9,'ISO 178','GPa'),('printed-yield-elongation','elongation_at_yield',elong,'1',.01,'ISO 527-1','percent')]:
            for j,orientation in enumerate(('Horizontal','Vertical xz')):
                P.append(prop(code+'-'+str(j),quantity,values[j],unit,method,scale,source_unit=srcunit,orientation_as_reported=orientation,specimen_context_id='test.'+key,temperature_k=None))
        for p in P:p['source_id']=sid
        out.append({'id':'physical.fff.prusament.'+key,'key':key,'name':name,'chemistry':chem,'filler_mass_fraction':None,'texture_class':grain,'appearance_palette_srgb':color,'source':{'id':sid,'url':url,'version':version,'dated':date,'accessed':DATE,'pages_reviewed':[1,2,3],'table_visually_verified':True,'redistributed_document':False},'specimen_context':context(key),'properties':P,'effective_printed_density_kg_m3':None,'full_mechanical_model':None,'limitations':COMMON_LIMITS.copy()})
    sid='prusament-tpu-95a-tds'
    P=[prop('density','material_density',1.25,'kg/m3','ISO 1183',1000,source_unit='g/cm3',temperature_k=None,specimen_basis='material reference; not effective printed bulk density'),prop('vicat-a','vicat_softening_temperature',101.6,'K','ISO 306',1,273.15,source_unit='degC',source_variant='A'),prop('hdt-1.8','heat_deflection_temperature',78.6,'K','ISO 75',1,273.15,source_unit='degC',bending_stress_pa=1.8e6),prop('hardness-a','hardness_shore_a',[92,.4],'Shore A','Prusa Polymers'),prop('hardness-d','hardness_shore_d',[39,.7],'Shore D','Prusa Polymers'),prop('filament-strength','tensile_strength',[64,3],'Pa','ISO 527',1e6,source_unit='MPa',specimen='filament'),prop('interlayer','interlayer_adhesion',[9.5,.2],'Pa','ISO 527',1e6,source_unit='MPa')]
    for hrs,x in [(24,.02),(168,.04)]:P.append(prop('uptake-'+str(hrs),'moisture_absorption',x,'kg/kg','Prusa Polymers',.01,source_unit='percent',duration_h=hrs,temperature_k=298.15,relative_humidity=.20))
    for key,q,val,u,sc,srcu in [('printed-strength','tensile_strength',[41.4,1.3],'Pa',1e6,'MPa'),('stress100','stress_at_100_percent_elongation',[8.9,.2],'Pa',1e6,'MPa'),('stress200','stress_at_200_percent_elongation',[14.7,.2],'Pa',1e6,'MPa'),('stress300','stress_at_300_percent_elongation',[21.3,.4],'Pa',1e6,'MPa'),('printed-elongation','elongation_maximum',[563.3,13.1],'1',.01,'percent')]:P.append(prop(key,q,val,u,'ISO 37',sc,source_unit=srcu,orientation_as_reported='Horizontal',specimen_context_id='test.tpu-95a',temperature_k=None))
    for p in P:p['source_id']=sid
    out.append({'id':'physical.fff.prusament.tpu-95a','key':'tpu-95a','name':'Prusament TPU 95A','chemistry':'Thermoplastic polyurethane','filler_mass_fraction':None,'texture_class':'smooth','appearance_palette_srgb':[60,67,75],'source':{'id':sid,'url':TPU_URL,'version':'1.0','dated':'2025-05-29','accessed':DATE,'pages_reviewed':[1,2,3],'table_visually_verified':True,'redistributed_document':False},'specimen_context':context('tpu-95a'),'properties':P,'effective_printed_density_kg_m3':None,'full_mechanical_model':None,'limitations':COMMON_LIMITS+['The trade name 95A does not replace the source measured Shore A value 92 +/- 0.4.','Source elongation moduli are stresses at specified strains, not small-strain Young modulus.'],'excluded_source_rows':[{'label':'Maximum elongation for filament','source_text':'7264 +/- 76 percent','reason':'Ambiguous/suspicious source magnitude retained for review, not silently corrected or used.'}]})
    return out

def process_recipes():
    records=[]
    def add(ident,pattern,group,layer=.20,nozzle=.4,width=.45,**kw):
        records.append({'id':ident,'pattern':pattern,'group':group,'layer_height_mm':layer,'nozzle_diameter_mm':nozzle,'extrusion_width_mm':width,'patch_mm':[12.8,12.8],'mapping':'finite patch, +U across roads, +V build-up for walls; not seamless','measurement_status':'original authored visual study, not a measured toolpath','slicing_profile':False,**kw})
    for group in ['smooth','fiber','wood']:
        heights=[.08,.12,.16,.20,.28] if group=='smooth' else [.16,.20,.28]
        for h in heights:
            for pat in ['wall','aligned-seam','fuzzy-wall']:
                add(f'{group}-{pat}-L{round(h*1000):03d}',pat,group,h)
        for n,w in [(.4,.45),(.6,.66),(.8,.88)]:
            for pat in ['monotonic-top','concentric-top','ironed-top']:
                add(f'{group}-{pat}-N{round(n*100):02d}',pat,group,.20,n,w)
        for pat in ['smooth-bed','textured-bed','support-contact','sanded-wall']:
            add(group+'-'+pat,pat,group)
    add('smooth-smoothed-wall','smoothed-wall','smooth',scope='Appearance-only smooth-surface study for ASA/PVB; no solvent instructions, no postprocess mechanics prediction')
    return records

def records():
    pp=profiles();rr=process_recipes();vv=[]
    for p in pp:
        for r in rr:
            if p['texture_class']!=r['group'] or (r['pattern']=='smoothed-wall' and p['key'] not in ('asa','pvb')):continue
            ident='fff.prusament.'+p['key']+'.'+r['id']
            vv.append({'id':ident,'name':p['name']+' / '+r['pattern']+' / '+str(r['layer_height_mm'])+' mm','kind':'material_appearance','profile_id':p['id'],'process_id':r['id'],'source_measurement_context':'Referenced independently; never replaced by this visual recipe','visual_parameters':{'base_color_srgb':p['appearance_palette_srgb'],'metallic':0,'ior':1.5,'opacity':1,'ior_status':'unmeasured authoring constant','optics_scope':'Opaque surface study; translucency, scattering and spectral tint not characterized'},'engineering_assignment':False,'effective_printed_density_kg_m3':None,'native_acceptance':'not_run','premium_qualification':'not_qualified'})
    assert len(pp)==11 and len(rr)==73 and len(vv)==280,(len(pp),len(rr),len(vv))
    return pp,rr,vv

def main():
    pp,rr,vv=records();dump(ROOT/'data/physical-profiles.json',{'profiles':pp});dump(ROOT/'data/process-recipes.json',{'items':rr});dump(ROOT/'data/material-variants.json',{'items':vv});dump(ROOT/'data/sources.json',{'sources':[p['source'] for p in pp]})
    print('DATA',len(pp),'profiles',sum(len(p['properties']) for p in pp),'properties',len(rr),'mapsets',len(vv),'appearances')
if __name__=='__main__':main()
