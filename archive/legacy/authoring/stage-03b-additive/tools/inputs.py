"""Versioned manufacturer facts and original appearance recipes; not a plugin contract."""
from pathlib import Path
import json, copy, csv
ROOT=Path(__file__).resolve().parents[1]
def dump(p,v):
    p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf8')
SOURCES={
'bambu-abs-v3':('Bambu Lab ABS TDS V3.0','https://store.bblcdn.com/s7/default/23b4cf2b83d5470bb96d19970b5f3ae8/Bambu_ABS_Technical_Data_Sheet_V3.pdf','pp.2-3; visually checked'),
'polymaker-abs-v56':('Polymaker PolyLite ABS V5.6 2025-12-30','https://polymaker.com/wp-content/uploads/lana-downloads/TDS_Polymaker_PolyLite-ABS_V5.6_2025-12-30_EN.pdf','p.1; visually checked; conflicting fields explicitly excluded'),
'ultimaker-abs-v5':('UltiMaker ABS v5.00 2022-04-20','https://um-support-files.ultimaker.com/materials/2.85mm/tds/ABS/Ultimaker-ABS-TDS-v5.00.pdf','pp.1-3; visually checked'),
'formlabs-density':('Formlabs selected resin densities by liquid/green/cured state','https://formlabs.com/support/Density-of-selected-Formlabs-SLA-resins/','named version row, post-cured column; cure schedule not specified'),
'durable-v2':('Formlabs Durable V2 FLDUCL02, rev.01 2020-07-10','https://formlabs-media.formlabs.com/datasheets/1801084-TDS-ENUS-0P.pdf','p.2 post-cured and footnote 3; visually checked'),
'flex80-v1':('Formlabs Flexible 80A FLFL8001, 2020','https://formlabs-media.formlabs.com/datasheets/2001418-TDS-ENUS-0.pdf','p.2 post-cured; visually checked'),
'elastic-v1':('Formlabs Elastic FLELCL01 rev.01 2019-01-07','https://formlabs-media.formlabs.com/datasheets/Elastic_Resin_Technical.pdf','p.2 post-cured; text verified, screenshot service unavailable'),
'rigid-v1':('Formlabs Rigid FLRGWH01 rev.01 2018-01-23','https://formlabs-media.formlabs.com/datasheets/Rigid_Technical.pdf','p.2 post-cured; text verified, screenshot service unavailable'),
'high-temp-v2':('Formlabs High Temp FLHTAM02 rev.02 2018-12-05','https://formlabs-media.formlabs.com/datasheets/High_Temp_Technical.pdf','p.2; mechanical footnotes 5/6 differ from thermal footnotes 3/4; visually checked'),
'tough2000-v2':('Formlabs Tough 2000 V2 FLTO2002 rev.01 2025-06-10','https://formlabs-media.formlabs.com/datasheets/25011072-TDS-ENUS-0.pdf','pp.2-3 post-cured; visually checked'),
'eos-pa2200':('EOS PA 2200 Balance, 120 um, dry','https://www.eos.info/polymer-solutions/data-sheets/all-processes-and-materials?id=pa-2200','Balance section only; do not mix Performance/Speed parameters'),
'eos-pa1101':('EOS PA 1101 MDS, dry','https://www.eos.info/polymer-solutions/polymer-materials/data-sheets/mds-pa-1101','main dry table, not machine-specific alternate rows'),
'eos-pa3200gf':('EOS PA 3200 GF MDS, dry, 40 wt% glass beads','https://www.eos.info/polymer-solutions/polymer-materials/data-sheets/mds-pa-3200-gf','main dry table'),
'eos-tpu1301':('EOS TPU 1301 MDS, dry','https://www.eos.info/polymer-solutions/polymer-materials/data-sheets/mds-eos-tpu-1301','main dry table, not alternate P770 strain row'),
'hp-tpu01':('HP 3D HR TPU 01, 4AA8-5021ENW August 2025','https://h20195.www2.hp.com/v2/GetDocument.aspx?docname=4AA8-5021ENW','MJF 5200/5600 Balanced table; extracted text checked, PDF screenshot unavailable'),
'eos-316l':('EOS 316L M290 40 um FlexLine, CR365 v03/12.2016 in 07/2022 MDS','https://www.eos.info/03_system-related-assets/material-related-contents/metal-materials-and-examples/metal-material-datasheet/stainlesssteel/material_datasheet_eos_stainlesssteel_316l_en_web.pdf','PDF pp.10-12; 40 um M290 only; visually checked'),
'eos-ti64':('EOS Ti64 M290 Performance_M291 1.10, 30 um, 06/2022','https://www.eos.info/var/assets/05-datasheet-images/Assets_MDS_Metal/EOS_Titanium_Ti64/Material_DataSheet_EOS_Titanium_Ti64_EOSM290_EOSM300-4_EOSM400_EOSM400-4_en.pdf','first M290 section pp.2-4; visually checked'),
'eos-in718':('EOS IN718 M290 40 um Performance 2.0, CR696 2020-02','https://www.eos.info/var/assets/05-datasheet-images/Assets_MDS_Metal/EOS_NickelAlloy_IN718/Material_DataSheet_EOS_NickelAlloy_IN718_en.pdf?v=3','PDF pp.5-7; as-manufactured and heat-treated tables kept separate; visually checked'),
'eos-alsi10mg':('EOS AlSi10Mg M290 1kW 80 um HiPro, heat treated','https://www.eos.info/metal-solutions/data-sheets/aluminium/pds-eos-aluminium-alsi10mg-eos-m-290-1kw-80um','heat-treated table; EOS T6 condition; no absolute density in selected source'),
'eos-ms1':('EOS MS1 M290 50 um SpeedM291, heat treated','https://www.eos.info/metal-solutions/data-sheets/toolsteel/pds-eos-maragingsteel-ms1-eos-m-290-50um','heat-treated table; no absolute density in selected source'),
'markforged-174':('Markforged Metal X 17-4PH rev.2.1 2020-07-02','https://static.markforged.com/downloads/17-4-ph-stainless-steel.pdf','p.2 Markforged columns only, not MIM/wrought; visually checked')}
UNITS={'g/cm3':('kg/m3',1000,0),'g/mL':('kg/m3',1000,0),'MPa':('Pa',1e6,0),'GPa':('Pa',1e9,0),'%':('1',.01,0),'C':('K',1,273.15),'um/m/K':('1/K',1e-6,0),'J/m':('J/m',1,0),'kJ/m2':('J/m2',1000,0),'kN/m':('N/m',1000,0),'Shore A':('Shore A',1,0),'Shore D':('Shore D',1,0),'HRC':('HRC',1,0),'HV5':('HV5',1,0),'um':('m',1e-6,0)}
def prop(p,q,v,u,method,axis=None,spread=None,qualifier='typical',source=None,condition=None,temperature_k=None,**extra):
    si,scale,offset=UNITS[u]; row={'quantity':q,'value':v*scale+offset,'unit':si,'qualifier':qualifier,'original':{'value':v,'unit':u,'scale_to_si':scale,'offset_to_si':offset},'source_id':source or p['source_id'],'source_locator':SOURCES[source or p['source_id']][2],'conditions':{'state':condition or p['condition'],'orientation':axis,'test_method':method,'temperature_k':temperature_k,**extra},'reported_spread':None if spread is None else {'value':spread*scale,'unit':si,'original':spread,'meaning':'source +/-; statistical meaning not inferred'}}; p['properties'].append(row)
def profile(key,name,brand,family,source,condition,color,process,layer=None,translucent=False):
    return {'id':'am.'+key,'name':name,'brand':brand,'family':family,'source_id':source,'condition':condition,'manufacturing_process':process,'source_layer_mm':layer,'appearance_palette_srgb':color,'translucent_intent':translucent,'properties':[],'unknown_properties':['full_constitutive_model','poisson_ratio','measured_spectral_optics','postfinish_effective_part_density'],'auto_assign_body':False,'engineering_design_allowable':False}
def rows(p,q,values,u,method,axes,spreads=None):
    for i,(axis,v) in enumerate(zip(axes,values)):prop(p,q,v,u,method,axis,None if spreads is None else spreads[i])
def records():
    out=[]
    p=profile('bambu.abs.v3','Bambu Lab ABS V3','Bambu Lab','fff','bambu-abs-v3','Source specimens: 100% infill, nozzle 260 C, bed 80 C, 200 mm/s; conditioned 80 C for 12 h before testing. Not unconditioned as-printed. Source layer unspecified.',[190,191,194],'FFF');out.append(p)
    prop(p,'material_density',1.05,'g/cm3','ISO 1183',condition='material reference; not effective infilled-part density')
    for q,v,s in [('tensile_modulus',[2200,1960],[190,110]),('tensile_strength',[33,28],[3,2]),('flexural_modulus',[1880,1590],[110,100]),('flexural_strength',[62,39],[4,4])]:rows(p,q,v,'MPa','ISO 527' if q.startswith('tensile') else 'ISO 178',['X-Y','Z'],s)
    rows(p,'strain_at_break',[10.5,4.7],'%','ISO 527',['X-Y','Z'],[1,.8])
    for q,v,load in [('hdt',84,1.8e6),('hdt',87,.45e6),('vicat',94,None)]:prop(p,q,v,'C','ISO 75' if q=='hdt' else 'ISO 306',load_pa=load)
    p=profile('polymaker.abs.v56','Polymaker PolyLite ABS V5.6','Polymaker','fff','polymaker-abs-v56','2025-12-30 PDF; specimens at 260 C nozzle, 90 C bed/chamber, 100% infill; exact layer unreported.',[218,214,205],'FFF');out.append(p)
    prop(p,'material_density',1.04,'g/cm3','ISO 1183 / GB/T1033',temperature_k=296.15,condition='Versioned material density; official wiki/older versions report 1.12; no substitution')
    rows(p,'tensile_modulus',[2246.6,2080.9],'MPa','ISO 527',['X-Y','Z'],[58.2,92.7]);prop(p,'tensile_strength',29.7,'MPa','ISO 527','Z',.3)
    rows(p,'strain_at_break',[17.9,3.1],'%','ISO 527',['X-Y','Z'],[1.3,.3]);prop(p,'flexural_modulus',2127.2,'MPa','table ISO527/GB-T1040 versus diagram ISO178/GB-T9341; source conflict','X-Y',29.9);prop(p,'flexural_strength',56.2,'MPa','table ISO527/GB-T1040 versus diagram ISO178/GB-T9341; source conflict','X-Y',.3)
    for q,v,load in [('glass_transition',101,None),('vicat',104,None),('hdt',98,1.8e6),('hdt',100,.45e6)]:prop(p,q,v,'C','DSC' if q=='glass_transition' else 'ISO 306' if q=='vicat' else 'ISO 75',load_pa=load)
    p=profile('ultimaker.abs.v5','UltiMaker ABS v5.00','UltiMaker','fff','ultimaker-abs-v5','S5 Pro/Cura4.9 engineering, AA0.4, 0.15 mm layer, 100% infill; conditioned 24 h room temperature.',[168,170,175],'FFF',.15);out.append(p)
    prop(p,'material_density',1.1,'g/cm3','ISO 1183',condition='filament material reference; no infill-density prediction')
    for q,v,s in [('tensile_modulus',[1962,1931,1699],[31,68,113]),('tensile_stress_at_break',[33.9,35.7,19],[1.5,1,.6]),('flexural_modulus',[1430,1470,1317],[83,48,28])]:rows(p,q,v,'MPa','ASTM D3039' if q.startswith('tensile') else 'ISO 178',['XY flat','YZ side','Z up'],s)
    rows(p,'strain_at_break',[4.6,4.5,2],'%','ASTM D3039',['XY flat','YZ side','Z up'],[.3,.2,.1]);prop(p,'hardness',76,'Shore D','ISO 7619-1','XY flat');prop(p,'hdt',86.6,'C','ISO 75',spread=.4,load_pa=.455e6);prop(p,'vicat',93.8,'C','ISO 306',spread=.7)
    specs=[('durable.v2','Durable V2 FLDUCL02','durable-v2','Form2, 100 um, post-cured 120 min at 60 C',1.13,[220,224,215],True,[("tensile_strength",28,'MPa','ASTM D638-14'),('tensile_modulus',1,'GPa','ASTM D638-14'),('strain_at_break',55,'%','ASTM D638-14'),('flexural_strength',24,'MPa','ASTM D790-15'),('flexural_modulus',.66,'GPa','ASTM D790-15'),('izod_notched',114,'J/m','ASTM D256-10')]),
    ('flex80.v1','Flexible 80A FLFL8001','flex80-v1','Form3, 100 um, post-cured 10 min at 60 C; tensile after 3+ h at 23 C',1.12,[59,61,65],False,[('tensile_strength',8.9,'MPa','ASTM D412-06A'),('stress_at_50pct_strain',3.1,'MPa','ASTM D412-06A'),('stress_at_100pct_strain',6.3,'MPa','ASTM D412-06A'),('strain_at_break',120,'%','ASTM D412-06A'),('hardness',80,'Shore A','ASTM D2240'),('glass_transition',27,'C','DMA')]),
    ('elastic.v1','Elastic V1 FLELCL01','elastic-v1','Form2, 100 um, post-cured 20 min at 60 C; tensile 23 C after 3+ h',1,[226,222,202],True,[('tensile_strength',3.23,'MPa','ASTM D412-06A'),('stress_at_50pct_strain',.94,'MPa','ASTM D412-06A'),('stress_at_100pct_strain',1.59,'MPa','ASTM D412-06A'),('strain_at_break',160,'%','ASTM D412-06A'),('hardness',50,'Shore A','ASTM D2240'),('tear_strength',19.1,'kN/m','ASTM D624-00')]),
    ('rigid.flrgwh01','Rigid FLRGWH01 (2018 reference)','rigid-v1','Form2, 100 um, post-cured 120 min at 80 C',None,[222,225,223],False,[('tensile_strength',75,'MPa','ASTM D638-14'),('tensile_modulus',4.1,'GPa','ASTM D638-14'),('strain_at_break',5.6,'%','ASTM D638-14'),('flexural_stress_at_5pct_strain',121,'MPa','ASTM D790-15'),('flexural_modulus',3.7,'GPa','ASTM D790-15'),('izod_notched',18.8,'J/m','ASTM D256-10')]),
    ('tough2000.v2','Tough 2000 V2 FLTO2002','tough2000-v2','Form4, 100 um, post-cured 12 min at 70 C in FormCure V2',None,[48,52,58],False,[('tensile_strength',40.4,'MPa','ASTM D638-14'),('tensile_modulus',1800,'MPa','ASTM D638-14'),('tensile_yield_strength',40.4,'MPa','ASTM D638-14'),('strain_at_break',79,'%','ASTM D638-14'),('flexural_strength',67,'MPa','ASTM D790-17'),('flexural_modulus',1701,'MPa','ASTM D790-17'),('izod_notched',25,'J/m','ASTM D256-10'),('hardness',76,'Shore D','ASTM D2240')])]
    for key,name,src,cond,rho,color,trans,pr in specs:
        p=profile('formlabs.'+key,'Formlabs '+name,'Formlabs','vat',src,cond,color,'SLA',.1,trans);out.append(p)
        if rho:prop(p,'cured_density',rho,'g/cm3','not reported',source='formlabs-density',condition=name+' post-cured; density source does not specify exact cure schedule')
        for q,v,u,m in pr:prop(p,q,v,u,m)
        if key=='tough2000.v2':
            prop(p,'solid_bulk_density',1.09,'g/mL','ASTM D792-20',condition='source bulk density row; not explicitly separated green/cured');prop(p,'liquid_density',1.03,'g/mL','ASTM D792-20',condition='uncured liquid; NEVER assign to printed solid');prop(p,'hdt',57,'C','ASTM D648-16',load_pa=1.8e6);prop(p,'hdt',70,'C','ASTM D648-16',load_pa=.45e6)
        if key=='rigid.flrgwh01':p['unknown_properties'].append('absolute_density_exact_formulation_not_confirmed')
    for key,cond,ts,em,eb,fs,ct in [('uv','Form2 100 um; mechanical specimens cured 60 min at 60 C',58.3,2.75,3.3,94.5,79.6),('thermal','Form2 100 um; mechanical specimens cured 60 min at 60 C plus 90 min at 160 C',51.1,2.9,2.4,93.8,74)]:
        p=profile('formlabs.high-temp.v2.'+key,'Formlabs High Temp V2 / '+key,'Formlabs','vat','high-temp-v2',cond,[222,174,87],'SLA',.1,True);out.append(p)
        prop(p,'cured_density',1.19,'g/cm3','not reported',source='formlabs-density',condition='High Temp V2 post-cured, exact density cure schedule not specified')
        for q,v,u,m in [('tensile_strength',ts,'MPa','ASTM D638-14'),('tensile_modulus',em,'GPa','ASTM D638-14'),('strain_at_break',eb,'%','ASTM D638-14'),('flexural_strength_at_break',fs,'MPa','ASTM D790-15'),('flexural_modulus',2.62,'GPa','ASTM D790-15'),('thermal_expansion',ct,'um/m/K','ASTM E831-13')]:prop(p,q,v,u,m,**({'temperature_interval_k':[273.15,423.15]} if q=='thermal_expansion' else {}))
        for load,temp in [(1.8e6,99.2 if key=='uv' else 101),(.45e6,142 if key=='uv' else 238)]:prop(p,'hdt',temp,'C','ASTM D648-16',load_pa=load,condition='THERMAL specimens: 120 min at 80 C'+(' plus 180 min at 160 C' if key=='thermal' else '')+'; NOT the mechanical cure')
    for key,name,rho,mod,ts,elong,src,process,color,layer in [('pa2200','EOS PA2200 Balance',.93,[1650]*3,[48,48,42],[18,18,4],'eos-pa2200','SLS',[225,223,214],.12),('pa1101','EOS PA1101',1.03,[1650]*3,[50,50,48],[30,30,15],'eos-pa1101','SLS',[223,218,202],None),('pa3200gf','EOS PA3200 GF',1.22,[3200,3200,2500],[51,51,47],[9,9,5.5],'eos-pa3200gf','SLS',[204,205,198],None),('tpu1301','EOS TPU1301',1.11,[60]*3,[7,7,5],[250,250,90],'eos-tpu1301','SLS',[219,218,207],None)]:
        p=profile('eos.'+key,name,'EOS','powder-polymer',src,'Laser-sintered part, dry main source table; exact process conditions limited to source, no filled/lattice homogenization.',color,process,layer);out.append(p)
        prop(p,'sintered_part_density',rho,'g/cm3','ISO 1183-1' if key=='pa1101' else 'EOS method')
        for q,v,u in [('tensile_modulus',mod,'MPa'),('tensile_strength',ts,'MPa'),('strain_at_break',elong,'%')]:rows(p,q,v,u,'ISO 527-1/-2',['X','Y','Z'])
        if key=='pa3200gf':prop(p,'glass_bead_mass_fraction',40,'%','manufacturer declared formulation')
    p=profile('hp.tpu01.balanced','HP 3D HR TPU01 / Balanced','HP / Forward AM','powder-polymer','hp-tpu01','HP Jet Fusion 5200/5600 Balanced reference, August 2025; conditioned/postprocessed as source. No lattice prediction.',[106,107,112],'MJF');out.append(p)
    prop(p,'printed_part_density',1.11,'g/cm3','ASTM D792');prop(p,'loose_powder_bulk_density',.50,'g/cm3','DIN EN ISO 60',condition='loose feedstock powder, not the printed part')
    rows(p,'tensile_strength',[9,7],'MPa','DIN 53504 S2',['XY','Z']);rows(p,'strain_at_break',[291,137],'%','DIN 53504 S2',['XY','Z']);rows(p,'tear_resistance',[61,50],'kN/m','ASTM D624 Die C',['XY','Z'])
    p=profile('eos.316l.m29040','EOS 316L M290 40 um / as manufactured','EOS','metal-am','eos-316l','M290 316L_040_FlexM291_1.X; as manufactured, not solution annealed.',[174,179,181],'LPBF',.04);out.append(p)
    prop(p,'part_density',7.97,'g/cm3','ISO 3369',qualifier='lower_bound')
    rows(p,'yield_strength',[540,480],'MPa','ISO 6892-1',['horizontal','vertical']);rows(p,'tensile_strength',[640,570],'MPa','ISO 6892-1',['horizontal','vertical']);rows(p,'strain_at_break',[40,51],'%','ISO 6892-1',['horizontal','vertical'])
    p=profile('eos.ti64.m29030.ht','EOS Ti64 M290 30 um / heat treated','EOS','metal-am','eos-ti64','M290 Ti64_Performance_M291 1.10; tensile specimens heat-treated 2 h at 800 C in argon; room-temperature tests.',[155,158,163],'LPBF',.03);out.append(p)
    prop(p,'part_density',4.41,'g/cm3','ISO 3369',qualifier='approximate',condition='M290 part density, source does not explicitly limit to tensile heat-treatment state')
    rows(p,'yield_strength',[945,965],'MPa','ISO 6892-1 A14',['horizontal','vertical']);rows(p,'tensile_strength',[1055,1075],'MPa','ISO 6892-1 A14',['horizontal','vertical']);rows(p,'strain_at_break',[13,14],'%','ISO 6892-1 A14',['horizontal','vertical'])
    for state,ys,ts,e in [('as-built',[800,650],[1090,970],[25,32]),('heat-treated',[1240,1145],[1505,1375],[12,17])]:
        p=profile('eos.in718.m29040.'+state,'EOS IN718 M290 40 um / '+state,'EOS','metal-am','eos-in718','M290 IN718_040_PerformanceM291_2xx; '+('as manufactured' if state=='as-built' else 'heat treated according to source AMS2774/AMS5662 condition; not generic wrought IN718'),[160,162,162],'LPBF',.04);out.append(p)
        prop(p,'part_density',8.15,'g/cm3','ISO 3369',qualifier='lower_bound',condition='process reference density; exact density thermal state unspecified')
        rows(p,'yield_strength',ys,'MPa','source tensile table',['horizontal','vertical']);rows(p,'tensile_strength',ts,'MPa','source tensile table',['horizontal','vertical']);rows(p,'strain_at_break',e,'%','source tensile table',['horizontal','vertical'])
    for key,name,source,layer,ys,ts,e,mod,color,cond in [('alsi10mg','EOS AlSi10Mg M290 1kW 80 um','eos-alsi10mg',.08,[250,240],[320,310],[7,7],None,[198,202,204],'EOS T6 heat treated, AlSi10Mg_080_HiProM294; 125 C build plate'),('ms1','EOS MS1 M290 50 um','eos-ms1',.05,[2030,2000],[2100,2100],[3,2],190,[149,153,158],'MS1_050_SpeedM291; solution treated 940 C/2h and aged 490 C/6h, source condition')]:
        p=profile('eos.'+key+'.ht',name+' / heat treated','EOS','metal-am',source,cond,color,'LPBF',layer);out.append(p)
        rows(p,'yield_strength',ys,'MPa','EN ISO 6892-1 room temperature',['horizontal','vertical']);rows(p,'tensile_strength',ts,'MPa','EN ISO 6892-1 room temperature',['horizontal','vertical']);rows(p,'strain_at_break',e,'%','EN ISO 6892-1 room temperature',['horizontal','vertical'])
        if mod:rows(p,'tensile_modulus',[mod,mod],'GPa','ASTM E132-04',['horizontal','vertical'])
        p['unknown_properties'].append('absolute_part_density_not_given_in_selected_process_source')
    for state,ts,ys,mod,e,hard in [('as-sintered',1050,800,140,5,30),('H900',1250,1100,170,6,36),('H1150',950,880,170,10,32)]:
        p=profile('markforged.174.'+state.lower(),'Markforged Metal X 17-4PH / '+state,'Markforged','metal-am','markforged-174','Metal X bound-metal extrusion then debind/sinter; '+state+'; rev2.1. No absolute density inferred from relative density.',[171,174,177],'bound-metal');out.append(p)
        for q,v,u,m in [('tensile_strength',ts,'MPa','ASTM E8'),('yield_strength',ys,'MPa','ASTM E8'),('tensile_modulus',mod,'GPa','ASTM E8'),('strain_at_break',e,'%','ASTM E8'),('hardness',hard,'HRC','ASTM E18'),('relative_density',96,'%','ASTM B923')]:prop(p,q,v,u,m)
        p['unknown_properties'].append('absolute_part_density_reference_denominator_unreported')
    return out
AUDIT=[
{'source':'polymaker-abs-v56','excluded':'XY tensile strength 33.4 +/- 92.7 MPa','reason':'Implausible spread repeats modulus spread; do not replace with wiki value from a different source version.'},
{'source':'polymaker-abs-v56','retained_conflict':'Density 1.04 g/cm3 in pinned PDF versus 1.12 in official wiki/older PIS; pinned PDF value is not a universal product identity.'},
{'source':'bambu-abs-v3','excluded':'ABS melting point 200 C','reason':'Amorphous-polymer interpretation unclear; no fabricated phase transition.'},
{'source':'flex80-v1','excluded':'Compression/tear rows with inconsistent printed methods','reason':'Do not silently repair method identifiers.'},
{'source':'rigid-v1','excluded':'Absolute density from renamed Rigid4K V1 row','reason':'Exact original FLRGWH01 formulation mapping not independently established.'},
{'source':'hp-tpu01','excluded':'Stress at 50% strain with percent unit in extraction','reason':'Dimensionally ambiguous; other clearly specified properties retained. PDF screenshot service failed; text verification only.'},
{'source':'eos-pa3200gf','excluded':'Flexural strength 73 with missing unit','reason':'Do not guess the omitted source unit.'},
{'source':'eos-ti64','excluded':'Modern grade5 URL with grade23 body','reason':'Contradictory identity. Use visually checked historical Ti64 M290 document instead.'},
{'source':'markforged-174','excluded':'Conversion of relative density to kg/m3','reason':'Reference denominator and actual part porosity not established.'}]
def recipes():
    rs=[]
    def add(fam,pat,layer=None,finish=None):
        ident=fam+'-'+pat+(('-L%03d'%round(layer*1000)) if layer else '')
        rs.append({'id':ident,'family':fam,'pattern':pat,'layer_mm':layer,'patch_mm':[6.4,6.4] if fam in ('vat','metal-am') else [12.8,12.8],'finish':finish or pat,'scope':'Authored metric surface study, not machine settings or guaranteed manufactured texture','seamless':False})
    for layer in [.08,.12,.16,.20,.28]:
        for pat in ['wall','seam','fuzzy']:add('fff',pat,layer)
    for pat in ['top-roads','ironed','bed-texture','sanded','polished']:add('fff',pat,.2)
    for layer in [.025,.05,.1]:
        for pat in ['wall','angled-stairs']:add('vat',pat,layer)
    for pat in ['support-marks','sanded','polished','matte']:add('vat',pat)
    for pat in ['as-built','bead-blasted','tumbled','smoothed']:add('powder-polymer',pat)
    for layer in [.03,.04,.05,.08]:
        for pat in ['upskin','vertical','downskin']:add('metal-am',pat,layer)
    for pat in ['shot-peened','machined','polished','sintered-roads']:add('metal-am',pat)
    return rs
def variants(profiles=None,rs=None):
    ps=profiles or records();rr=rs or recipes();out=[]
    for p in ps:
        for r in rr:
            if r['family']!=p['family']:continue
            if p['family']=='metal-am':
                if p['manufacturing_process']=='LPBF' and r['pattern']=='sintered-roads':continue
                if p['manufacturing_process']=='bound-metal' and r['layer_mm'] is not None:continue
                if p['manufacturing_process']=='LPBF' and r['layer_mm'] and r['layer_mm']!=p['source_layer_mm']:continue
            out.append({'id':p['id']+'.'+r['id'],'name':p['name']+' / '+r['id'],'physical_profile_id':p['id'],'recipe_id':r['id'],'family':p['family'],'source_condition_not_replaced_by_visual_recipe':True,'qualification':'authoring_candidate','native_acceptance':'not_run'})
    return out
def main():
    ps=records();rr=recipes();vv=variants(ps,rr)
    dump(ROOT/'data/physical-profiles.json',{'profiles':ps});dump(ROOT/'data/sources.json',{'retrieved':'2026-10-25','sources':[{'id':k,'title':v[0],'url':v[1],'locator':v[2],'redistribution':'factual values and original authoring only; source publications linked, not bundled'} for k,v in SOURCES.items()]});dump(ROOT/'data/source-audit.json',AUDIT);dump(ROOT/'data/process-recipes.json',{'items':rr});dump(ROOT/'data/material-variants.json',{'items':vv})
    dump(ROOT/'registry/resource-index.json',{'purpose':'authoring inventory, not plugin standard','items':vv,'physical_profiles':[{'id':p['id'],'name':p['name']} for p in ps],'records':len(ps)+len(vv)})
    with (ROOT/'data/physical-summary.csv').open('w',newline='',encoding='utf8') as f:
        w=csv.writer(f);w.writerow(['profile','name','quantity','value_si','unit','qualifier','orientation','state','source'])
        for p in ps:
            for v in p['properties']:w.writerow([p['id'],p['name'],v['quantity'],v['value'],v['unit'],v['qualifier'],v['conditions']['orientation'],v['conditions']['state'],v['source_id']])
    print('DATA',len(ps),'profiles',sum(len(p['properties']) for p in ps),'properties',len(rr),'mapsets',len(vv),'appearances')
if __name__=='__main__':main()
