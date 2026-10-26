#!/usr/bin/env python3
"""Reproducible CC0 scanned PBR benchmark; separate from the original procedural pack.
Only vendor-provided source maps, actual dimensions and source hashes are used.
No plugin contract, engineering density/strength, measured IOR or native validation.
"""
from __future__ import annotations
import argparse, hashlib, io, json, math, os, pathlib, struct, urllib.parse, urllib.request, gc
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

ROOT=pathlib.Path(__file__).resolve().parents[1]
MANIFEST=ROOT/"manifest.json"
AGENT="SolidCraft-Render-Catalog-Quality-Benchmark/1.0 (CC0; Powered by Poly Haven)"
def put(path,obj):
 path=pathlib.Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
def hashlib_file(path,kind="sha256"):
 h=hashlib.new(kind)
 with open(path,"rb") as f:
  for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
 return h.hexdigest()
def fetch_json(url):
 u=urllib.parse.urlparse(url)
 if u.scheme!="https" or u.hostname!="api.polyhaven.com":raise ValueError("Unexpected API URL")
 req=urllib.request.Request(url,headers={"User-Agent":AGENT,"Accept":"application/json"})
 with urllib.request.urlopen(req,timeout=45) as r:
  return json.load(r)
def get_file(role,variants,resolution,formats):
 if role not in variants: return None
 sz=variants[role].get(resolution,{})
 for fmt in formats:
  if fmt in sz and "url" in sz[fmt]:return sz[fmt]|{"format":fmt,"role":role}
 return None
def download(record,folder,name):
 u=urllib.parse.urlparse(record["url"])
 if u.scheme!="https" or u.hostname!="dl.polyhaven.org":raise ValueError("Unapproved original file host")
 path=folder/(name+"."+record["format"])
 path.parent.mkdir(parents=True,exist_ok=True)
 req=urllib.request.Request(record["url"],headers={"User-Agent":AGENT})
 with urllib.request.urlopen(req,timeout=120) as response, open(path,"wb") as dest:
  while b:=response.read(1024*1024):dest.write(b)
 if path.stat().st_size!=record["size"]:raise ValueError(f"Size mismatch for {path}")
 if hashlib_file(path,"md5")!=record["md5"]:raise ValueError(f"Source MD5 mismatch for {path}")
 return path,{"file":str(path.relative_to(ROOT)),"source_url":record["url"],
   "source_md5":record["md5"],"bytes":record["size"],"sha256":hashlib_file(path),
   "role":record["role"]}
def process(row):
 slug=row["slug"];source=ROOT/"build/source-4k"/slug;runtime=ROOT/"build/maps"/slug/"runtime-2048"
 files=fetch_json(f"https://api.polyhaven.com/files/{slug}")
 info=fetch_json(f"https://api.polyhaven.com/info/{slug}")
 if info["files_hash"]!=row["files_hash"]:raise ValueError("Poly Haven file revision changed: "+slug)
 if info["type"]!=1:raise ValueError("Not a PBR texture")
 if any(abs(float(info["dimensions"][i])-float(row["dimensions_mm"][i]))>.1 for i in (0,1)):
  raise ValueError("Physical scale changed for "+slug)
 roles={
  "diffuse":get_file("Diffuse",files,"4k",["jpg","png"]),
  "normal":get_file("nor_gl",files,"4k",["png","exr"]),
  "roughness":get_file("Rough",files,"4k",["png","exr"]),
  "displacement":get_file("Displacement",files,"4k",["png","exr"]),
  "ao":get_file("AO",files,"4k",["png","exr"])
 }
 if roles["roughness"] is None:roles["roughness"]=get_file("arm",files,"4k",["png","jpg"])
 if not roles["diffuse"] or not roles["normal"] or not roles["roughness"]:
  raise ValueError("PBR color, GL normal, or roughness is missing: "+slug)
 receipts={};path={}
 for key,record in roles.items():
  if record:
   path[key],receipts[key]=download(record,source,key)
 print("SOURCE_VERIFIED",slug,sorted(receipts),flush=True)
 def read_img(p):
  with Image.open(p) as im:
   im.load()
   if im.size!=(4096,4096):raise ValueError("Expected measured 4K map: "+str(p))
   return np.asarray(im)
 diffuse=read_img(path["diffuse"])
 if diffuse.ndim==2:diffuse=np.repeat(diffuse[:,:,None],3,axis=2)
 if diffuse.shape[2]>3:diffuse=diffuse[:,:,:3]
 if diffuse.dtype==np.uint16:diffuse=(diffuse/257).astype(np.uint8)
 if diffuse.dtype!=np.uint8:raise ValueError("Unsupported diffuse bit depth")
 # Linear-domain antialiasing when downsampling sRGB base color.
 f=diffuse.astype(np.float32)/255
 linear=np.where(f<=.04045,f/12.92,((f+.055)/1.055)**2.4)
 small=cv2.resize(linear,(2048,2048),interpolation=cv2.INTER_AREA)
 small=np.clip(small,0,1)
 col=np.where(small<=.0031308,small*12.92,1.055*np.power(small,1/2.4)-.055)
 base=np.uint8(np.rint(np.clip(col,0,1)*255))
 del diffuse,f,linear,small,col;gc.collect()
 normal=read_img(path["normal"])
 if normal.dtype==np.uint16:normal=normal.astype(np.float32)/65535
 elif normal.dtype==np.uint8:normal=normal.astype(np.float32)/255
 else:normal=normal.astype(np.float32)
 if normal.ndim!=3 or normal.shape[2]<3:raise ValueError("GL normal requires 3 channels")
 normal=normal[:,:,:3]*2-1
 normal=cv2.resize(normal,(2048,2048),interpolation=cv2.INTER_AREA)
 normal/=np.maximum(np.linalg.norm(normal,axis=2,keepdims=True),1e-7)
 normgl=np.uint8(np.rint(np.clip((normal*.5+.5)*255,0,255)))
 normdx=normgl.copy();normdx[:,:,1]=255-normdx[:,:,1]
 del normal;gc.collect()
 rough_source=read_img(path["roughness"])
 if rough_source.ndim==3:
  # A Poly Haven arm (AO, Roughness, Metallic) map uses GREEN for roughness.
  if roles["roughness"]["role"]=="arm":rough_source=rough_source[:,:,1]
  else:rough_source=rough_source[:,:,0]
 if rough_source.dtype==np.uint16:rough_source=rough_source.astype(np.float32)/257
 elif rough_source.dtype!=np.uint8:
  rough_source=np.asarray(rough_source,dtype=np.float32)*255
 rough=np.uint8(np.rint(np.clip(cv2.resize(rough_source.astype(np.float32),(2048,2048),interpolation=cv2.INTER_AREA),0,255)))
 del rough_source;gc.collect()
 # AO is deliberately not invented. Metallic zero for dielectric wood/stone scan.
 orm=np.stack((np.full_like(rough,255),rough,np.zeros_like(rough)),axis=-1)
 runtime.mkdir(parents=True,exist_ok=True)
 for name,data in {"base_color.png":base,"normal_opengl.png":normgl,
       "normal_directx.png":normdx,"roughness.png":rough,"orm.png":orm}.items():
  Image.fromarray(data).save(runtime/name,compress_level=4)
 phys={"reference_id":"scan."+slug,"name":row["title"],
   "visual_source":"Poly Haven", "source_url":"https://polyhaven.com/a/"+slug,
   "source_authors":row["authors"],"license":"CC0-1.0",
   "source_physical_patch_mm":row["dimensions_mm"],
   "physical_reference_state":"bulk engineering grade not identified",
   "density_kg_m3":None,"strength_Pa":None,"bulk_material_assignment":False,
   "possible_external_physical_reference":row["candidate_physical_ref"],
   "candidate_reference_is_not_certification":True,
   "displacement_scale_mm":None,"measured_complex_ior":None,
   "unmeasured_optics":True}
 put(ROOT/"data/physical-profiles"/(slug+".json"),phys)
 metadata={"id":"scan."+slug, "name":row["title"],"kind":"photo_scanned_PBR",
   "physical_profile_id":phys["reference_id"],
   "source_hash":row["files_hash"],"license":"CC0-1.0",
   "provider":"Poly Haven","provider_source":phys["source_url"],
   "scan_extent_mm":row["dimensions_mm"],
   "runtime_resolution_px":2048,"source_resolution_px":4096,
   "roles":{k:v for k,v in receipts.items()},"roughness_channel":"G" if roles["roughness"]["role"]=="arm" else "L/first",
   "normal_source_convention":"OpenGL +Y vendor map",
   "glTF_normal_convention":"Green inverted for explicit Y-up UV/tangent convention",
   "status":"scanned_source_verified_not_native_accepted","premium_qualification":"pending_visual_and_native",
   "plugin_standard":None}
 put(ROOT/"data/appearance-records"/(slug+".json"),metadata)
 out=ROOT/"build/materials"/slug
 build_gltf(out,base,normdx,orm,row,metadata)
 build_preview(out/"preview.png",base,normgl,rough,row)
 del base,normdx,normgl,rough,orm;gc.collect()
 return metadata
def build_gltf(out,base,normal,orm,row,metadata):
 out.mkdir(parents=True,exist_ok=True)
 # Plane of original scan extent with curved comparator; geometry is illustrative.
 W=float(row["dimensions_mm"][0])/1000;H=float(row["dimensions_mm"][1])/1000
 positions=[[0,0,0],[W,0,0],[W,H,0],[0,H,0]]
 norms=[[0,0,1]]*4;uv=[[0,1],[1,1],[1,0],[0,0]];tangents=[[1,0,0,-1]]*4;indices=[0,1,2,0,2,3]
 cols,rows=32,8;r=W*1.1;start=4
 for j in range(rows+1):
  for i in range(cols+1):
   a=(i/cols-.5)*W/r
   positions.append([W*1.15+r*math.sin(a),j/rows*H,r*(1-math.cos(a))])
   norms.append([-math.sin(a),0,math.cos(a)])
   uv.append([i/cols,1-j/rows]);tangents.append([math.cos(a),0,math.sin(a),-1])
 for j in range(rows):
  for i in range(cols):
   a=start+j*(cols+1)+i;b=a+cols+1
   indices.extend([a,a+1,b+1,a,b+1,b])
 b=bytearray();views=[];accessors=[]
 def append(data,target=None):
  while len(b)%4:b.append(0)
  off=len(b);b.extend(data)
  while len(b)%4:b.append(0)
  v={"buffer":0,"byteOffset":off,"byteLength":len(data)}
  if target:v["target"]=target
  views.append(v);return len(views)-1
 def attr(data,num,component=5126,position=False,indices_attr=False):
  arr=np.asarray(data,dtype="<u4" if component==5125 else "<f4")
  idx=append(arr.reshape(-1).tobytes(),34963 if indices_attr else 34962)
  a={"bufferView":idx,"componentType":component,"count":len(arr),"type":{1:"SCALAR",2:"VEC2",3:"VEC3",4:"VEC4"}[num]}
  if position:
   a["min"]=[float(x) for x in arr.min(axis=0)];a["max"]=[float(x) for x in arr.max(axis=0)]
  accessors.append(a);return len(accessors)-1
 p=attr(positions,3,position=True);no=attr(norms,3);tx=attr(uv,2);ta=attr(tangents,4);ind=attr(indices,1,component=5125,indices_attr=True)
 ims=[]
 for mat in [base,orm,normal]:
  mem=io.BytesIO();Image.fromarray(mat).save(mem,format="PNG",compress_level=6)
  ims.append({"bufferView":append(mem.getvalue()),"mimeType":"image/png"})
 tree={"asset":{"version":"2.0","generator":"SolidCraft CC0 scanned reference PBR baseline"},
 "scenes":[{"nodes":[0]}],"scene":0,"nodes":[{"mesh":0,"name":row["title"]}],
 "meshes":[{"primitives":[{"attributes":{"POSITION":p,"NORMAL":no,"TEXCOORD_0":tx,"TANGENT":ta},"indices":ind,"material":0}]}],
 "materials":[{"name":row["title"],"doubleSided":True,"pbrMetallicRoughness":{
  "baseColorFactor":[1,1,1,1],"baseColorTexture":{"index":0},
  "metallicFactor":0,"roughnessFactor":1,"metallicRoughnessTexture":{"index":1}},
  "normalTexture":{"index":2},
  "extras":{"physical_reference_id":metadata["physical_profile_id"],
    "scan_extent_mm":row["dimensions_mm"],
    "source_license":"CC0-1.0","source_asset":metadata["provider_source"],
    "unmeasured_engineering_properties":True,"native_acceptance":"not_run"}}],
 "images":ims,"textures":[{"source":0},{"source":1},{"source":2}],
 "accessors":accessors,"bufferViews":views,"buffers":[{"byteLength":len(b)}]}
 external=json.loads(json.dumps(tree));external["buffers"][0]["uri"]="sample.bin"
 put(out/"material.gltf",external);(out/"sample.bin").write_bytes(b)
 js=json.dumps(tree,separators=(",",":")).encode("utf8");js+=b" "*((-len(js))%4)
 while len(b)%4:b.append(0)
 head=struct.pack("<4sII",b"glTF",2,12+8+len(js)+8+len(b))
 (out/"material.glb").write_bytes(head+struct.pack("<II",len(js),0x4e4f534a)+js+
                                   struct.pack("<II",len(b),0x004e4942)+bytes(b))
def build_preview(out,base,normal,rough,row):
 # An honest surface appearance thumbnail, not a synthetic photo of a manufactured part.
 w,h=1000,590
 im=Image.new("RGB",(w,h),(18,24,34))
 panel=Image.fromarray(base).resize((700,520),Image.Resampling.LANCZOS)
 im.paste(panel,(20,38))
 roughim=Image.fromarray(rough).resize((225,225),Image.Resampling.LANCZOS).convert("RGB")
 im.paste(roughim,(751,83))
 ni=Image.fromarray(normal).resize((225,225),Image.Resampling.LANCZOS)
 im.paste(ni,(751,337))
 draw=ImageDraw.Draw(im)
 draw.text((20,12),row["title"]+" / photographic color",fill=(231,236,244))
 draw.text((751,54),"Roughness",fill=(177,204,227))
 draw.text((751,310),"OpenGL normal",fill=(177,204,227))
 draw.text((20,567),"CC0 scan: Poly Haven | Measured source dimensions | NOT SolidCraft native",fill=(162,190,218))
 out.parent.mkdir(parents=True,exist_ok=True);im.save(out)
def main():
 parser=argparse.ArgumentParser();parser.add_argument("--full",action="store_true");args=parser.parse_args()
 catalog=json.loads(MANIFEST.read_text())
 assets=catalog["assets"]
 if not args.full:assets=assets[:1]
 out=[]
 for j,row in enumerate(assets):
  out.append(process(row))
  print("SCAN_VERIFIED",j+1,len(assets),row["slug"],flush=True)
 put(ROOT/"registry/resource-index.json",{"status":"source_hash_verified_not_native_qualified",
 "records":out,"source_license":"CC0-1.0","plugin_standard":None,
 "native_acceptance":"not_run","premium_visual_review":"pending"})
 html='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Scanned PBR Benchmarks</title><style>body{font:14px system-ui;background:#10161f;color:#e7eef5;padding:18px}h1{font-size:25px}main{display:grid;grid-template-columns:repeat(auto-fill,minmax(360px,1fr));gap:18px}article{border:1px solid #3a485e;background:#1b2737;border-radius:9px;padding:14px}img{width:100%}a{color:#99cbed}</style><h1>Scanned PBR quality benchmarks</h1><p>Real CC0 photo/scan-based surface maps. Source dimensions and original files pinned and verified. Native SolidCraft acceptance and measured engineering properties pending.</p><main>'''
 for v in out:
  slug=v["id"][5:]
  html+=f'<article><img loading="lazy" src="build/materials/{slug}/preview.png"><h3>{v["name"]}</h3><p>{v["scan_extent_mm"][0]:g} × {v["scan_extent_mm"][1]:g} mm photographed source</p><a href="build/materials/{slug}/material.glb">GLB specimen</a> | <a href="data/appearance-records/{slug}.json">Provenance and maps</a> | <a href="data/physical-profiles/{slug}.json">Physical identity</a></article>'
 html+='</main><footer>Powered by <a href="https://polyhaven.com">Poly Haven</a> — CC0 assets. Not a plugin interface.</footer></html>'
 (ROOT/"index.html").write_text(html,encoding="utf8")
 put(ROOT/"reports/build-summary.json",{"status":"GENERATED","assets":len(out),"master_resolution":4096,
 "runtime_resolution":2048,"scan_source":"Poly Haven CC0","native_acceptance":"not_run",
 "premium_qualification":"pending_visual_and_native","license":"CC0-1.0"})
if __name__=="__main__":main()
