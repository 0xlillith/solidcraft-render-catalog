"""Metric-height and linear-color software preview; never native-render evidence."""
from pathlib import Path
import numpy as np
import cv2
from PIL import Image, ImageDraw
# Retain the original preview arithmetic precision for byte-exact reproduction.
def srgb(x):
 return np.where(x<=.0031308,12.92*x,1.055*np.maximum(x,0)**(1/2.4)-.055)
def linear(x):
 return np.where(x<=.04045,x/12.92,((x+.055)/1.055)**2.4)

def preview_normals(height, scale_mm, size=300):
 """Finite metric height gradients; image rows point down, OpenGL +V points up."""
 field=np.asarray(height,dtype=np.float32)
 scale=np.asarray(scale_mm,dtype=np.float64)
 if field.ndim!=2 or min(field.shape)<2 or not np.isfinite(field).all():
  raise ValueError('Finite two-dimensional physical height required')
 if scale.shape!=(2,) or not np.isfinite(scale).all() or (scale<=0).any():
  raise ValueError('Two positive physical patch dimensions in millimetres required')
 if not isinstance(size,int) or isinstance(size,bool) or not 2<=size<=1024:
  raise ValueError('Bounded preview dimension 2..1024 required')
 filtered=cv2.resize(field,(size,size),interpolation=cv2.INTER_AREA)
 gy,gx=np.gradient(filtered,scale[1]/size,scale[0]/size)
 result=np.stack((-gx,gy,np.ones_like(gx)),axis=-1)
 return result/np.linalg.norm(result,axis=-1,keepdims=True)

def preview(path,height,shade,rough,color,scale_mm):
 # Software visualization only: preserve physical slopes after thumbnail filtering.
 normal=preview_normals(height,scale_mm)
 ss=cv2.resize(shade,(300,300),interpolation=cv2.INTER_AREA)
 rr=cv2.resize(rough,(300,300),interpolation=cv2.INTER_AREA)
 direction=np.array([-.55,.65,.4],dtype=np.float32)
 direction/=np.linalg.norm(direction)
 light=np.maximum(.24,(normal*direction).sum(axis=-1))
 factor=np.stack(color)/255
 patch=np.clip(srgb(linear(factor)[None,None,:]*linear(ss)[:,:,None]*(.55+.6*light[:,:,None]) + (1-rr[:,:,None])*.045),0,1)
 sw=(patch*255).astype('uint8');im=Image.new('RGB',(560,330),(20,23,29));im.paste(Image.fromarray(sw),(15,15))
 strip=Image.fromarray(np.uint8(np.round(np.clip(srgb(linear(factor)[None,None,:]*linear(ss)[:,:,None]*.9),0,1)*255)))
 im.paste(strip.resize((215,260)),(330,32))
 dr=ImageDraw.Draw(im);dr.rectangle((326,286,549,310),fill=(30,33,40))
 dr.text((335,291),'Software preview - not native',fill=(205,211,221))
 path.parent.mkdir(parents=True,exist_ok=True);im.save(path)
