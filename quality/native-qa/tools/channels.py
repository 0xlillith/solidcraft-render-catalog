"""Color-correct native profiles and explicit, non-destructive finish baking.

Inputs and archived high-resolution originals remain unchanged. These operations
are authored appearance transforms, not physical measurements or new substances.
"""
from __future__ import annotations
import numpy as np
import cv2

def srgb_decode(a):
    x=np.asarray(a,dtype=np.float32)
    return np.where(x<=.04045,x/12.92,((x+.055)/1.055)**2.4)

def srgb_encode(a):
    x=np.clip(np.asarray(a,dtype=np.float32),0,1)
    return np.where(x<=.0031308,12.92*x,1.055*x**(1/2.4)-.055)

def _check(a,channels=None):
    x=np.asarray(a)
    if x.dtype!=np.uint8 or x.ndim not in (2,3) or min(x.shape[:2])<1:
        raise ValueError('An 8-bit, nonempty map is required')
    if channels is not None and (x.ndim!=3 or x.shape[2]!=channels):
        raise ValueError(f'Expected {channels} channels')
    if max(x.shape[:2])>4096:raise ValueError('Source map exceeds bounded 4K contract')
    return x

def _size(size,shape):
    if not isinstance(size,int) or isinstance(size,bool) or size<1 or size>1024 or size>min(shape[:2]):
        raise ValueError('Native profile must be 1..1024 pixels and must not upscale')
    return size

def albedo(a,*,size=None,multiplier=(1.,1.,1.)):
    a=_check(a,3);m=np.asarray(multiplier,dtype=np.float32)
    if m.shape!=(3,) or not np.isfinite(m).all() or (m<0).any() or (m>1).any():
        raise ValueError('Authored color multiplier must be finite RGB in 0..1')
    linear=srgb_decode(a.astype(np.float32)/255)*m
    if size is not None:
        n=_size(size,a.shape);linear=cv2.resize(linear,(n,n),interpolation=cv2.INTER_AREA)
    return np.rint(srgb_encode(linear)*255).astype(np.uint8)

def normals(a,*,size=None,strength=1.):
    a=_check(a,3)
    if not np.isfinite(strength) or not 0<=strength<=1:raise ValueError('Normal strength must be in 0..1')
    v=a.astype(np.float32)/127.5-1
    if size is not None:
        n=_size(size,a.shape);v=cv2.resize(v,(n,n),interpolation=cv2.INTER_AREA)
    # Never gamma-filter a direction. Finish smoothing applies once to tangent XY.
    v[...,:2]*=strength;length=np.linalg.norm(v,axis=-1,keepdims=True)
    if not np.isfinite(v).all() or (length<1e-6).any():raise ValueError('Degenerate filtered normal')
    return np.rint(np.clip(v/length*.5+.5,0,1)*255).astype(np.uint8)

def roughness(a,*,size=None,factor=1.):
    a=_check(a)
    if a.ndim!=2:raise ValueError('Roughness is a scalar linear-data channel')
    if not np.isfinite(factor) or not 0<factor<=1:raise ValueError('Roughness factor must be in (0,1]')
    v=a.astype(np.float32)/255
    if size is not None:
        n=_size(size,a.shape);v=cv2.resize(v,(n,n),interpolation=cv2.INTER_AREA)
    return np.rint(np.clip(v*factor,.045,1)*255).astype(np.uint8)

def orm(rough,metallic=0):
    r=_check(rough)
    if r.ndim!=2 or metallic not in (0,1):raise ValueError('Expected scalar roughness and metallic 0 or 1')
    return np.stack((np.full_like(r,255),r,np.full_like(r,255*metallic)),axis=-1)

def materialize(base,normal,rough,finish,*,size=None):
    if base.shape[:2]!=normal.shape[:2] or base.shape[:2]!=rough.shape[:2]:raise ValueError('Map dimensions differ')
    coat=float(finish.get('clearcoat',0));coat_rough=float(finish.get('clearcoat_roughness',.4))
    if not np.isfinite([coat,coat_rough]).all() or not 0<=coat<=1 or not .045<=coat_rough<=1:
        raise ValueError('Invalid authored coat contract')
    b=albedo(base,size=size,multiplier=finish.get('color_multiplier_linear',(1,1,1)))
    n=normals(normal,size=size,strength=finish.get('normal_scale',1))
    r=roughness(rough,size=size,factor=finish.get('roughness_factor',1))
    dx=n.copy();dx[:,:,1]=255-dx[:,:,1]
    return {'base_color':b,'normal_opengl':n,'normal_directx':dx,'roughness':r,'orm':orm(r)}, {'weight':coat,'roughness':coat_rough,'ior':1.5,'basis':'original authored coating approximation, not measured chemistry or thickness'}
