"""Original finite coarse-rock studies; physical centers and relief do not depend on pixels.

Neutral correlated mineral tones, irregular convex facets, and non-grid placement.
These are authored surface studies, not measured quarry grading or true displacement.
Do not apply these coarse-stone recipes to cement powder or fine sand.
"""
from __future__ import annotations
import numpy as np
import cv2
from channels import srgb_encode
RECIPES={
 'aggregate.exposed-stones':{'patch_mm':[180.,180.],'grid':9,'radius_mm':[6.,10.5],'height_mm':[.8,2.4],'angular':True,'seed':271041},
 'aggregate.tumbled-stones':{'patch_mm':[180.,180.],'grid':9,'radius_mm':[6.5,10.7],'height_mm':[1.,2.2],'angular':False,'seed':271042},
 'cement.exposed-stones':{'patch_mm':[240.,240.],'grid':13,'radius_mm':[3.5,8.4],'height_mm':[.25,.85],'angular':True,'seed':271043},
}
def layout(recipe):
 r=RECIPES[recipe];rng=np.random.default_rng(r['seed']);w,h=r['patch_mm'];out=[]
 for _ in range(r['grid']**2):
  radius=float(rng.uniform(*r['radius_mm']))
  for attempt in range(500):
   center=rng.uniform([0,0],[w,h])
   if all(np.linalg.norm(center-np.asarray(s['center_mm']))>=.78*(radius+max(s['axes_mm'])) for s in out):break
  else:raise ValueError('Could not place bounded non-grid clasts')
  lum=float(rng.uniform(.40,.94));warm=float(rng.uniform(-.045,.055));count=int(rng.integers(5,9))
  angles=np.arange(count)*2*np.pi/count+rng.uniform(-.17,.17,count);radii=rng.uniform(.80,1.12,count)
  points=np.stack((np.cos(angles)*radii,np.sin(angles)*radii),axis=-1).astype(np.float32)
  polygon=cv2.convexHull(points,clockwise=False).reshape(-1,2)
  area=np.sum(polygon[:,0]*np.roll(polygon[:,1],-1)-polygon[:,1]*np.roll(polygon[:,0],-1))
  if area<0:polygon=polygon[::-1]
  out.append({'center_mm':center.tolist(),'axes_mm':[radius,radius*float(rng.uniform(.66,1.06))],
    'angle':float(rng.uniform(0,2*np.pi)),'height_mm':float(rng.uniform(*r['height_mm'])),
    'tones':[lum*(1+warm),lum,lum*(1-warm)],'polygon':polygon.tolist(),'tilt':rng.uniform(-.18,.18,2).tolist()})
 return out

def fields(recipe,n):
 if recipe not in RECIPES or isinstance(n,bool) or not isinstance(n,int) or not 32<=n<=2048:
  raise ValueError('Known recipe and bounded 32..2048 resolution required')
 r=RECIPES[recipe];w,h=r['patch_mm'];yy,xx=np.mgrid[0:n,0:n].astype(np.float32);xx=(xx+.5)*w/n;yy=(yy+.5)*h/n
 grain=np.sin(xx*3.13+yy*.45)*np.sin(yy*4.41-xx*.3);fine=np.sin(xx*12.17-yy*2.7)*np.sin(yy*10.1+xx*.43)
 micro=(.018*grain+.005*fine).astype(np.float32)
 height=micro.copy();base=np.repeat((.48+.035*grain+.012*fine)[:,:,None],3,axis=2);rough=np.full((n,n),.87,np.float32);coverage=np.zeros((n,n),np.float32)
 for stone in layout(recipe):
  cx,cy=stone['center_mm'];rx,ry=stone['axes_mm'];radius=max(rx,ry)*1.22
  x0=max(0,int((cx-radius)*n/w));x1=min(n,int(np.ceil((cx+radius)*n/w)));y0=max(0,int((cy-radius)*n/h));y1=min(n,int(np.ceil((cy+radius)*n/h)))
  x=xx[y0:y1,x0:x1]-cx;y=yy[y0:y1,x0:x1]-cy;c=np.cos(stone['angle']);s=np.sin(stone['angle'])
  u=(c*x+s*y)/rx;v=(-s*x+c*y)/ry
  if r['angular']:
   poly=np.asarray(stone['polygon']);dist=np.full(u.shape,np.inf)
   for a,b in zip(poly,np.roll(poly,-1,axis=0)):
    edge=b-a;dist=np.minimum(dist,(edge[0]*(v-a[1])-edge[1]*(u-a[0]))/np.linalg.norm(edge))
   edge=np.clip(dist/.12,0,1);dome=np.clip(.88+stone['tilt'][0]*u+stone['tilt'][1]*v,.5,1)
  else:
   dist=np.hypot(u,v);edge=np.clip((1-dist)/.14,0,1);dome=np.maximum(0,1-dist*dist)**.5
  mask=edge*edge*(3-2*edge);elevation=stone['height_mm']*dome*mask
  patch=height[y0:y1,x0:x1];wins=elevation>patch;weight=(mask*wins).astype(np.float32)
  patch[:]=np.maximum(patch,elevation+micro[y0:y1,x0:x1]*.45)
  coverage[y0:y1,x0:x1]=np.maximum(coverage[y0:y1,x0:x1],mask)
  mineral=np.asarray(stone['tones'],np.float32)[None,None,:]*(1+.11*grain[y0:y1,x0:x1,None]+.035*fine[y0:y1,x0:x1,None])
  color=base[y0:y1,x0:x1];color[:]=color*(1-weight[:,:,None])+mineral*weight[:,:,None]
  rp=rough[y0:y1,x0:x1];rp[:]=rp*(1-weight)+(.66 if not r['angular'] else .79)*weight
 height-=float(np.mean(height));return height,np.clip(base,0,1),rough,coverage

def encoded(recipe,n):
 height,base,rough,coverage=fields(recipe,n);w,h=RECIPES[recipe]['patch_mm'];gy,gx=np.gradient(height,h/n,w/n)
 normal=np.stack((-gx,gy,np.ones_like(gx)),axis=-1);normal/=np.linalg.norm(normal,axis=-1,keepdims=True)
 ng=np.rint((normal*.5+.5)*255).clip(0,255).astype(np.uint8);nd=ng.copy();nd[:,:,1]=255-nd[:,:,1]
 rr=np.rint(rough*255).clip(0,255).astype(np.uint8);zero=np.zeros_like(rr)
 return {'base_color':np.rint(srgb_encode(base)*255).astype(np.uint8),'normal_opengl':ng,'normal_directx':nd,'roughness':rr,'metallic':zero,'orm':np.stack((np.full_like(rr,255),rr,zero),axis=-1),'height_mm_u16':np.rint(np.clip((height+8)/16,0,1)*65535).astype(np.uint16)},height,coverage
