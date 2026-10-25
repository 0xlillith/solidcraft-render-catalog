"""Original numerical transcription of primary alloy references; not an installer or design allowables."""
from __future__ import annotations
import csv, hashlib, json, math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RETRIEVED='2026-10-25'
UNITS={'g/cm^3':('kg/m^3',1000.),'Mg/m^3':('kg/m^3',1000.),'kg/m^3':('kg/m^3',1.),'GPa':('Pa',1e9),'MPa':('Pa',1e6),'ksi':('Pa',6894757.293168),'lb/in^3':('kg/m^3',.45359237/.0254**3),'J/(kg K)':('J/(kg K)',1.),'J/(g K)':('J/(kg K)',1000.),'W/(m K)':('W/(m K)',1.),'Btu_IT/(h ft degF)':('W/(m K)',1055.05585262/(3600*.3048)*1.8),'Btu_IT/(lb degF)':('J/(kg K)',1055.05585262/.45359237*1.8),'microstrain/K':('1/K',1e-6),'microstrain/degF':('1/K',1.8e-6),'microohm cm':('ohm m',1e-8),'microohm m':('ohm m',1e-6),'microohm in':('ohm m',2.54e-8),'1':('1',1.),'HRC':('HRC',1.)}
SOURCES=[];PROFILES=[];REVIEWS=[]
def dump(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def source(id,url,title,locator):
    SOURCES.append(dict(id=id,url=url,title=title,locator=locator,retrieved=RETRIEVED,kind='primary_manufacturer_or_industry_reference',redistributed_document=False,source_license=None))
    return id

def profile(id,name,family,sid,condition,palette):
    p=dict(id=id,name=name,family=family,source_id=sid,material_state='solid',condition=condition,properties=[],composition=[],composition_scope='Selected major constituents only; source specification remains authoritative.',appearance_palette_linear=palette,appearance_value_basis='Original illustrative RGB conductor reflectance; not measured optical constants',unknown_is_zero=False,auto_assign=False,structural_design_allowable=False)
    PROFILES.append(p);return p

def prop(p,key,value,unit,temp=None,interval=None,locator='Physical Properties',qualifier='supplier_typical',note=None):
    si,factor=UNITS[unit]
    def convert(x):
        if not isinstance(x,(int,float)) or isinstance(x,bool) or not math.isfinite(x):raise ValueError('finite numerical source value required')
        return x*factor
    converted=[convert(x) for x in value] if isinstance(value,list) else convert(value)
    p['properties'].append(dict(quantity=key,value=converted,unit=si,original={'value':value,'unit':unit,'scale_to_si':factor},source_id=p['source_id'],source_locator=locator,temperature_k=None if temp is None else temp+273.15,temperature_interval_k=None if interval is None else [x+273.15 for x in interval],qualifier=qualifier,uncertainty=None,note=note))

def chem(p,symbol,low=None,high=None,nominal=None,balance=False):
    p['composition'].append(dict(element_or_group=symbol,min_mass_percent=low,max_mass_percent=high,nominal_mass_percent=nominal,balance=balance,source_id=p['source_id'],source_locator='Chemical Analysis / Composition',uncertainty=None))

def note(p,text):REVIEWS.append({'profile':p['id'],'disposition':text})

def sand(id,name,slug,family='stainless',rho=None,e=None,cp=None,k=None,cte=None,condition=None):
    sid=source('sand-'+id,'https://www.sandmeyersteel.com/'+slug+'/',name+' — Sandmeyer Steel','Main physical-property table; FAQ is not used')
    p=profile(id,name,family,sid,condition or 'Supplier plate reference; heat treatment and test direction not stated for all physical values',[.57,.59,.61] if family=='stainless' else [.56,.55,.52])
    if rho is not None:prop(p,'density',rho,'g/cm^3')
    if e is not None:prop(p,'young_modulus',e,'GPa')
    if cp is not None:prop(p,'specific_heat',cp,'J/(kg K)',interval=[0,100])
    if k is not None:prop(p,'thermal_conductivity',k,'W/(m K)',temp=100)
    if cte is not None:prop(p,'mean_linear_expansion',cte,'microstrain/K',interval=[20,100])
    return p

p=sand('ss-304l','304L plate reference','alloy-304-304l',rho=7.90,e=200,cp=500,k=16.3,cte=16.6)
for row in [('Cr',18,20),('Ni',8,12),('C',None,.030),('Mn',None,2),('Si',None,.75),('N',None,.1)]:chem(p,*row)
chem(p,'Fe',balance=True);note(p,'Use main table E=200 GPa, not FAQ E=193 GPa. This does not certify a heat or product.')
p=sand('ss-316l','316L plate reference','alloy-316-316l',rho=7.90,e=200,cp=450,k=14.6,cte=16.6)
for row in [('Cr',16,18),('Ni',10,14),('Mo',2,3),('C',None,.030)]:chem(p,*row)
chem(p,'Fe',balance=True);note(p,'Metric table values transcribed explicitly; imperial thermal-conductivity rounding/heading differs. No claim of a measured specimen.')
p=sand('ss-321','321 plate reference','alloy-321-321h',rho=7.920,e=193,cte=16.0)
for row in [('Cr',17,19),('Ni',9,12),('C',None,.08)]:chem(p,*row)
chem(p,'Fe',balance=True);note(p,'Specific heat, resistivity and thermal conductivity omitted because online units/temperatures are inconsistent. Titanium stabilization constraints remain in the source, not replaced with a nominal fraction.')
p=sand('ss-17-4ph-a','17-4PH — Condition A','alloy-17-4ph',rho=7.75,e=196,k=18.3,condition='Physical table Condition A; not an aged H900/H1150 strength model')
prop(p,'specific_heat',460,'J/(kg K)',temp=20);prop(p,'mean_linear_expansion',11.3,'microstrain/K',interval=[21,427])
for row in [('Cr',15,17.5),('Ni',3,5),('Cu',3,5),('Nb+Ta',.15,.45)]:chem(p,*row)
chem(p,'Fe',balance=True)
p=sand('ss-904l','904L plate reference','alloy-904l',rho=7.95,e=190,cp=450,k=12.9,cte=15.3)
for row in [('Cr',19,23),('Ni',23,28),('Mo',4,5),('Cu',1,2)]:chem(p,*row)
chem(p,'Fe',balance=True);note(p,'Electrical resistivity omitted: inconsistent unit columns; no guessed correction.')
p=sand('duplex-2205','Duplex 2205 plate reference','alloy-2205',family='duplex')
prop(p,'density',.278,'lb/in^3',temp=20);prop(p,'young_modulus',27600,'ksi',temp=20);prop(p,'thermal_conductivity',8.7,'Btu_IT/(h ft degF)',temp=20);prop(p,'mean_linear_expansion',7.5,'microstrain/degF',interval=[20,100]);prop(p,'electrical_resistivity',33.5,'microohm in',temp=20)
note(p,'2205 is retained as supplier designation, not an assertion that UNS S31803 and S32205 specifications are identical. Physical data converted from explicit imperial units. Specific-heat typo excluded.')
p=sand('superduplex-2507','Superduplex 2507 plate reference','alloy-2507',family='duplex')
for key,v,u in [('density',7800,'kg/m^3'),('young_modulus',200,'GPa'),('shear_modulus',75,'GPa'),('specific_heat',450,'J/(kg K)'),('thermal_conductivity',17,'W/(m K)'),('electrical_resistivity',80,'microohm cm')]:prop(p,key,v,u,temp=20)
prop(p,'mean_linear_expansion',13,'microstrain/K',interval=[20,100])
for el,v in [('Cr',25),('Ni',7),('Mo',4),('N',.27)]:chem(p,el,nominal=v)
chem(p,'Fe',balance=True);note(p,'Chemistry is supplier typical, not grade limits. Mechanical tables containing an unrelated 2304 designation are excluded.')
p=sand('ni-400','Nickel-copper alloy 400','monel-alloy-400-400ar',family='nickel',rho=8.8)
for key,v,u in [('young_modulus',182,'GPa'),('specific_heat',427,'J/(kg K)'),('thermal_conductivity',22,'W/(m K)')]:prop(p,key,v,u,temp=20)
chem(p,'Ni+Co',63,70);chem(p,'Cu',28,34);note(p,'Alloy 400 physical reference only: no 400AR strength substitution. Resistivity not used because HTML unit transcription conflicts with manufacturer bulletin.')
p=sand('ni-600','Nickel-chromium alloy 600','inconel-alloy-600',family='nickel',rho=8.42,e=214,cp=444)
note(p,'Thermal conductivity and resistivity not used because the HTML temperature/unit labels conflict. Strength remains unknown.')
p=sand('ni-625','Nickel alloy 625','inconel-alloy-625',family='nickel',rho=8.44,e=207.5,cp=427)
for row in [('Ni',58,None),('Cr',20,23),('Mo',8,10),('Nb+Ta',3.15,4.15)]:chem(p,*row)
note(p,'Resistivity temperature and thermal-conductivity FAQ/table discrepancy not resolved; both properties deliberately omitted.')
p=sand('ni-825','Nickel-iron-chromium alloy 825','incoloy-alloy-825',family='nickel',rho=8.14)
prop(p,'specific_heat',440,'J/(kg K)');prop(p,'thermal_conductivity',11.3,'W/(m K)',temp=26)
note(p,'Elastic modulus omitted: online table says 196 MPa alongside 28.3 million psi. Composition table contains conflicting duplicated rows; no fabricated limits imported.')
p=sand('ni-c276','Nickel alloy C-276','hastelloy-c-276-alloy',family='nickel',rho=8.89,e=205)
prop(p,'specific_heat',427,'J/(kg K)',temp=20);prop(p,'thermal_conductivity',9.8,'W/(m K)',temp=100)
for row in [('Mo',15,17),('Cr',14.5,16.5),('Fe',4,7),('W',3,4.5)]:chem(p,*row)
chem(p,'Ni',balance=True);note(p,'Main physical-table modulus retained; FAQ differs. Resistivity unit is inconsistent and excluded.')
p=sand('invar-36','Invar 36 reference','ssc-invar-36',family='iron-nickel',rho=8.11,cte=1.5)
prop(p,'specific_heat',515,'J/(kg K)');chem(p,'Ni',nominal=36);chem(p,'Fe',balance=True)
note(p,'No elastic modulus supplied by reviewed physical table; unknown, not substituted from a generic steel.')

# Manufacturer PDF tables viewed independently as page images. Do not bundle copyrighted PDFs.
kaiser='https://online.kaiseraluminum.com/depot/PublicProductInformation/Document/'
rows=[('al-6061-t651','6061-T651','1015/Kaiser_Aluminum_6061_Sheet_Coil_and_Plate.pdf',2.70,68.3,896,167,23.6,310,276,'sheet/coil/plate; T6/T651 typical row'),('al-7075-t651','7075-T651','1028/Kaiser_Aluminum_7075_Rod_and_Bar.pdf',2.80,71.0,960,130,23.4,572,503,'rod/bar; T6/T651 typical row'),('al-7075-t7351','7075-T7351','1028/Kaiser_Aluminum_7075_Rod_and_Bar.pdf',2.80,71.0,960,155,23.4,503,434,'rod/bar; T73/T7351 typical row'),('al-2024-t351','2024-T351','1012/Kaiser_Aluminum_2024_Sheet_Coil_and_Plate.pdf',2.77,73.1,875,120,22.9,469,324,'sheet/coil/plate; T4/T351 typical row')]
for id,name,url,rho,e,cp,k,a,uts,ys,cond in rows:
    sid=source('kaiser-'+id,kaiser+url,'Kaiser Aluminum '+name,'PDF page 1 mechanical / page 2 physical and composition tables; metric columns')
    p=profile(id,name,'aluminum',sid,cond,[.88,.90,.92]);prop(p,'density',rho,'Mg/m^3',temp=20,locator='p2 Nominal Density');prop(p,'young_modulus',e,'GPa',locator='p1 Typical mechanical properties, named temper');prop(p,'specific_heat',cp,'J/(kg K)',temp=100,locator='p2 Specific Heat');prop(p,'thermal_conductivity',k,'W/(m K)',temp=20,locator='p2 Thermal conductivity, named temper');prop(p,'mean_linear_expansion',a,'microstrain/K',interval=[20,100],locator='p2 Mean linear expansion');prop(p,'tensile_strength',uts,'MPa',locator='p1 Typical tensile, 0.500-inch diameter specimen');prop(p,'yield_strength',ys,'MPa',locator='p1 Typical yield, 0.500-inch diameter specimen')
    for row in ([('Si',.4,.8),('Cu',.15,.4),('Mg',.8,1.2),('Cr',.04,.35)] if '6061' in id else [('Cu',1.2,2),('Mg',2.1,2.9),('Cr',.18,.28),('Zn',5.1,6.1)] if '7075' in id else [('Cu',3.8,4.9),('Mn',.3,.9),('Mg',1.2,1.8)]):chem(p,*row)
    chem(p,'Al',balance=True)
    note(p,'Use printed metric typical data verbatim, including source-specific density/modulus. These are not guaranteed minima, allowable stresses, or all-form/size values. Temperature for mechanical table not stated; left null.')

curows=[('c26000','C26000 cartridge brass','brass',.308,16000,6000,70,11.1,[20,300],[.72,.53,.24]),('c93200','C93200 bearing bronze','bronze',.322,14500,None,33.6,10,[20,100],[.61,.38,.18]),('c95400','C95400 aluminum bronze','bronze',.269,15500,None,33.9,9,[20,300],[.68,.49,.22]),('c70600','C70600 copper-nickel','copper-nickel',.323,18000,6800,26,9.5,[20,300],[.67,.57,.48]),('c71500','C71500 copper-nickel','copper-nickel',.323,22000,8300,17,9,[20,300],[.62,.58,.53])]
for id,name,family,rho,e,g,k,a,interval,palette in curows:
    sid=source('cda-'+id,'https://alloys.copper.org/alloy/'+id.upper(),'Copper Development Association '+id.upper(),'Physical Properties and Chemical Composition tables; individual table units')
    p=profile(id,name,family,sid,'CDA alloy physical reference; product form and temper must be selected separately',palette)
    prop(p,'density',rho,'lb/in^3',temp=20);prop(p,'young_modulus',e,'ksi')
    if g is not None:prop(p,'shear_modulus',g,'ksi')
    prop(p,'thermal_conductivity',k,'Btu_IT/(h ft degF)',temp=20);prop(p,'specific_heat',.1 if id=='c95400' else .09,'Btu_IT/(lb degF)',temp=20);prop(p,'mean_linear_expansion',a,'microstrain/degF',interval=interval)
    if id=='c26000':chem(p,'Cu',68.5,71.5);chem(p,'Zn',balance=True)
    if id=='c93200':
        for row in [('Cu',81,85),('Pb',6,8),('Sn',6.3,7.5),('Zn',1,4)]:chem(p,*row)
    if id=='c95400':
        for row in [('Cu',83,None),('Fe',3,5),('Al',10,11.5)]:chem(p,*row)
    if id in ('c70600','c71500'):
        chem(p,'Ni+Co',9 if id=='c70600' else 29,11 if id=='c70600' else 33);chem(p,'Fe',1 if id=='c70600' else .4,1.8 if id=='c70600' else 1);chem(p,'Cu+Ag',balance=True)
    note(p,'Explicit original imperial units retained. Density is converted from lb/in^3, not substituted from rounded specific gravity. No fabrication/medical/safety recommendation is inferred.')

sid=source('timet-6-4','https://www.timet.com/documents/datasheets/alpha-and-beta-alloys/timetal-6-4.pdf','TIMETAL 6-4 data sheet TMC-0150','PDF p1 Tables 1 and 2; visually verified')
p=profile('ti-6al4v','Ti-6Al-4V / TIMETAL 6-4','titanium',sid,'Grade 5 reference; modulus range depends on texture and heat treatment; thermal conductivity explicitly mill annealed',[.53,.52,.50])
prop(p,'density',4.42,'g/cm^3',temp=22);prop(p,'young_modulus',[107,122],'GPa',temp=20,qualifier='source_range',note='Range retained; no midpoint or isotropic tensor inferred.');prop(p,'shear_modulus',[41,45],'GPa',temp=20,qualifier='source_range');prop(p,'poisson_ratio',.31,'1',temp=20);prop(p,'thermal_conductivity',6.6,'W/(m K)',temp=20);prop(p,'specific_heat',.580,'J/(g K)',temp=20);prop(p,'mean_linear_expansion',9,'microstrain/K',interval=[0,100])
chem(p,'Al',5.5,6.75);chem(p,'V',3.5,4.5);chem(p,'Ti',balance=True);note(p,'Use density 4.42 from this named data sheet at 22 C, not 4.43 from a different TIMET publication. Ranged moduli are deliberately not combined with Poisson ratio into an invented isotropic elastic card.')
sid=source('uddeholm-sverker21','https://www.uddeholm.com/app/uploads/sites/216/productdb/api/tech_uddeholm-sverker-21_en.pdf','Uddeholm Sverker 21, edition 13 04.2019','PDF p3 Physical Data: hardened and tempered to 62 HRC; table visually verified')
p=profile('d2-sverker21-62hrc','D2 / Sverker 21 — hardened and tempered 62 HRC','tool-steel',sid,'Hardened and tempered to 62 HRC, not the soft-annealed delivery condition',[.55,.56,.57])
for key,v,u in [('density',7700,'kg/m^3'),('young_modulus',210000,'MPa'),('thermal_conductivity',20,'W/(m K)'),('specific_heat',460,'J/(kg K)')]:prop(p,key,v,u,temp=20)
prop(p,'rockwell_c_hardness',62,'HRC',locator='Physical Data condition');prop(p,'compressive_proof_strength',2200,'MPa',locator='p3 Compressive strength at 62 HRC',qualifier='source_approximate',note='Rc0.2 compressive proof strength; not tensile yield strength.')
for el,v in [('C',1.55),('Si',.3),('Mn',.4),('Cr',11.3),('Mo',.8),('V',.8)]:chem(p,el,nominal=v)
chem(p,'Fe',balance=True);note(p,'Typical analysis is not full grade composition limits; physical table condition is 62 HRC, not delivery hardness.')

FINISHES=[{'id':'mirror-polished','name':'Mirror polished','roughness':.055,'height_amplitude_mm':.00035,'pattern':'polished'}, {'id':'fine-brushed','name':'Fine directional brush','roughness':.24,'height_amplitude_mm':.002,'pattern':'brushed'}, {'id':'cross-satin','name':'Cross-satin brushed','roughness':.32,'height_amplitude_mm':.003,'pattern':'cross'}, {'id':'precision-ground','name':'Precision ground','roughness':.19,'height_amplitude_mm':.0015,'pattern':'ground'}, {'id':'lathe-turned','name':'Lathe-turned face','roughness':.26,'height_amplitude_mm':.005,'pattern':'turned'}, {'id':'face-milled','name':'Face-milled overlapping passes','roughness':.30,'height_amplitude_mm':.008,'pattern':'milled'}, {'id':'bead-blasted','name':'Fine bead blast','roughness':.57,'height_amplitude_mm':.009,'pattern':'blasted'}, {'id':'service-scuffed','name':'Scuffed bare metal','roughness':.37,'height_amplitude_mm':.004,'pattern':'scuffed'}]

def build():
    assert len(PROFILES)==24
    variants=[]
    for i,p in enumerate(PROFILES):
        p['property_count']=len(p['properties']);p['missing_properties']=[q for q in ['density','young_modulus','poisson_ratio','tensile_strength','yield_strength','specific_heat','thermal_conductivity','mean_linear_expansion','electrical_resistivity'] if q not in {v['quantity'] for v in p['properties']}]
        for f in FINISHES:
            variants.append({'id':'alloy.'+p['id']+'.'+f['id'],'name':p['name']+' / '+f['name'],'kind':'material_appearance','physical_profile_id':p['id'],'finish_id':f['id'],'palette_linear':p['appearance_palette_linear'],'map_contract':'finite40mm-v1','engineering_properties_changed_by_finish':False,'native_validation':'not_run','premium_qualification':'pending','limitations':['Original RGB finish approximation, not measured spectral reflectance.','Machining marks are shading detail, not dimensionally certified manufacturing geometry.','Bare metal only; no plating, anodizing, corrosion, residual stress or strength change is inferred.','Physical reference applies only to its recorded grade, form, condition and temperature.']})
    dump(ROOT/'data/physical-profiles.json',{'license_scope':'Original selection and metadata MIT OR Apache-2.0; factual source claims retain provenance; no full datasheet redistributed.','profiles':PROFILES})
    dump(ROOT/'data/finishes.json',{'finishes':FINISHES,'mapping':'finite 40x40 mm, clamp-to-edge; no seamless claim','native_optical_model':'opaque metallic PBR approximation'})
    dump(ROOT/'data/variants.json',{'items':variants,'plugin_standard':None})
    dump(ROOT/'data/sources.json',{'retrieved':RETRIEVED,'items':SOURCES})
    dump(ROOT/'reports/source-review.json',{'reviewed_sources':len(SOURCES),'notes':REVIEWS,'excluded_candidate_sources':[{'url':'https://online.kaiseraluminum.com/depot/PublicProductInformation/Document/1040/Kaiser_Aluminum_5052_Tube_and_Pipe.pdf','reason':'Density number lacks an unambiguous unit and no metric value; deferred rather than guessing.'},{'url':'https://alloys.copper.org/alloy/C36000','reason':'Maintenance page during source review; no unsourced data added.'}], 'not_a_certified_material_database':True})
    with (ROOT/'data/property-index.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['profile','quantity','value_si','unit_si','temperature_k','interval_k','condition','source','locator'])
        for p in PROFILES:
            for v in p['properties']:w.writerow([p['id'],v['quantity'],json.dumps(v['value']),v['unit'],v['temperature_k'],v['temperature_interval_k'],p['condition'],v['source_id'],v['source_locator']])
    dump(ROOT/'registry.json',{'status':'authoring_index_not_plugin_standard','base_v1_resources':1386,'stage01_wood_resources':400,'stage02_profiles':len(PROFILES),'stage02_variants':len(variants),'global_indexed_records':1386+400+len(PROFILES)+len(variants),'alloys_distinct_grades':23,'later_work':['carbon/alloy steels beyond D2','more tool steels','magnesium and zinc alloys','solders','additional aluminum/copper/titanium grades','native rendering and physical-card acceptance','complete legacy material reference reconciliation'],'items':[{'id':v['id'],'physical_profile':v['physical_profile_id'],'appearance':f"build/materials/{v['id']}/material.gltf"} for v in variants]})
    print('PREPARED',len(PROFILES),'grade-condition profiles',len(variants),'appearances',sum(len(p['properties']) for p in PROFILES),'sourced physical records')
if __name__=='__main__':build()
