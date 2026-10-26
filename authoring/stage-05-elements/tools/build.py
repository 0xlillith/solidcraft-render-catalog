#!/usr/bin/env python3
"""Original scientific authoring pack for 118 pure elements.
All visual PBR approximations are unmeasured; scientific reference data are separate.
No plugin standard, installer, or SolidCraft application importer is declared.
"""
from __future__ import annotations
import argparse, hashlib, io, json, math, os, pathlib, struct
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

ROOT=pathlib.Path(__file__).resolve().parents[1]
SOURCE=ROOT/"data/pubchem-reference.json"
SOURCE_URL="https://pubchem.ncbi.nlm.nih.gov/rest/pug/periodictable/JSON"
PATCH_MM=[30.,30.]
BASE_PALETTES={"Au":[211,157,59],"Cu":[184,102,72],"Ag":[215,222,224],
"Fe":[142,150,155],"Co":[154,159,169],"Ni":[177,182,180],"Pt":[185,185,190],
"Al":[185,194,203],"Ti":[147,156,170],"Zn":[178,186,195],"Pb":[117,128,144],
"Sn":[183,190,198],"Hg":[181,191,203],"C":[44,46,50],"S":[224,194,54],
"P":[144,78,69],"Se":[105,51,69],"I":[73,63,88],"B":[111,85,71],
"Si":[118,130,137],"Ge":[144,150,155],"As":[117,125,131],"Sb":[143,143,149],
"Te":[113,126,136]}
FONT_CANDIDATES=["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
"/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"]
def font(size):
 for path in FONT_CANDIDATES:
  if pathlib.Path(path).exists():return ImageFont.truetype(path,size)
 return ImageFont.load_default()
def writejson(p,v):
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
def lin(s):
 v=np.asarray(s,dtype=np.float32)
 return np.where(v<=.04045,v/12.92,((v+.055)/1.055)**2.4)
def srgb(v):
 v=np.clip(np.asarray(v),0,1)
 return np.where(v<=.0031308,v*12.92,1.055*np.power(v,1/2.4)-.055)
def hexsha(p):
 d=hashlib.sha256()
 with open(p,"rb") as fh:
  for chunk in iter(lambda:fh.read(1024*1024),b""):d.update(chunk)
 return d.hexdigest()
def metallic(group):
 return ("metal" in group.lower() or group.lower() in ("lanthanide","actinide")) and "metalloid" not in group.lower() and "nonmetal" not in group.lower()
def group_style(r):
 if metallic(r["group_block"]):return ["metal-polished","metal-brushed"]
 if r["group_block"]=="Metalloid":return ["metalloid-cleaved","metalloid-matte"]
 return ["nonmetal-crystal","nonmetal-grain"]
def palette(r):
 return BASE_PALETTES.get(r["symbol"],[167,174,181] if metallic(r["group_block"]) else [138,130,112])
def blur_noise(rng,n,cell):
 s=max(2,round(n/cell))
 noise=rng.random((s,s),dtype=np.float32)
 return cv2.resize(noise,(n,n),interpolation=cv2.INTER_CUBIC)-.5
def fields(name,n):
 if n not in (128,256,512,1024,2048):raise ValueError("bounded power-of-two resolution")
 rng=np.random.default_rng(int.from_bytes(hashlib.sha256(name.encode()).digest()[:8],"little"))
 y,x=np.mgrid[0:n,0:n].astype(np.float32)
 coarse=blur_noise(rng,n,40)
 fine=blur_noise(rng,n,3)
 micro=blur_noise(rng,n,1)
 gx=x*PATCH_MM[0]/n;gy=y*PATCH_MM[1]/n
 if name=="metal-polished":
  h=.0009*(micro+.2*fine)+.0008*coarse;rough=.055+.009*fine+.012*coarse
 elif name=="metal-brushed":
  h=.0038*np.sin(gy*(2*math.pi)/.24+.18*coarse)+.0012*micro
  rough=.29+.036*fine+.026*coarse
 elif name=="metalloid-cleaved":
  h=.018*np.sin(gx*.83+gy*.36+coarse*2.6)+.016*coarse+.003*fine
  rough=.30+.045*coarse+.022*micro
 elif name=="metalloid-matte":
  h=.017*coarse+.003*fine+.001*micro;rough=.49+.045*coarse+.025*fine
 elif name=="nonmetal-crystal":
  h=.028*np.abs(np.sin(gx*.8+gy*.7+coarse*1.3))+.016*coarse
  rough=.34+.035*coarse+.02*fine
 elif name=="nonmetal-grain":
  h=.023*coarse+.009*fine+.002*micro;rough=.62+.025*coarse+.025*fine
 else:raise ValueError("unknown surface")
 h=np.asarray(h,dtype=np.float32)
 h-=float(np.mean(h))
 h=np.clip(h,-.09,.09)
 rough=np.clip(rough,.055,.92).astype(np.float32)
 alb=np.clip(1+coarse*.08+fine*.018,.80,1.13).astype(np.float32)
 return h,rough,alb
def write_maps(folder,h,rough,alb,metal):
 folder.mkdir(parents=True,exist_ok=True)
 n=h.shape[0]
 # Physical gradients in millimetres, not arbitrary pixel gradients.
 gy,gx=np.gradient(h,PATCH_MM[1]/n,PATCH_MM[0]/n)
 xyz=np.stack([-gx,+gy,np.ones_like(gx)],axis=-1)
 xyz/=np.maximum(np.linalg.norm(xyz,axis=-1,keepdims=True),1e-9)
 ogl=np.uint8(np.clip(np.rint((xyz*.5+.5)*255),0,255))
 dx=ogl.copy();dx[:,:,1]=255-dx[:,:,1]
 rc=np.uint8(np.clip(np.rint(rough*255),0,255))
 mc=np.full((n,n),255 if metal else 0,dtype=np.uint8)
 base=np.uint8(np.clip(np.rint(srgb(lin(np.clip(alb,0,1))*1.0)*255),0,255))
 rgb=np.stack([base,base,base],axis=-1)
 orm=np.stack([np.full_like(rc,255),rc,mc],axis=-1)
 heights=np.uint16(np.clip(np.rint((h+.1)/.2*65535),0,65535))
 images={"base_color":rgb,"normal_opengl":ogl,"normal_directx":dx,
 "roughness":rc,"metallic":mc,"orm":orm,"height_u16":heights}
 for name,a in images.items():
  Image.fromarray(a).save(folder/(name+".png"))
 os.environ["OPENCV_IO_ENABLE_OPENEXR"]="1"
 if not cv2.imwrite(str(folder/"height_mm.exr"),h):raise RuntimeError("OpenEXR write failed")
def export_maps(size):
 surface_names=["metal-polished","metal-brushed","metalloid-cleaved","metalloid-matte","nonmetal-crystal","nonmetal-grain"]
 idx={}
 for name in surface_names:
  h,rough,alb=fields(name,size)
  sub=ROOT/"build/maps"/("metal" if name.startswith("metal-") else "mineral")/name
  ms=sub/("master-"+str(size));write_maps(ms,h,rough,alb,name.startswith("metal-"))
  runtime_n=size//2
  if runtime_n:
   filt=lambda x:cv2.resize(x,(runtime_n,runtime_n),interpolation=cv2.INTER_AREA)
   rs=sub/("runtime-"+str(runtime_n));write_maps(rs,filt(h),filt(rough),filt(alb),name.startswith("metal-"))
  idx[name]={"master":str(ms.relative_to(ROOT)),"runtime":str(rs.relative_to(ROOT)),
    "patch_mm":PATCH_MM,"measured_surface_profile":False,"seamless":False}
  print("ELEMENT_MAPSET",name,flush=True)
 return idx
def geometry_gltf(out,appearance,mp):
 out.mkdir(parents=True,exist_ok=True)
 # Flat 30 mm patch + explicitly UV-mapped curved patch, right handed.
 W=PATCH_MM[0]/1000.; H=PATCH_MM[1]/1000.
 pos=[[0,0,0],[W,0,0],[W,H,0],[0,H,0]]
 norms=[[0,0,1]]*4; uv=[[0,1],[1,1],[1,0],[0,0]]
 tang=[[1,0,0,-1]]*4; faces=[0,1,2,0,2,3]
 columns=32;rows=8;radius=.08
 off=len(pos)
 for iy in range(rows+1):
  for ix in range(columns+1):
   a=(ix/columns-.5)*W/radius
   pos.append([W*1.4+radius*math.sin(a),iy/rows*H,radius*(1-math.cos(a))])
   norms.append([-math.sin(a),0,math.cos(a)])
   uv.append([ix/columns,1-iy/rows])
   tang.append([math.cos(a),0,math.sin(a),-1])
 for iy in range(rows):
  for ix in range(columns):
   i=off+iy*(columns+1)+ix;j=i+columns+1
   faces.extend([i,i+1,j+1,i,j+1,j])
 buf=bytearray();views=[];accessors=[]
 def append(raw,target=None):
  while len(buf)%4:buf.append(0)
  p=len(buf);buf.extend(raw)
  while len(buf)%4:buf.append(0)
  view={"buffer":0,"byteOffset":p,"byteLength":len(raw)}
  if target:view["target"]=target
  views.append(view);return len(views)-1
 def attr(vals,count,component=5126,key=None):
  arr=np.asarray(vals,dtype="<f4" if component==5126 else "<u4")
  raw=arr.reshape(-1).tobytes()
  view=append(raw,34963 if key=="indices" else 34962)
  a={"bufferView":view,"componentType":component,"count":len(vals) if key!="indices" else len(raw)//4,
    "type":{1:"SCALAR",2:"VEC2",3:"VEC3",4:"VEC4"}[count]}
  if key=="position":
   a["min"]=[float(x) for x in arr.min(axis=0)]
   a["max"]=[float(x) for x in arr.max(axis=0)]
  accessors.append(a);return len(accessors)-1
 p=attr(pos,3,key="position");no=attr(norms,3);tx=attr(uv,2);ta=attr(tang,4);f=attr(faces,1,component=5125,key="indices")
 ims=[]
 for name in ["base_color","orm","normal_directx"]:
  a=Image.open(mp/(name+".png"))
  m=io.BytesIO();a.save(m,format="PNG")
  ims.append({"bufferView":append(m.getvalue()),"mimeType":"image/png"})
 sr=np.asarray(appearance["palette_srgb"],dtype=np.float32)/255.
 color=[float(x) for x in lin(sr)]
 tree={"asset":{"version":"2.0","generator":"SolidCraft pure elements authoring 2026-10-26"},
  "scene":0,"scenes":[{"nodes":[0]}],"nodes":[{"mesh":0,"name":appearance["name"]}],
  "meshes":[{"primitives":[{"attributes":{"POSITION":p,"NORMAL":no,"TEXCOORD_0":tx,"TANGENT":ta},
   "indices":f,"material":0}]}],
  "materials":[{"name":appearance["name"],"doubleSided":True,
   "pbrMetallicRoughness":{"baseColorFactor":color+[1],
    "baseColorTexture":{"index":0},"metallicFactor":1 if appearance["metallic"] else 0,
    "roughnessFactor":1,"metallicRoughnessTexture":{"index":1}},
   "normalTexture":{"index":2},
   "extras":{"element_id":appearance["element_id"],"unmeasured_optics":True,
     "not_measured_finite_surface":True,"finite_patch_mm":PATCH_MM,
     "not_an_allotrope_assay":True,"native_acceptance":"not_run"}}],
  "images":ims,"textures":[{"source":0},{"source":1},{"source":2}],
  "accessors":accessors,"bufferViews":views,"buffers":[{"byteLength":len(buf)}]}
 ext=json.loads(json.dumps(tree));ext["buffers"][0]["uri"]="material.bin"
 writejson(out/"material.gltf",ext)
 (out/"material.bin").write_bytes(buf)
 internal=json.dumps(tree,separators=(",",":")).encode("utf8")
 internal+=b" "*((-len(internal))%4)
 binary=bytes(buf)
 header=struct.pack("<4sII",b"glTF",2,12+8+len(internal)+8+len(binary))
 (out/"material.glb").write_bytes(header+struct.pack("<II",len(internal),0x4e4f534a)+internal+struct.pack("<II",len(binary),0x004e4942)+binary)
def identity_card(r):
 name=r["name"];sym=r["symbol"];z=r["atomic_number"]
 state=r["standard_state_reported"];style=r["preview_representation"];col=palette(r)
 w,h=780,500
 im=Image.new("RGB",(w,h));px=im.load()
 for j in range(h):
  for i in range(w):
   g=.045+.055*(1-j/h)+.018*(i/w)
   px[i,j]=(int(g*255),int((g+.013)*255),int((g+.035)*255))
 d=ImageDraw.Draw(im)
 d.rounded_rectangle((28,26,750,474),radius=24,fill=(22,29,41),outline=(60,72,90),width=2)
 d.rounded_rectangle((48,47,190,188),radius=14,fill=tuple(max(23,min(225,int(v*.60))) for v in col),outline=(120,130,150),width=2)
 d.text((66,59),str(z),font=font(21),fill=(236,240,245))
 d.text((75,92),sym,font=font(60),fill=(249,250,251))
 d.text((220,61),name,font=font(40),fill=(234,239,247))
 d.text((222,119),str(r["group_block"]),font=font(22),fill=(165,184,205))
 d.line((54,224,720,224),fill=(70,81,99),width=2)
 d.text((61,246),"PubChem standard state: "+state,font=font(23),fill=(223,228,234))
 den=r["density_reference"]["reported_g_cm3"]
 d.text((61,292),"Reference density: "+(den+" g/cm3" if den else "unknown"),font=font(22),fill=(188,201,217))
 d.text((61,340),"Representation: "+style.replace("_"," "),font=font(18),fill=(175,190,206))
 d.text((61,424),"Scientific reference | Appearance unmeasured | Not native",font=font(17),fill=(123,161,190))
 out=ROOT/"build/cards"/(r["id"]+".png")
 out.parent.mkdir(parents=True,exist_ok=True);im.save(out)
 return str(out.relative_to(ROOT))
def study_preview(appearance,mp,out):
 n=360
 rough=np.asarray(Image.open(mp/"roughness.png").convert("L").resize((n,n)),dtype=np.float32)/255
 mod=np.asarray(Image.open(mp/"base_color.png").convert("L").resize((n,n)),dtype=np.float32)/255
 no=np.asarray(Image.open(mp/"normal_opengl.png").convert("RGB").resize((n,n)),dtype=np.float32)/255*2-1
 rgb=np.asarray(appearance["palette_srgb"],dtype=np.float32)/255
 l=np.array([-.45,.4,.8],dtype=np.float32);l/=np.linalg.norm(l)
 light=np.clip((no*l).sum(axis=-1),.08,1)
 base=lin(rgb)[None,None,:]*lin(mod)[:,:,None]
 shaded=base*(.24+.72*light[:,:,None]) + (1-rough[:,:,None])*.08
 tile=np.uint8(np.clip(np.rint(srgb(shaded)*255),0,255))
 im=Image.new("RGB",(540,400),(18,25,35))
 im.paste(Image.fromarray(tile),(20,20))
 draw=ImageDraw.Draw(im)
 draw.text((400,30),appearance["element_symbol"],font=font(43),fill=(225,232,241))
 draw.text((400,100),appearance["finish"],font=font(17),fill=(173,196,219))
 draw.text((400,355),"Software only",font=font(14),fill=(155,171,187))
 out.parent.mkdir(parents=True,exist_ok=True);im.save(out)
def build(size):
 source=json.loads(SOURCE.read_text(encoding="utf8"))
 rr=source["records"];assert len(rr)==118
 maps=export_maps(size)
 appearances=[]
 for index,r in enumerate(rr):
  p=identity_card(r)
  r["card_path"]=p
  if r["preview_representation"]=="illustrative_solid_pbr":
   for finish in group_style(r):
    name=r["name"]+" / "+finish.replace("-"," ")
    aid=r["id"]+"."+finish
    m=metallic(r["group_block"]);look={"id":aid,"name":name,
     "element_id":r["id"],"element_symbol":r["symbol"],"finish":finish,
     "metallic":m,"palette_srgb":palette(r),"mapset":finish,"native_acceptance":"not_run",
     "material_class":"illustrative_surface_not_measured","physical_link_qualified":True}
    appearance_dir=ROOT/"build/materials"/aid
    tex=ROOT/maps[finish]["runtime"]
    geometry_gltf(appearance_dir,look,tex)
    study_preview(look,tex,appearance_dir/"preview.png")
    writejson(appearance_dir/"appearance.json",look)
    appearances.append(look)
  if (index+1)%20==0:print("ELEMENTS",index+1,len(rr),flush=True)
 writejson(ROOT/"data/element-profiles.json",{"profiles":rr,"source":SOURCE_URL})
 writejson(ROOT/"data/element-appearances.json",{"items":appearances})
 writejson(ROOT/"registry/resource-index.json",{"purpose":"internal research authoring inventory only",
    "plugin_standard":None,"element_count":118,"appearance_count":len(appearances),
    "records":[{"id":r["id"],"kind":"pure_element_reference","card":r["card_path"]} for r in rr]+
      [{"id":a["id"],"kind":"illustrative_element_appearance","physical_profile_id":a["element_id"]} for a in appearances],
    "mapsets":maps,"native_acceptance":"not_run","premium_qualification":"not_qualified"})
 cards=[]
 for r in rr:
  looks=[a for a in appearances if a["element_id"]==r["id"]]
  links=" ".join(f'<a href="build/materials/{a["id"]}/material.glb">{a["finish"]} GLB</a>' for a in looks)
  cards.append(f'<article data-name="{r["name"].lower()} {r["symbol"].lower()} {r["group_block"].lower()}" data-mode="{r["preview_representation"]}"><img loading="lazy" src="{r["card_path"]}"><h3>{r["atomic_number"]}. {r["name"]} ({r["symbol"]})</h3><p>{r["standard_state_reported"]} — {r["preview_representation"].replace("_"," ")}</p>{links}</article>')
 html='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Pure Elements — SolidCraft Authoring</title><style>body{font:14px system-ui;background:#10151e;color:#ebf1f7;margin:0}header{position:sticky;top:0;background:#10151e;padding:16px 26px;z-index:2;border-bottom:1px solid #35445b}input,select{padding:9px;background:#253247;color:white;border:1px solid #53627a;border-radius:6px}main{display:grid;grid-template-columns:repeat(auto-fill,minmax(265px,1fr));gap:15px;padding:22px}article{background:#1c2736;border:1px solid #354357;border-radius:9px;padding:12px}img{width:100%;border-radius:6px}h3{margin:7px 0}p{color:#a9bad0}a{color:#92c3ee;margin-right:10px}</style><header><h1>All 118 pure elements</h1><p>Source-linked scientific references and illustrative looks. No fictitious synthetic-element bulk materials, certified optics, or plugin format.</p><input id="q" placeholder="Element or symbol" oninput="f()"><select id="mode" onchange="f()"><option value="">All representations</option><option value="illustrative_solid_pbr">Solid PBR candidates</option><option value="liquid_reference_only">Liquid reference</option><option value="gas_reference_only">Gas reference</option><option value="identity_reference_only">Identity only</option></select></header><main>'''+''.join(cards)+'''</main><script>function f(){let q=document.getElementById("q").value.toLowerCase(),m=document.getElementById("mode").value;document.querySelectorAll("article").forEach(e=>e.hidden=!(e.dataset.name.includes(q)&&(!m||e.dataset.mode===m)))}</script></html>'''
 (ROOT/"index.html").write_text(html,encoding="utf8")
 report={"status":"GENERATED","source_elements":len(rr),"solid_look_variants":len(appearances),
  "mapsets":len(maps),"expected_png":len(maps)*7*2,"expected_exr":len(maps)*2,
  "expected_glb_gltf":len(appearances)*2,"element_cards":len(rr),
  "native_acceptance":"not_run","premium_qualification":"not_qualified","plugin_standard":None}
 writejson(ROOT/"reports/build-summary.json",report)
 print("ELEMENTS_GENERATED",report,flush=True)
if __name__=="__main__":
 pa=argparse.ArgumentParser();pa.add_argument("--size",type=int,default=2048);build(pa.parse_args().size)
