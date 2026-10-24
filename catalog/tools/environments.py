"""Original procedural environment realizations, explicit finite context geometry,
independent illumination probes and camera-only backplates. No photography/AI imagery,
site DEM, architectural survey, calibrated atmosphere or mission model is claimed.
"""
from core import *
from lighting import area, sunlight, radiance_image
from PIL import ImageDraw, ImageFont
import concurrent.futures, time, traceback

class Scene:
    def __init__(self):self.meshes=[];self.materials=[];self.material_keys={};self.objects=[]
    def material(self,name,hexcolor,rough=.65,metal=0):
        key=(name,hexcolor,rough,metal)
        if key not in self.material_keys:self.material_keys[key]=len(self.materials);self.materials.append(simple_material(name,rgbhex(hexcolor),rough,metal))
        return self.material_keys[key]
    def add(self,name,mesh,color='999999',rough=.65,metal=0):
        idx=self.material(name.split('/')[0],color,rough,metal);self.meshes.append({'name':name,'mesh':mesh,'material':idx})
    def box(self,name,c,s,color='999999',rough=.65,metal=0):
        self.add(name,box_mesh(c,s),color,rough,metal);self.objects.append({'type':'box','name':name,'center_mm':list(map(float,c)),'size_mm':list(map(float,s)),'color':color})
    def sphere(self,name,c,s,color='999999',rough=.75,metal=0,segments=12,rings=8):
        self.add(name,transformed_mesh(sphere_mesh(1,segments,rings),s,c),color,rough,metal);self.objects.append({'type':'ellipsoid','name':name,'center_mm':list(map(float,c)),'radii_mm':list(map(float,s)),'color':color})
    def beam(self,name,a,b,radius,color='888888',sides=8):
        a=np.array(a,float);b=np.array(b,float);axis=unit(b-a);ref=np.array([0,0,1.])
        if abs(axis[2])>.95:ref=np.array([0,1.,0])
        u=unit(np.cross(axis,ref));v=np.cross(axis,u);angles=np.linspace(0,2*np.pi,sides,endpoint=False);ring=np.cos(angles)[:,None]*u+np.sin(angles)[:,None]*v
        vertices=np.concatenate([a+ring*radius,b+ring*radius,[a],[b]]);faces=[]
        for i in range(sides):j=(i+1)%sides;faces +=[[i,j,sides+j],[i,sides+j,sides+i],[2*sides,j,i],[2*sides+1,sides+i,sides+j]]
        self.add(name,mesh_triangles(vertices,faces),color)
    def terrain(self,name,width,depth,amp,color,seed,style='rolling',z=0):
        n=48;ax=np.linspace(-width/2,width/2,n);ay=np.linspace(-depth/2,depth/2,n);x,y=np.meshgrid(ax,ay);rng=np.random.default_rng(seed)
        height=np.zeros_like(x)
        for _ in range(7):
            a,b=rng.uniform(.5,4,2);phase=rng.uniform(0,2*np.pi);height+=np.sin(x/width*a*2*np.pi+phase)*np.cos(y/depth*b*2*np.pi-phase)*amp/(1+a+b)
        if style=='dunes':height=amp*(.4+.6*np.sin(x/width*8*np.pi+.5*np.sin(y/depth*4*np.pi)))
        if style=='slope':height+=amp*(x/width)*3
        if style in ('crater','depression'):
            r=np.sqrt((x/(width*.32))**2+(y/(depth*.32))**2);height+=amp*(1.5*np.exp(-((r-1)/.14)**2)-2.1*np.exp(-(r/.8)**4))
        if style=='ridge':height+=amp*2*np.exp(-(x/(width*.1))**2)
        # Explicit clear centre support patch, blended rather than deleting triangles.
        fall=np.clip(np.sqrt((x/(width*.13))**2+(y/(depth*.13))**2)-.5,0,1);height=height*fall+z
        vertices=np.stack([x,y,height],-1).reshape(-1,3);faces=[]
        for j in range(n-1):
            for i in range(n-1):a=j*n+i;faces.extend([[a,a+1,a+n+1],[a,a+n+1,a+n]])
        self.add(name,mesh_triangles(vertices,faces),color,1.0)
        self.objects.append({'type':'terrain','name':name,'width_mm':width,'depth_mm':depth,'amplitude_mm':amp,'seed':seed,'style':style,'z_mm':z,'grid':n})
    def tree(self,name,x,y,h,kind,rng):
        self.beam(name+'/trunk',[x,y,0],[x,y,h*.7],h*.035,'69533b')
        if kind=='conifer':
            for j in range(3):
                z=h*(.4+j*.17);rad=h*(.32-j*.07);self.sphere(name+'/crown'+str(j),[x,y,z],[rad,rad,h*.29],'3e5c45',segments=10,rings=6)
        elif kind=='bamboo':
            for i in range(3):self.beam(name+'/stem'+str(i),[x+i*70,y,0],[x+i*70,y,h],h*.009,'6c7b47');self.sphere(name+'/leaves',[x,y,h*.8],[h*.22,h*.12,h*.22],'708a49',segments=8,rings=6)
        else:
            for i in range(3):
                dx,dy=rng.uniform(-.12,.12,2)*h;self.sphere(name+'/crown'+str(i),[x+dx,y+dy,h*(.68+.05*i)],[h*.28,h*.27,h*.28],'677647' if kind=='olive' else '55764c',segments=10,rings=6)
    def desk(self,name,x,y,w=1800,d=800,h=750,color='b59665'):
        self.box(name+'/top',[x,y,h],[w,d,45],color,.48)
        for dx in [-w*.43,w*.43]:
            for dy in [-d*.36,d*.36]:self.box(name+'/leg',[x+dx,y+dy,h/2],[55,55,h],'555b60',.4,.6)
    def rack(self,name,x,y,w=1600,d=650,h=2500,boxes=True):
        for dx in [-w/2,w/2]:
            for dy in [-d/2,d/2]:self.box(name+'/upright',[x+dx,y+dy,h/2],[65,65,h],'626c76',.45,.65)
        for j in range(4):
            z=200+j*(h-300)/3;self.box(name+'/shelf',[x,y,z],[w,d,55],'a0a5a7',.5,.5)
            if boxes and j<3:
                for i in [-.3,.2]:self.box(name+'/crate',[x+i*w,y,z+240],[w*.35,d*.75,400],'a08764',.85)


def build_scene(item):
    num=int(item['id'].split('-')[1]);family=(num-1)//10;variant=(num-1)%10;n=item['name'].lower();text=n+' '+item.get('geometry','').lower();rng=np.random.default_rng(840000+num*3271);s=Scene();extent=6000.;support=0.;special=[]
    dark='dark' in n or 'black' in n;floor='34383f' if dark else 'a7a7a1';wall='4b4e55' if dark else 'd5d7d7'
    is_space=family>=24
    if family==0:
        extent=6000
        if 'transparent' not in n:s.box('Studio floor',[0,0,-30],[6000,6500,60],floor)
        if 'corner' in n:
            s.box('Left wall',[-3000,1400,1700],[80,3800,3400],wall);s.box('Back wall',[0,3300,1700],[6000,80,3400],wall)
        elif 'hangar' in n:
            for i in range(5):s.beam('Hangar beam',[-3000,-2000+i*1200,3300],[3000,-2000+i*1200,3300],80,'888f99')
        elif 'infinite' in n or 'envelop' in n or 'studio' in n:
            radius=1200
            for j in range(16):
                a=j*np.pi/32;b=(j+1)*np.pi/32;center=[0,2000+radius*np.sin((a+b)/2),radius*(1-np.cos((a+b)/2))];u=[3000,0,0];v=[0,radius*(b-a)/2*np.cos((a+b)/2),radius*(b-a)/2*np.sin((a+b)/2)];s.add('Cyclorama strip '+str(j),panel_mesh(center,u,v),wall)
            s.box('Back wall',[0,3200,2600],[6000,60,2800],wall)
    elif family==1:
        extent=4500;s.box('Presentation floor',[0,0,-30],[5000,5000,60],floor)
        if any(k in n for k in ['ring','circular']):
            for j in range(3):s.sphere('Elliptical podium '+str(j),[(j-1)*950,200,180+j*120],[750,650,160+j*100],'b9b9b4',segments=32,rings=8)
            special.append('Round staging is a faceted ellipsoid realization, not an exact cylindrical manufacturing solid.')
        elif 'arches' in n:
            for j in range(3):
                x=(j-1)*1600
                for k in range(12):
                    a=k*np.pi/12;b=(k+1)*np.pi/12;s.beam('Display arch',[x+650*np.cos(a),1300,1400+650*np.sin(a)],[x+650*np.cos(b),1300,1400+650*np.sin(b)],160,'c6b9a1')
                s.box('Arch pillar',[x-650,1300,700],[300,300,1400],'c6b9a1');s.box('Arch pillar',[x+650,1300,700],[300,300,1400],'c6b9a1')
        else:
            for i in range(3+variant%3):s.box('Podium '+str(i),[(i-1)*850,500+(i%2)*500,150+i*130],[700,700,300+i*260],'b4afa7')
        support=300
    elif family==2:
        extent=2600;support=760;colors=['b69968','dfded4','595c60','b3c6ca','a4a9af','777b82','36685b','c7ccc9','999890','dbddd9'];s.desk('Work surface',0,0,2000,1200,760,colors[variant]);s.box('Backdrop',[0,1400,1400],[2800,50,2000],wall)
        if 'mat' in n:
            s.box('Task mat',[0,0,790],[1200,700,8],colors[variant])
            if 'cutting' in n:
                for i in range(-5,6):s.box('Mat ruling',[i*100,0,795],[1,700,1],'b2c6b5');s.box('Mat ruling',[0,i*50,795],[1200,1,1],'b2c6b5')
        if 'tray' in n:
            for x in (-600,600):s.box('Tray edge',[x,0,800],[25,700,80],'969795')
        if 'plate' in n:s.sphere('Presentation plate',[0,0,790],[550,550,30],'d8dcd7',segments=48,rings=8)
    elif family in [3,4,5,6,7,8,9,20,21,22,23]:
        extent=9000 if family not in [21,22] else 6000
        s.box('Room floor',[0,0,-40],[extent,extent,80],floor);s.box('Back wall',[0,extent/2,1600],[extent,100,3200],wall);s.box('Left wall',[-extent/2,0,1600],[100,extent,3200],wall)
        # A real opening is left in the right wall. No window decal substitutes for it.
        s.box('Right wall lower',[extent/2,1000,500],[100,extent-2000,1000],wall);s.box('Right wall lintel',[extent/2,1000,2900],[100,extent-2000,600],wall)
        if family in [4,5,6]:
            s.desk('Desk',-1800,1000,1800,800,750,'bba282');s.desk('Table',1800,1700,1500,900,750,'b7b7b1')
            for x in (-1800,1800):
                s.box('Seat',[x,200,450],[550,550,80],'66757d');s.box('Chair back',[x,460,850],[550,80,720],'66757d')
            if any(k in text for k in ['shel','book','retail','boutique','library','kitchen','cabinet']):s.rack('Wall shelving',0,extent/2-450,2400,650,2500,True)
            if any(k in n for k in ['sofa','living','bedroom','hotel']):s.box('Upholstered seat',[-1500,2400,400],[2400,900,600],'928f86');s.box('Upholstered back',[-1500,2750,850],[2400,200,700],'928f86')
            if 'stair' in n:
                for i in range(10):s.box('Step '+str(i),[2500,1200+i*220,100+i*150],[1000,240,180+i*300],'aaaca8')
        if family==3:
            for i in range(4):s.box('Exhibit plinth '+str(i),[-2600+i*1700,1800,500],[900,900,1000],['c4c1b7','949b9e','bba88a','dadbd6'][i])
        if family in [7,8,21,22]:
            for i in (-1,1):s.desk('Technical bench '+str(i),i*1700,1700,2000,900,780,'78938b' if family in (8,21) else '8b939a')
            for i in range(3):s.box('Instrument '+str(i),[-2200+i*700,2000,1030],[500,450,450],'c7cdd0');s.box('Instrument display '+str(i),[-2200+i*700,1765,1080],[330,12,180],'25353d')
            s.rack('Parts storage',3000,2500,1600,600,2400,True)
            if any(k in n for k in ['print','cnc','reflow','enclosure']):
                s.box('Machine base',[1500,-1500,700],[1800,1300,1400],'6b737c')
                for x in (650,2350):s.box('Machine column',[x,-1500,2000],[120,1300,1200],'565f68')
                s.box('Machine top',[1500,-1500,2600],[1800,1300,120],'8b959e');s.box('Machine bed',[1500,-1500,1500],[1500,1050,100],'c1c4c2')
            if family==22:
                s.desk('Optical breadboard',0,-1200,2200,1000,850,'252a30')
                for j in range(5):s.beam('Optical post',[(-2+j)*350,-1200,880],[(-2+j)*350,-1200,1150],25,'999fa6');s.box('Optical holder',[(-2+j)*350,-1200,1200],[200,80,230],'3e4854')
        if family==9:
            for x in (-3000,-1300,1300,3000):s.rack('Warehouse rack',x,1800,1300,900,3000,True)
        if family in [20,23]:
            for x in (-3000,3000):
                for y in (-2200,0,2200):s.box('Bay frame',[x,y,1700],[160,160,3400],'858d98')
            for y in (-2200,0,2200):s.beam('Overhead rail',[-3000,y,3300],[3000,y,3300],90,'929ba3')
            s.box('Equipment platform',[0,1500,150],[2800,2200,300],'7f8994')
            if 'chamber' in n:
                for j in range(16):
                    a=j*2*np.pi/16;b=(j+1)*2*np.pi/16;s.beam('Chamber rim',[1500*np.cos(a),2400,1600+1500*np.sin(a)],[1500*np.cos(b),2400,1600+1500*np.sin(b)],120,'a6adb3')
    elif family in [10,11,12]:
        extent=16000;s.box('Paving',[0,0,-60],[extent,extent,120],'999892')
        if family==12 or 'road' in n or 'avenue' in n or 'lane' in n:
            s.box('Roadway',[0,0,5],[5000,extent,25],'484c4f')
            for y in range(-7000,7500,1300):s.box('Lane marking',[0,y,20],[100,650,3],'d5d1bb')
            for x in (-3000,3000):s.box('Kerb',[x,0,100],[250,extent,200],'b2b3ad')
        for i,x in enumerate((-6000,6000)):
            for j in range(3):
                h=2800+(variant+j)%4*1100;y=-4500+j*4500;s.box('Context building',[x,y,h/2],[2500,3300,h],'c2bdae' if family==10 else '9eabb1')
                for k in range(2):s.box('Window',[x-np.sign(x)*1260,y-700+k*1300,h*.65],[20,700,1000],'536c7c',.2)
        if any(k in n for k in ['bridge','viaduct','footbridge']):
            for x in (-2600,2600):
                s.beam('Bridge rail',[x,-7000,1200],[x,7000,1200],70,'677882')
                for y in range(-6500,7000,1300):s.beam('Bridge diagonal',[x,y,1200],[x,y+1200,2600],50,'677882')
        if 'courtyard' in n:s.box('Rear courtyard wall',[0,7000,2000],[14000,200,4000],'cfc5ae')
    elif family in [13,14,15,16,17,18,19]:
        extent=24000;style='dunes' if 'dune' in n else 'slope' if any(k in n for k in ['slope','mountain']) else 'rolling';amp=600 if family in (16,17) else 130
        color='c3b28d' if family==17 or 'sand' in n else '8d8a80' if family==16 else '777c64'
        if 'snow' in n or 'polar' in n or 'frozen' in n:color='d3d9dc'
        if family==18:color='8c9086';amp=25
        if family==19:color='4e5258';amp=10
        s.terrain('Terrain',extent,extent,amp,color,840000+num,style)
        if family in [13,14] or any(k in n for k in ['garden','woodland','forest','tree','park','vineyard','grove']):
            kind='conifer' if any(k in n for k in ['pine','conifer','snow']) else 'olive' if 'olive' in n else 'bamboo' if 'bamboo' in n else 'broadleaf'
            for j in range(16):
                a=j*2*np.pi/16;radius=6000+rng.uniform(-1200,2800);x,y=radius*np.cos(a),radius*np.sin(a);s.tree('Tree '+str(j),x,y,2500+rng.uniform(0,3500),kind,rng)
        if family in [15,16,17] or any(k in n for k in ['rock','gravel','quarry']):
            for j in range(24):
                xy=rng.uniform(-11000,11000,2)
                if np.linalg.norm(xy)<2300:xy[0]+=4500
                rr=rng.uniform(180,950);s.sphere('Rock '+str(j),[*xy,rr*.35],[rr,rr*.7,rr*.5],color,segments=8,rings=5)
        if family==15 or any(k in n for k in ['water','lake','pool','river','coast','beach','harbor']):
            s.box('Water surface',[0,6500,-5],[24000,10000,10],'3e7789',.12)
            special.append('Water context is a static authored surface. No hydrodynamics or wave transport is claimed.')
            if 'pier' in n or 'marina' in n:
                for j in range(25):s.box('Pier plank',[0,3000+j*220,60],[1800,200,100],'9b825d')
        if family==19:
            for j in range(6):x=(-1 if j%2 else 1)*4000;y=-6000+j*2200;s.beam('Streetlight post',[x,y,0],[x,y,4000],55,'606a73');s.box('Streetlight housing',[x,y,4100],[500,300,100],'e3d6a3')
        if family==18:special.append('Sky/weather radiance is an artistic analytic field, not a calibrated atmosphere. Optional rain/snow/fog intent is retained separately.')
    elif family==24:
        extent=12000
        if any(k in n for k in ['truss','array','radiator','corridor','clearance','maintenance']):
            for j in range(7):
                x=-4500+j*1500
                for y in (-1200,1200):s.beam('Space frame',[x,y,-1800],[x+1500,y,-1800],70,'a3a9b2');s.beam('Frame diagonal',[x,y,-1800],[x+1500,-y,-1800],50,'a3a9b2')
            if 'array' in n:
                for j in range(8):s.box('Array cell panel',[-4200+j*1200,2000,-800],[1100,2200,40],'263f69',.2,.2)
        # Free flight remains genuinely groundless, not an invented dark floor.
        special+=['Vacuum: zero atmospheric sky. Earth and star fields disabled without explicit external inputs.','Relative context is authored, not a mission/ephemeris model.']
    else:
        extent=16000 if family<27 else 4500
        style='crater' if any(k in n for k in ['crater','pocket','depression']) else 'ridge' if 'ridge' in n else 'slope' if 'slope' in n else 'rolling'
        color='888783' if 'highland' in n or family==26 else '626165'
        s.terrain('Lunar terrain',extent,extent,500 if family<27 else 80,color,840000+num,style)
        for j in range(22 if family<27 else 12):
            xy=rng.uniform(-extent*.46,extent*.46,2)
            if np.linalg.norm(xy)<extent*.16:xy[0]+=extent*.27
            rr=rng.uniform(extent*.012,extent*.055);s.sphere('Angular lunar rock '+str(j),[*xy,rr*.3],[rr,rr*.7,rr*.65],color,segments=7,rings=5)
        if any(k in n for k in ['tray','container','core-tube','handoff','transfer','inspection']):
            s.box('Generic sample staging tray',[extent*.25,0,130],[700,500,80],'a9afb4',.4,.8)
            for j in range(3):s.sphere('Sample proxy '+str(j),[extent*.2+j*180,0,220],[60,60,70],'8f8c82',segments=7,rings=5)
        if 'dust snapshot' in n:
            for j in range(30):
                t=(j+.5)/30;s.sphere('Authored ballistic particle '+str(j),[-800+1600*t,300*np.sin(t*4),1600*t*(1-t)],[8,8,8],'898680',segments=6,rings=4)
            special.append('Static authored ballistic curve only; no dynamics or dust simulation.')
        special+=['Conceptual terrain, not measured lunar topography.','Vacuum: no atmospheric haze, rain, wind or added sky illumination.']
    # Groundless source still has an exportable coordinate witness outside the subject zone.
    if not s.meshes:
        s.box('Optional coordinate witness - hide for free flight',[0,5000,-5000],[1,1,1],'000000')
        special.append('One 1 mm coordinate witness is included solely to keep portable mesh files nonempty; hide or delete it in free-flight scenes.')
    return s,extent,support,special


def environment_radiance(item,width=2048,height=1024):
    num=int(item['id'].split('-')[1]);family=(num-1)//10;vnum=(num-1)%10;n=item['name'].lower();phi=2*np.pi*((np.arange(width)[None,:]+.5)/width-.5);theta=np.pi*(np.arange(height)[:,None]+.5)/height;z=np.cos(theta)+np.zeros_like(phi)
    vacuum=family>=24;lights={'environment':[0,0,0],'area_lights':[]};sun=None
    if vacuum:
        rgb=np.zeros((height,width,3),np.float32)
        off=any(k in n for k in ['eclipse','deep-space','full-shadow','shadowed','shadow sampling','shadow interval','shadow alcove'])
        if not off:sun=sunlight(30+vnum*19,4+vnum*6,14000)
        if 'led' in n:
            lights['area_lights']=[area([-500,-350,500],80,40,30)];sun=None
    else:
        night=family==19 or 'night' in n;outdoor=10<=family<=19
        if outdoor:
            t=np.clip(z,0,1)[:,:,None];zen=np.array([.12,.24,.48]);hor=np.array([.55,.64,.72]);ground=np.array([.055,.05,.043]);rgb=np.where((z>=0)[:,:,None],hor[None,None,:]*(1-t)+zen[None,None,:]*t,ground)
            if 'overcast' in n or 'rain' in n or 'snowfall' in n:rgb=np.where((z>=0)[:,:,None],np.array([.38,.42,.48])*(.6+.4*t),ground);sun=None
            else:sun=sunlight(25+vnum*23,15+vnum*6,10000)
            if any(k in n for k in ['sunset','dawn','dusk']):rgb[:]=np.where((z>=0)[:,:,None],np.array([.55,.28,.13])*(1-t)+np.array([.08,.12,.29])*t,ground);sun=sunlight(210,6,5000)
            cloud=.5+.5*np.sin(phi*7+.35*np.cos(theta*9))*np.sin(phi*3-theta*4);cloud=(np.clip((cloud-.55)*2.5,0,1)*(z>0))[:,:,None]
            if family==18 or 'cloud' in n:rgb=rgb*(1-cloud*.55)+cloud*.5
            if night:rgb*=.004;sun=None;lights['area_lights']=[area([-2000,-1000,2000],400,400,8,[1,.78,.48]),area([2500,1500,3000],500,300,6,[.6,.75,1])]
        else:
            rgb=np.full((height,width,3),.025 if 'black' in n or 'dark' in n else .12,np.float32)
            w=1700+100*vnum;lights['area_lights']=[area([-2200,-1700,1700],w,2000,5,[1,.95,.85]),area([2400,700,1800],1000,1600,2,[.83,.91,1])]
            if family in (7,8,9,20,21,23):lights['area_lights'].append(area([0,0,2800],3000,800,3))
            # Distant room structure in the lighting probe, not a replacement for exported geometry.
            bands=(np.cos(phi*8+vnum*.3)>.91)&(z>-.5)&(z<.8);rgb=np.where(bands[:,:,None],rgb*.45,rgb)
    # Analytic Sun is kept out of the reusable sky probe to avoid a duplicated energy owner.
    rgb=np.asarray(rgb,dtype=np.float32)+radiance_image(lights,width,height,include_sun=False)
    return np.maximum(rgb,0),sun,lights


def camera_preview(scene,extent,support,path,width=1200,height=750,background=None):
    """Original shaded mesh-authoring preview, labelled; no native transport claim."""
    bg=background or (24,29,37);im=Image.new('RGB',(width,height),bg);draw=ImageDraw.Draw(im)
    yaw=np.deg2rad(-55);pitch=np.deg2rad(32);back=np.array([np.cos(pitch)*np.sin(yaw),-np.cos(pitch)*np.cos(yaw),np.sin(pitch)]);right=unit(np.cross([0,0,1],back));up=np.cross(back,right);target=np.array([0,800 if extent>5000 else 0,support+extent*.05]);scale=min(width,height)*.78/extent;polygons=[]
    for it in scene.meshes:
        m=it['mesh'];p=m['positions'];tri=p[m['indices'].reshape(-1,3)];delta=tri-target;screenx=width*.5+(delta@right)*scale;screeny=height*.62-(delta@up)*scale;depth=delta@back
        normals=unit(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]));shade=.32+.68*np.maximum(normals@unit([-1,-.8,2]),0);col=np.array(scene.materials[it['material']]['pbrMetallicRoughness']['baseColorFactor'][:3]);colors=np.clip(srgb(col[None,:]*shade[:,None]),0,1)*255
        for i in range(len(tri)):
            xs=screenx[i];ys=screeny[i]
            if xs.max()<0 or xs.min()>width or ys.max()<0 or ys.min()>height:continue
            polygons.append((float(depth[i].mean()),[(float(xs[j]),float(ys[j])) for j in range(3)],tuple(colors[i].astype(int))))
    polygons.sort(key=lambda x:x[0])
    for _,points,col in polygons:draw.polygon(points,fill=col)
    im.save(path);return im


def generate_one(item):
    rid=item['id'];f=ROOT/'environments'/rid;f.mkdir(exist_ok=True);scene,extent,support,special=build_scene(item)
    export_gltf(f,'environment',scene.meshes,scene.materials,{'catalog_id':rid,'source_geometry_units':'mm Z-up','scope':'Original finite procedural context, not a facility/site reconstruction','limitations':special})
    save_obj(f,'environment',scene.meshes,scene.materials)
    rgb,sun,lights=environment_radiance(item);hdr(f/'illumination.hdr',rgb);exr(f/'illumination.exr',{'RGB':rgb},'Authored linear sRGB illumination excluding separately owned analytic Sun. Relative unmeasured radiance.')
    png(f/'panorama.png',np.rint(np.clip(srgb(rgb/(1+rgb)),0,1)*255).astype(np.uint8),'srgb')
    background=(0,0,0) if int(rid.split('-')[1])>=241 else (34,42,53)
    im=camera_preview(scene,extent,support,f/'backplate.png',background=background);im.resize((480,300),Image.Resampling.LANCZOS).save(f/'preview.png')
    lighting={'environment':[0.,0.,0.],'area_lights':[]}
    if sun:lighting['sun']=sun
    # The HDR already contains room/task patches. Do not also add those area emitters.
    recipe={'id':rid,'name':item['name'],'family':item['family'],'version':VERSION,'license':LICENSE,'original_specification':item,'generated_geometry':scene.objects,'geometry_summary':{'mesh_nodes':len(scene.meshes),'triangles':sum(len(m['mesh']['indices'])//3 for m in scene.meshes),'units':'millimetres Z-up in OBJ; metres Y-up in glTF/GLB','extent_mm':extent,'suggested_subject_support_mm':support},'radiance':{'file':'illumination.hdr','exr':'illumination.exr','orientation':'phi = 2*pi*(u-.5), theta=pi*v, Z up','native_rotation_offset_rad':float(np.pi),'sun_disk_in_hdr':False,'analytic_sun':sun,'source_owner':'HDR owns distant room/task patches; the separate Sun owns solar energy','units':'authored relative linear-sRGB','measurement_status':'not_measured'},'background':{'file':'backplate.png','kind':'camera_only_shaded_geometry_authoring_view','lighting_source':False,'limitations':'Not a photograph or native renderer output; finite scene geometry is provided separately.'},'limitations':special+['Procedural family realization with named contextual components; no claim that every physical detail of the concept has been modeled or validated.','Native glTF import retains geometry and scalar appearances, not arbitrary material extensions or textures.'],'full_original_requirements_validated':False}
    dump(f/'environment.json',recipe)
    name=rid+' '+item['name'];commands=[{'command':'file.insert_mesh','params':{'path':str(f/'environment.glb'),'up':'y','name':rid+' Context'}},{'command':'document.metadata.set','params':{'values':{'project':name,'license':LICENSE,'org.solidcraft.local_catalog':{'id':rid,'scope':'Finite procedural environment authoring scene','source_recipe':'environment.json','not_measured':True}}}},{'command':'render.settings.capture_hdr','params':{'name':name,'set':{'width':960,'height':640,'background':list(background),'camera':{'target':[0,0,support+extent*.08],'yaw':-.8,'pitch':.5,'roll':0,'distance':extent*1.15,'fov':.65,'up':'z'},'job':{'method':'gpu_path','options':{'samples':128,'max_depth':8,'seed':840000+int(rid.split('-')[1]),'lighting':lighting,'tone_map':'aces_fitted'}}},'path':str(f/'illumination.hdr'),'expected_sha256':sha(f/'illumination.hdr'),'rotation_rad':float(np.pi),'intensity':1,'assume_linear_srgb':False}}]
    dump(f/'solidcraft-build.json',commands)
    return {'id':rid,'name':item['name'],'family':item['family'],'kind':'environment','path':f.relative_to(ROOT).as_posix(),'thumbnail':f.relative_to(ROOT).as_posix()+'/preview.png','generated':True,'mesh_nodes':len(scene.meshes),'limitations':special,'native_status':'build_recipe_pending_execution'}


def main():
    items=load(SOURCE/'environments.json')['items'];results=[];errors=[];start=time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        jobs={pool.submit(generate_one,x):x for x in items}
        for f in concurrent.futures.as_completed(jobs):
            try:results.append(f.result())
            except Exception as e:errors.append({'id':jobs[f]['id'],'error':str(e),'trace':traceback.format_exc()})
            if (len(results)+len(errors))%10==0:dump(ROOT/'reports/environment-progress.json',{'count':len(results),'errors':errors,'expected':280});print('ENVIRONMENTS',len(results),'errors',len(errors),flush=True)
    results.sort(key=lambda x:x['id']);dump(ROOT/'environments/index.json',{'items':results});dump(ROOT/'reports/environment-generation.json',{'status':'PASS' if not errors else 'FAIL','count':len(results),'expected':280,'errors':errors,'seconds':time.time()-start})
    if errors:raise RuntimeError(errors[:2])
if __name__=='__main__':main()
