"""Original numeric realisations of all 280 lighting concepts. Relative linear radiance,
not measured lumens, IES photometry, a solar ephemeris or proof of caustic convergence.
"""
from core import *
import re, concurrent.futures, time, traceback
from PIL import ImageDraw


def area(center,width,height,power=8,color=(1,1,1),target=(0,0,0),roll=0):
    c=np.array(center,float);n=unit(np.asarray(target)-c);up=np.array([0.,0.,1.])
    if abs(n[2])>.98:up=np.array([0.,1.,0.])
    u=unit(np.cross(up,n));v=np.cross(n,u);uu=u*np.cos(roll)+v*np.sin(roll);vv=-u*np.sin(roll)+v*np.cos(roll)
    return {'center':c.tolist(),'u':(uu*width/2).tolist(),'v':(vv*height/2).tolist(),'radiance':(np.array(color)*power).tolist()}

def sunlight(azimuth=45,elevation=35,power=12000):
    a=np.deg2rad(azimuth);e=np.deg2rad(elevation)
    return {'direction':[float(np.cos(e)*np.cos(a)),float(np.cos(e)*np.sin(a)),float(np.sin(e))],'angular_radius_rad':.00465,'radiance':[float(power)]*3}

def card(id,center,normal,width,height,reflectance=.75):
    c=np.array(center,float);n=unit(normal);up=np.array([0.,0.,1.])
    if abs(n[2])>.98:up=np.array([0.,1.,0.])
    u=unit(np.cross(up,n))*width/2;v=np.cross(n,unit(u))*height/2
    return {'id':id,'center_mm':c.tolist(),'half_u_mm':u.tolist(),'half_v_mm':v.tolist(),'reflectance_linear':[reflectance]*3}


def build_recipe(item,extent=1000.):
    n=item['name'].lower();text=(' '.join(str(item.get(k,'')) for k in ['name','sources','geometry','contribution_policy'])).lower();num=int(item['id'].split('-')[1]);f=(num-1)//10;k=(num-1)%10
    scale=extent; seed=730000+num*1543;areas=[];sun=None;ambient=[0.,0.,0.];cards=[];limitations=[];conditional=[];type_name='rectangular_area';declaration={}
    def add(p,w,h,power=8,col=(1,1,1),roll=0):areas.append(area(np.array(p)*scale,w*scale,h*scale,power,col,roll=roll))
    # Family-specific base arrangements, refined from the named concept below.
    positions=[(-1.35,-1.4,1.2),(1.4,-.7,.55),(0,1.4,1.4)]
    if f in [0,1,5,8,9,18,20,21,22,23,25]:
        add(positions[0],1.2,1.6,8)
        if any(t in text for t in ['paired','three','two','fill','dual','both','family','ceiling','window','upper','overhead','consistent']):add(positions[1],.85,1.3,3)
        if any(t in text for t in ['three','rim','roof','ceiling','top','overhead','envelop']):add(positions[2],1.5,.65,5)
    elif f in [2,6]:
        add((-1.2,-.8,.4),.18,2.2,14);add((1.2,-.1,.6),.25,2.,10)
        if 'dark' not in n:add((0,-1.7,1.5),1.2,.8,2.5)
    elif f==3:
        if 'dark field' in text:add((-1.1,.4,.2),.15,2.5,12);add((1.1,.4,.2),.15,2.5,12)
        else:add((0,1.6,.2),2.4,2.4,7);add((-1.4,-1.,.8),.25,1.8,3)
        limitations.append('Refraction/caustic quality depends on the actual optical object, topology and executor, not on this light recipe.')
    elif f==4:add((0,1.5,.5),1.6,2.,12);add((-1.3,-1.2,.8),1.1,1.3,1.5)
    elif f==7:add((0,-.2,1.8),1.7,1.2,7);add((-1.3,-1.,.45),.25,1.4,8)
    elif f==10:add((0,0,2.0),3.,1.,7);add((-1.4,-1.2,.45),.25,3.0,8);add((1.4,.1,.5),.3,2.8,5)
    elif f==11:add((-1.7,-.2,1.),1.1,2.1,7,(.86,.92,1.));ambient=[.025,.035,.055]
    elif f==12:
        for i in range(4):add((((i%2)*2-1)*.9,((i//2)*2-1)*.8,1.8),.65,.65,4,(1.,.91,.76))
    elif f==13:
        sun=sunlight(25+12*k,8+7*k,10000);ambient=[.16,.23,.38]
        if 'overcast' in n:sun=None;ambient=[.4,.43,.48]
        if 'sunset' in n:sun=sunlight(210,6,5000);sun['radiance']=[7000,4100,2200];ambient=[.08,.1,.18]
        if 'moonlit' in n:sun=sunlight(60,40,30);ambient=[.0006,.001,.002]
    elif f==14:
        add((0,0,1.5),.25,.25,20)
        limitations.append('Original luminaire-shaped area source, not measured IES/LDT intensity distribution or lux validation.')
    elif f==15:add((-1.2,-1.2,1.2),1.2,1.2,8);add((1.2,0,1.2),.6,1.2,4)
    elif f==16:
        for a in [35,145,215,325]:
            rad=np.deg2rad(a);add((np.cos(rad)*.9,-1.5,np.sin(rad)*.7),.22,.30,6)
    elif f==17:add((-1.3,.3,.6),.2,1.8,16);add((1.4,.5,.3),.25,1.6,9)
    elif f==19:add((-1.2,-1.2,1.1),.5,.5,12);add((1.4,-.5,1.),1.2,1.3,1.5);limitations.append('Specialized optical/volume intent remains dependent on matching scene media and geometry.')
    elif f==24:add((0,.7,0),.8,.04,20);add((-1.4,-1.4,1.),1.,1.,.75);limitations.append('Fixture reference position is illustrative; bind the aperture and calibrate real output before optical/photometric use.')
    elif f==26:
        sun=sunlight(40+20*k,5+8*k,14000);ambient=[0.,0.,0.]
        if 'night' in n or 'earthshine' in n:sun=None
        if 'onboard' in n:add((0,-.7,.4),.06,.04,40)
        if 'earthshine' in n:conditional.append('Earth position, angular extent, phase and radiance are unspecified; Earth source remains disabled, not invented.')
        if 'unilluminated' in n:areas=[];sun=None
    elif f==27:
        sun=sunlight(45,12+3*k,14000)
        if any(t in n for t in ['led','night']):sun=None;add((-.6,-.5,.5),.06,.04,35)
        if 'editorial' in n:add((.7,-1.1,.65),.5,.8,2);limitations.append('Editorial fill is deliberate additional energy and is never labelled unassisted lunar lighting.')
    # Specific source cardinality and size cues are preserved where unambiguous.
    if 'six large areas' in text or 'discrete upper dome' in n:
        areas=[]
        for a in range(0,360,60):rad=np.deg2rad(a);add((1.5*np.cos(rad),1.5*np.sin(rad),1.5),1.,1.,5)
    if 'four-direction' in n:
        areas=[]
        for a in (0,90,180,270):rad=np.deg2rad(a);add((1.6*np.cos(rad),1.6*np.sin(rad),.7),.8,1.0,6)
    if 'single' in n and 'sun' not in n and areas:areas=areas[:1]
    if 'clamshell' in n:areas=[area([0,-1500,700],1500,700,7),area([0,-1400,-700],1400,600,3)]
    if 'graz' in n and areas:areas[0]=area([-1400,-300,120],180,1600,12)
    if 'caustic' in n and areas:areas[0]=area([-1400,-1200,1500],30,30,80);limitations.append('Finite source authored; no claim that the current integrator resolves the requested caustic.')
    if 'two-color' in n and len(areas)>1:areas[0]['radiance']=[3,7,16];areas[1]['radiance']=[16,4,1.5]
    if 'passive' in text or 'card' in text:
        refl=.02 if 'dark' in text or 'black' in text else .75
        cards=[card('passive-fill',[900,0,0],[-1,0,0],800,1500,refl)]
    if 'shutter' in text or 'blinds' in text:
        cards+=[card('flag-'+str(i),[-700,-600+i*160,150],[1,0,0],80,1700,.005) for i in range(3)]
        limitations.append('Passive flags are geometric rectangles; this is not a photometric projector or image gobo.')
    if any(t in text for t in ['spot','projector','downlight','wall washer']):limitations.append('Native GPU realization uses a finite rectangular emitter; a directional/spot angular model is retained as intent, not silently equated to a measured fixture.')
    if any(t in text for t in ['fog','smoke','dust medium','underwater','submerged']):limitations.append('Requires an explicitly bound volume/material; the light asset does not silently add an atmosphere or a water medium.')
    if num>=261:
        ambient=[0.,0.,0.]
        limitations+=['Vacuum mode: no atmospheric sky, fog, star dome or undeclared ambient light.','Solar direction and radiance are authored relative values, not site ephemerides or measured lunar photometry.']
    result={'id':item['id'],'name':item['name'],'family':item['family'],'version':VERSION,'license':LICENSE,'original_specification':item,'units':{'length':'mm','radiance':'authored relative linear-sRGB','angle':'radian'},'subject_reference_extent_mm':extent,'subject_origin_mm':[0,0,0],'scale_policy':'Scale light positions/sizes once to an explicitly selected subject; never scale the subject.','seed':seed,'lights':{'environment':ambient,'area_lights':areas},'passive_stage':cards,'limitations':limitations,'unresolved_external_inputs':conditional,'measurement_status':'not_measured','native_gpu_complete':len(areas)<=4 and not conditional}
    if sun:result['lights']['sun']=sun
    if len(areas)>4:result['limitations']+=['Current native GPU maximum is four area lights. The full rig remains in the authoritative recipe; its environment projection is a separately identified position-bound approximation.']
    return result


def radiance_image(lights,width=1024,height=512,include_sun=True):
    u=(np.arange(width,dtype=np.float64)[None,:]+.5)/width;v=(np.arange(height,dtype=np.float64)[:,None]+.5)/height
    phi=2*np.pi*(u-.5);theta=np.pi*v
    d=np.stack([np.sin(theta)*np.cos(phi)+np.zeros_like(v),np.sin(theta)*np.sin(phi)+np.zeros_like(v),np.cos(theta)+np.zeros_like(u)],-1)
    rgb=np.broadcast_to(np.asarray(lights.get('environment',[0,0,0]),float),(height,width,3)).copy()
    for a in lights.get('area_lights',[]):
        c=np.asarray(a['center']);uu=np.asarray(a['u']);vv=np.asarray(a['v']);normal=unit(np.cross(uu,vv));den=d@normal;distance=float(c@normal)/np.where(np.abs(den)>1e-12,den,1e-12)
        hit=d*distance[:,:,None]-c;su=hit@uu/(uu@uu);sv=hit@vv/(vv@vv)
        visible=(distance>0)&(den<0)&(np.abs(su)<=1)&(np.abs(sv)<=1)
        rgb+=visible[:,:,None]*np.asarray(a['radiance'])
    if include_sun and lights.get('sun'):
        s=lights['sun'];direction=unit(s['direction']);dot=d@direction;radius=float(s['angular_radius_rad']);coverage=(dot>=np.cos(radius)).astype(float)
        if not coverage.any():
            # Preserve solid angle in a subpixel disk; no widening of the physical source.
            index=np.unravel_index(np.argmax(dot),dot.shape);omega=2*np.pi/width*np.pi/height*np.sin(theta[index[0],0]);coverage[index]=min(1.,2*np.pi*(1-np.cos(radius))/max(omega,1e-16))
        rgb+=coverage[:,:,None]*np.asarray(s['radiance'])
    return rgb.astype(np.float32)


def diagram(r,path):
    im=Image.new('RGB',(640,480),(18,23,31));draw=ImageDraw.Draw(im);cx,cy=320,255;scale=.1
    draw.ellipse((cx-35,cy-35,cx+35,cy+35),fill=(135,143,153),outline=(215,220,225),width=2)
    draw.text((20,20),r['id']+'  '+r['name'],fill=(238,241,246));draw.text((20,44),'Top view / authored layout / not a native render',fill=(148,165,184))
    for i,a in enumerate(r['lights'].get('area_lights',[])):
        x,y,z=a['center'];x=cx+x*scale;y=cy+y*scale
        draw.line((x,y,cx,cy),fill=(91,111,132),width=2);draw.rounded_rectangle((x-10,y-6,x+10,y+6),radius=3,fill=(247,207,119));draw.text((x+13,y),str(i+1),fill=(247,223,173))
    if r['lights'].get('sun'):draw.text((20,420),'Finite Sun - one energy owner',fill=(247,207,119))
    if not r['lights'].get('area_lights') and not r['lights'].get('sun'):draw.text((20,420),'No added emitters / see environmental conditions',fill=(148,165,184))
    im.save(path)


def generate_one(item):
    r=build_recipe(item);f=ROOT/'lighting'/r['id'];f.mkdir(exist_ok=True)
    dump(f/'rig.json',r);dump(f/'lighting-full.json',r['lights']);diagram(r,f/'preview.png')
    rgb=radiance_image(r['lights']);hdr(f/'reference-origin.hdr',rgb);exr(f/'reference-origin.exr',{'RGB':rgb},'Reference-origin ray projection of the authored rig. Does not retain distance/parallax; never combine with the same analytic emitters.')
    png(f/'reference-origin.png',np.rint(np.clip(srgb(rgb/(1+rgb)),0,1)*255).astype(np.uint8),'srgb')
    meshes=[{'name':'Reference subject - remove before use','mesh':sphere_mesh(180,24,12),'material':0}];mats=[simple_material('Reference gray',[.18]*3)]
    for i,a in enumerate(r['lights']['area_lights']):
        radiance=np.array(a['radiance']);peak=max(float(radiance.max()),1.);m=simple_material('Emitter '+str(i),[0,0,0]);m['emissiveFactor']=(radiance/peak).tolist();m['extensions']={'KHR_materials_emissive_strength':{'emissiveStrength':peak}}
        mats.append(m);meshes.append({'name':'Area source '+str(i),'mesh':panel_mesh(a['center'],a['u'],a['v']),'material':len(mats)-1})
    for c in r['passive_stage']:
        mats.append(simple_material(c['id'],c['reflectance_linear']));meshes.append({'name':c['id'],'mesh':panel_mesh(c['center_mm'],c['half_u_mm'],c['half_v_mm']),'material':len(mats)-1})
    export_gltf(f,'rig',meshes,mats,{'authoritative_rig':'rig.json','native_area_cap':4,'scope':'Geometry/material visualization. Emissive meshes are not a promise of real-time GI.','sun':r['lights'].get('sun'),'unresolved_external_inputs':r['unresolved_external_inputs']})
    if r['native_gpu_complete']:
        dump(f/'solidcraft-apply.json',[{'command':'render.settings.set','params':{'name':r['id']+' '+r['name'],'set':{'width':960,'height':640,'exposure_ev':-1,'job':{'method':'gpu_path','options':{'samples':128,'max_depth':8,'seed':r['seed'],'lighting':r['lights'],'tone_map':'aces_fitted'}},'stage':r['passive_stage']}}}])
    else:dump(f/'native-blockers.json',{'complete_native_application':False,'reasons':r['unresolved_external_inputs']+r['limitations'],'full_authoring_rig_retained':True,'reference_origin_hdr_is_approximation':True})
    return {'id':r['id'],'name':r['name'],'family':r['family'],'kind':'lighting','path':f.relative_to(ROOT).as_posix(),'thumbnail':f.relative_to(ROOT).as_posix()+'/preview.png','generated':True,'native_complete':r['native_gpu_complete'],'area_count':len(r['lights']['area_lights']),'limitations':r['limitations']}


def main():
    items=load(SOURCE/'lighting.json')['items'];results=[];errors=[];start=time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        jobs={pool.submit(generate_one,x):x for x in items}
        for f in concurrent.futures.as_completed(jobs):
            try:results.append(f.result())
            except Exception as e:errors.append({'id':jobs[f]['id'],'error':str(e),'trace':traceback.format_exc()})
            if (len(results)+len(errors))%20==0:dump(ROOT/'reports/lighting-progress.json',{'count':len(results),'errors':errors,'expected':280});print('LIGHTING',len(results),'errors',len(errors),flush=True)
    results.sort(key=lambda x:x['id']);dump(ROOT/'lighting/index.json',{'items':results});dump(ROOT/'reports/lighting-generation.json',{'status':'PASS' if not errors else 'FAIL','count':len(results),'expected':280,'errors':errors,'seconds':time.time()-start})
    if errors:raise RuntimeError(errors[:2])
if __name__=='__main__':main()
