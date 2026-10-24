"""Original local asset authoring utilities. MIT OR Apache-2.0.
World geometry is authored in millimetres, right-handed Z-up. glTF exports are metres, Y-up.
No application source or user design is modified. Derived preview images are labelled.
"""
from __future__ import annotations
from pathlib import Path
import base64, copy, hashlib, io, json, math, os, struct, sys
import numpy as np
from PIL import Image, PngImagePlugin
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/_deps'))
import OpenEXR
SOURCE=ROOT/'source/docs/render-materials'
VERSION='1.0.0-local'
LICENSE='MIT OR Apache-2.0'

def load(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def dump(p,d):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def fingerprint(data):return hashlib.sha256(json.dumps(data,sort_keys=True,allow_nan=False).encode()).hexdigest()
def unit(v):
    v=np.asarray(v,dtype=np.float64); n=np.linalg.norm(v,axis=-1,keepdims=True)
    return v/np.maximum(n,1e-16)
def srgb(a):
    a=np.maximum(np.asarray(a),0);return np.where(a<=.0031308,12.92*a,1.055*a**(1/2.4)-.055)
def linear(a):
    a=np.asarray(a);return np.where(a<=.04045,a/12.92,((a+.055)/1.055)**2.4)
def rgbhex(h):return linear(np.array([int(h[i:i+2],16) for i in (0,2,4)])/255).tolist()
def png(p,a,encoding='linear_data'):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);a=np.asarray(a)
    info=PngImagePlugin.PngInfo();info.add_text('Author','Original SolidCraft contributor authoring');info.add_text('License',LICENSE);info.add_text('Encoding',encoding)
    if encoding=='srgb':info.add(b'sRGB',b'\x00')
    Image.fromarray(a).save(p,compress_level=3,pnginfo=info)
def exr(p,channels,description):
    header={'compression':OpenEXR.ZIP_COMPRESSION,'type':OpenEXR.scanlineimage,'comments':description,'owner':'Original SolidCraft contributors','colorSpace':'linear sRGB / D65'}
    arrays={k:np.ascontiguousarray(v,dtype=np.float32) for k,v in channels.items()}
    with OpenEXR.File(header,arrays) as f:f.write(str(p))
def hdr(p,rgb):
    rgb=np.asarray(rgb,dtype=np.float64)
    if rgb.ndim!=3 or rgb.shape[2]!=3 or not np.isfinite(rgb).all() or rgb.min()<0 or rgb.max()>1e6:raise ValueError('invalid bounded RGBE source')
    h,w,_=rgb.shape;maximum=rgb.max(axis=2);mantissa,exponent=np.frexp(maximum)
    scale=np.where(maximum>1e-32,mantissa*256/np.maximum(maximum,1e-32),0)
    b=np.empty((h,w,4),np.uint8);b[:,:,:3]=np.clip(rgb*scale[:,:,None],0,255).astype(np.uint8);b[:,:,3]=np.where(maximum>1e-32,exponent+128,0).astype(np.uint8)
    with Path(p).open('wb') as f:
        f.write(('#?RADIANCE\n# Original deterministic local catalogue; relative radiance, not measured\nFORMAT=32-bit_rle_rgbe\nPRIMARIES=0.64 0.33 0.30 0.60 0.15 0.06 0.3127 0.3290\n\n-Y %d +X %d\n'%(h,w)).encode())
        for row in b:
            f.write(bytes([2,2,w>>8,w&255]))
            for c in range(4):
                a=row[:,c];i=0
                while i<w:
                    j=i+1
                    while j<min(w,i+127) and a[j]==a[i]:j+=1
                    if j-i>=4:f.write(bytes([128+j-i,int(a[i])]));i=j;continue
                    end=min(w,i+128);j=i+1
                    while j<end:
                        if j+3<w and a[j]==a[j+1]==a[j+2]==a[j+3]:break
                        j+=1
                    f.write(bytes([j-i]));f.write(a[i:j].tobytes());i=j
    return b

def decode_hdr(p):
    with Path(p).open('rb') as f:
        lines=[]
        while True:
            s=f.readline()
            if not s:raise ValueError('missing RGBE resolution')
            if s.startswith(b'-Y '):h,w=int(s.split()[1]),int(s.split()[3]);break
            lines.append(s)
        out=np.empty((h,w,4),np.uint8)
        for y in range(h):
            assert f.read(4)==bytes([2,2,w>>8,w&255])
            for c in range(4):
                x=0
                while x<w:
                    n=f.read(1)[0]
                    if n>128:k=n-128;out[y,x:x+k,c]=f.read(1)[0]
                    else:k=n;out[y,x:x+k,c]=np.frombuffer(f.read(k),np.uint8)
                    x+=k
                assert x==w
        assert not f.read(1)
    e=out[:,:,3].astype(np.int32);return np.where(e[:,:,None]>0,out[:,:,:3].astype(np.float32)*np.exp2(e-136)[:,:,None],0).astype(np.float32)

def sphere_mesh(radius=20.,segments=48,rings=24):
    p=[];n=[];uv=[];t=[];ind=[]
    for j in range(rings+1):
        theta=np.pi*j/rings
        for i in range(segments+1):
            phi=2*np.pi*i/segments;x,y,z=np.sin(theta)*np.cos(phi),np.sin(theta)*np.sin(phi),np.cos(theta)
            p.append([radius*x,radius*y,radius*z]);n.append([x,y,z]);uv.append([i/segments,j/rings]);t.append([-np.sin(phi),np.cos(phi),0,1])
    for j in range(rings):
        for i in range(segments):
            a=j*(segments+1)+i;b=a+segments+1
            if j>0:ind.extend([a,b,a+1])
            if j<rings-1:ind.extend([a+1,b,b+1])
    return {'positions':np.array(p),'normals':np.array(n),'uv':np.array(uv),'tangents':np.array(t),'indices':np.array(ind,dtype=np.uint32)}

def mesh_triangles(vertices,faces):
    vertices=np.asarray(vertices,dtype=np.float64);faces=np.asarray(faces,dtype=np.uint32).reshape(-1,3)
    tri=vertices[faces];norm=unit(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]));p=tri.reshape(-1,3);n=np.repeat(norm,3,axis=0)
    return {'positions':p,'normals':n,'indices':np.arange(len(p),dtype=np.uint32)}

def box_mesh(center,size):
    c=np.asarray(center);s=np.asarray(size)/2
    v=np.array([[x,y,z] for z in (-1,1) for y in (-1,1) for x in (-1,1)])*s+c
    f=[[0,2,3],[0,3,1],[4,5,7],[4,7,6],[0,1,5],[0,5,4],[2,6,7],[2,7,3],[0,4,6],[0,6,2],[1,3,7],[1,7,5]]
    return mesh_triangles(v,f)

def panel_mesh(center,u,v):
    c=np.asarray(center);u=np.asarray(u);v=np.asarray(v)
    return mesh_triangles([c-u-v,c+u-v,c+u+v,c-u+v],[[0,1,2],[0,2,3]])

def transformed_mesh(m,scale,translation):
    r={k:v.copy() for k,v in m.items()};r['positions']=m['positions']*np.asarray(scale)+np.asarray(translation);r['normals']=unit(m['normals']/np.asarray(scale));return r

def export_gltf(folder,name,meshes,materials,extras=None,embed=True):
    """Write core glTF and self-contained GLB with original geometry. Each mesh names a material index."""
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True);buf=bytearray()
    doc={'asset':{'version':'2.0','generator':'SolidCraft Local Catalog Author '+VERSION,'copyright':'Original SolidCraft contributors; '+LICENSE},'scene':0,'scenes':[{'nodes':list(range(len(meshes)))}],'nodes':[],'meshes':[],'materials':copy.deepcopy(materials),'buffers':[],'bufferViews':[],'accessors':[]}
    if extras:doc['extras']=extras
    def view(data,target=None):
        while len(buf)%4:buf.append(0)
        off=len(buf);buf.extend(data);v={'buffer':0,'byteOffset':off,'byteLength':len(data)}
        if target:v['target']=target
        doc['bufferViews'].append(v);return len(doc['bufferViews'])-1
    def acc(a,typ,ct,target,bounds=False):
        a=np.ascontiguousarray(a,dtype='<f4' if ct==5126 else '<u4');v=view(a.tobytes(),target);d={'bufferView':v,'componentType':ct,'count':len(a),'type':typ}
        if bounds:d.update(min=a.min(axis=0).tolist(),max=a.max(axis=0).tolist())
        doc['accessors'].append(d);return len(doc['accessors'])-1
    images=[];textures=[]
    for mat in doc['materials']:
        slots=mat.pop('_textures',{})
        for role,relative in slots.items():
            if relative not in images:images.append(relative);textures.append({'source':len(images)-1,'sampler':0})
            idx=images.index(relative)
            if role=='base':mat['pbrMetallicRoughness']['baseColorTexture']={'index':idx}
            elif role=='mr':mat['pbrMetallicRoughness']['metallicRoughnessTexture']={'index':idx}
            elif role=='normal':mat['normalTexture']={'index':idx,'scale':1.0}
            elif role=='occlusion':mat['occlusionTexture']={'index':idx,'strength':1.0}
            elif role=='emissive':mat['emissiveTexture']={'index':idx}
    exts=sorted({k for m in doc['materials'] for k in m.get('extensions',{})})
    if exts:doc['extensionsUsed']=exts
    if images:doc.update(images=[{'uri':x} for x in images],textures=textures,samplers=[{'magFilter':9729,'minFilter':9987,'wrapS':10497,'wrapT':10497}])
    for idx,item in enumerate(meshes):
        m=item['mesh'];p=np.asarray(m['positions']);n=np.asarray(m['normals']);p=np.stack([p[:,0],p[:,2],-p[:,1]],axis=1)*.001;n=np.stack([n[:,0],n[:,2],-n[:,1]],axis=1)
        attrs={'POSITION':acc(p,'VEC3',5126,34962,True),'NORMAL':acc(n,'VEC3',5126,34962)}
        if 'uv' in m:attrs['TEXCOORD_0']=acc(m['uv'],'VEC2',5126,34962)
        if 'tangents' in m:
            t=m['tangents'];t=np.stack([t[:,0],t[:,2],-t[:,1],t[:,3]],axis=1);attrs['TANGENT']=acc(t,'VEC4',5126,34962)
        prim={'attributes':attrs,'indices':acc(m['indices'].reshape(-1),'SCALAR',5125,34963),'material':item.get('material',0),'mode':4}
        doc['meshes'].append({'name':item['name'],'primitives':[prim]});doc['nodes'].append({'name':item['name'],'mesh':idx})
    doc['buffers']=[{'uri':name+'.bin','byteLength':len(buf)}];(folder/(name+'.bin')).write_bytes(buf);dump(folder/(name+'.gltf'),doc)
    if embed:
        gd=copy.deepcopy(doc)
        if images:
            for image,rel in zip(gd['images'],images):
                data=(folder/rel).read_bytes()
                while len(buf)%4:buf.append(0)
                gd['bufferViews'].append({'buffer':0,'byteOffset':len(buf),'byteLength':len(data)});buf.extend(data)
                image.clear();image.update(bufferView=len(gd['bufferViews'])-1,mimeType='image/png')
        gd['buffers']=[{'byteLength':len(buf)}];j=json.dumps(gd,separators=(',',':'),allow_nan=False).encode();j+=b' '*((-len(j))%4);buf.extend(b'\0'*((-len(buf))%4))
        with (folder/(name+'.glb')).open('wb') as f:f.write(struct.pack('<III',0x46546c67,2,12+8+len(j)+8+len(buf))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(buf),0x004e4942)+buf)
    return doc

def simple_material(name,color,roughness=.65,metallic=0):
    return {'name':name,'pbrMetallicRoughness':{'baseColorFactor':[float(x) for x in color]+[1.0],'metallicFactor':float(metallic),'roughnessFactor':float(roughness)},'doubleSided':True}

def save_obj(folder,name,meshes,materials):
    lines=['# Original procedural scene; units millimetres, Z-up',f'mtllib {name}.mtl'];base=1
    for item in meshes:
        m=item['mesh'];lines+=[f'o {item["name"]}',f'usemtl material_{item.get("material",0)}']
        lines+=['v %.7g %.7g %.7g'%tuple(p) for p in m['positions']]
        for tri in m['indices'].reshape(-1,3):lines.append('f '+' '.join(str(base+int(i)) for i in tri))
        base+=len(m['positions'])
    (Path(folder)/(name+'.obj')).write_text('\n'.join(lines)+'\n',encoding='utf-8')
    out=['# Approximate scalar display fallback; glTF is the richer material representation.']
    for i,m in enumerate(materials):
        col=m['pbrMetallicRoughness']['baseColorFactor'][:3];out +=[f'newmtl material_{i}','Kd %.6g %.6g %.6g'%tuple(col),'Ks 0.04 0.04 0.04','Ns 20']
    (Path(folder)/(name+'.mtl')).write_text('\n'.join(out)+'\n',encoding='utf-8')
