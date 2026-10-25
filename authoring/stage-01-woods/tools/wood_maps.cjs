'use strict';
/** Original finite-board wood fields. No photographs, native engine, plugin loader or network.
 * Pixel coordinates have +U right, +V up. Height is millimetres; normals are derived from it.
 * Common-name species labels select illustrative anatomy/palettes, not measured appearance.
 */
const fs=require('node:fs'), path=require('node:path'), zlib=require('node:zlib'), crypto=require('node:crypto');
const A=path.resolve(__dirname,'..');
const load=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const save=(p,v)=>{fs.mkdirSync(path.dirname(p),{recursive:true});fs.writeFileSync(p,JSON.stringify(v,null,2)+'\n');};
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const clamp=(x,a=0,b=1)=>Math.min(b,Math.max(a,x));
const mix=(a,b,t)=>a+(b-a)*t;
const decode=x=>x<=.04045?x/12.92:Math.pow((x+.055)/1.055,2.4);
const encode=x=>{x=clamp(x);return x<=.0031308?12.92*x:1.055*Math.pow(x,1/2.4)-.055;};
const crcTable=Array.from({length:256},(_,n)=>{for(let k=0;k<8;k++)n=(n&1)?0xedb88320^(n>>>1):n>>>1;return n>>>0;});
function crc32(b){let c=0xffffffff;for(const x of b)c=crcTable[(c^x)&255]^(c>>>8);return(c^0xffffffff)>>>0;}
function chunk(type,data){const t=Buffer.from(type);const b=Buffer.alloc(data.length+12);b.writeUInt32BE(data.length,0);t.copy(b,4);data.copy(b,8);b.writeUInt32BE(crc32(Buffer.concat([t,data])),data.length+8);return b;}
function png(file,w,h,channels,depth,data,srgb=false){
  if(!Number.isInteger(w)||!Number.isInteger(h)||w<1||h<1||w>4096||h>4096)throw Error('bounded image dimensions required');
  if(![1,3].includes(channels)||![8,16].includes(depth))throw Error('unsupported PNG shape');
  const stride=w*channels*depth/8,bpp=channels*depth/8;
  if(data.length!==stride*h)throw Error('pixel byte count mismatch');
  const filtered=Buffer.alloc((stride+1)*h);
  for(let y=0;y<h;y++){const to=y*(stride+1),src=y*stride;filtered[to]=1;for(let x=0;x<stride;x++)filtered[to+1+x]=(data[src+x]-(x>=bpp?data[src+x-bpp]:0))&255;}
  const hdr=Buffer.alloc(13);hdr.writeUInt32BE(w,0);hdr.writeUInt32BE(h,4);hdr[8]=depth;hdr[9]=channels===3?2:0;
  const parts=[Buffer.from([137,80,78,71,13,10,26,10]),chunk('IHDR',hdr)];
  if(srgb)parts.push(chunk('sRGB',Buffer.from([0])));
  parts.push(chunk('IDAT',zlib.deflateSync(filtered,{level:6})),chunk('IEND',Buffer.alloc(0)));
  const result=Buffer.concat(parts);fs.mkdirSync(path.dirname(file),{recursive:true});fs.writeFileSync(file,result);
  return{sha256:sha(result),bytes:result.length,width:w,height:h,channels,bit_depth:depth,color_space:srgb?'sRGB':'linear_data'};
}
function hash(x,y,s){let n=Math.imul(x|0,374761393)^Math.imul(y|0,668265263)^Math.imul(s|0,1442695041);n=Math.imul(n^(n>>>13),1274126177);return((n^(n>>>16))>>>0)/4294967296;}
function noise(x,y,s){const i=Math.floor(x),j=Math.floor(y);let u=x-i,v=y-j;u=u*u*(3-2*u);v=v*v*(3-2*v);return mix(mix(hash(i,j,s),hash(i+1,j,s),u),mix(hash(i,j+1,s),hash(i+1,j+1,s),u),v);}
function field(x,y,wood,cut){
  const s=wood.seed,warp=(noise(x*.045,y*.017,s)-.5)*3.8;
  const wander=(noise(0,y*.012,s+41)-.5)*8;
  let radial,ray=0;
  if(cut==='plain-sawn')radial=Math.hypot(x-48-wander,14+.19*y+2*noise(0,y*.018,s+42))+warp;
  else if(cut==='quarter-sawn')radial=x+60+1.4*Math.sin(y*.014+s)+warp*.35;
  else if(cut==='rift-sawn')radial=x*.78+y*.052+70+.9*Math.sin(y*.019+s)+warp*.45;
  else if(cut==='end-grain'){
    const angle=Math.atan2(y-43,x-38);
    radial=Math.hypot(x-38,y-43)+.8*Math.sin(angle*3)+.36*Math.sin(angle*7)+warp*.48;
  }else throw Error('unknown cut');
  const phase=radial/wood.ring_pitch_mm+.72*noise(radial*.09,0,s+47)+.12*Math.sin(radial*.17+s);
  const ring=phase-Math.floor(phase);
  const late=Math.pow(clamp((ring-.48)/.48),1.5)*(1-clamp((ring-.94)/.06));
  const fine=noise((x+warp*.22)*6.8,y*(cut==='end-grain'?6.8:.8),s+3);
  const fibre=noise((x+warp*.23)*14.5,y*.115,s+5);
  const vessel=wood.pore_style!=='softwood';
  const cellX=cut==='end-grain'?1.6:2.6,cellY=cut==='end-grain'?1.6:.31;
  const ix=Math.floor(x*cellX),iy=Math.floor(y*cellY),pseed=hash(ix,iy,s+9);
  const dx=x*cellX-ix-(.15+.7*hash(ix,iy,s+10)),dy=y*cellY-iy-(.15+.7*hash(ix,iy,s+11));
  const pr=wood.pore_style==='diffuse'?.075:.16;
  const d=dx*dx/(pr*pr)+dy*dy/(cut==='end-grain'?pr*pr:.12);
  const ringMask=wood.pore_style==='ring'?.18+.82*(1-late):wood.pore_style==='semi-ring'?.55+.45*(1-late):1;
  const pore=vessel&&pseed>.36?Math.pow(clamp(1-d),2)*ringMask:0;
  if(cut==='quarter-sawn'){
    const rx=Math.floor(x/9),ry=Math.floor(y/4),rr=hash(rx,ry,s+27);
    const u=x/9-rx-(.2+.6*hash(rx,ry,s+28)),v=y/4-ry-(.2+.6*hash(rx,ry,s+29));
    if(rr>.32)ray=clamp(1-u*u/.2-v*v/.006)*wood.ray_strength;
  }else if(cut==='end-grain'){
    const theta=Math.atan2(y-43,x-38);ray=Math.pow(Math.max(0,Math.sin(theta*82+radial*.04)),18)*wood.ray_strength*.35;
  }
  const tone=clamp(.11+.68*late+.12*(1-fibre)+.06*(1-fine)-.24*ray);
  const h=.012*(fine-.5)+.008*(fibre-.5)+.018*late-.055*pore+.006*ray;
  return{tone,h,pore,ray,fine,roughness:clamp(.64+.10*late+.09*pore+.035*(fine-.5)-.045*ray,.1,1)};
}
function generateFields(wood,cut,n){
  if(!Number.isInteger(n)||n<16||n>2048)throw Error('bounded field dimensions: 16..2048');
  if(!Number.isSafeInteger(wood.seed)||wood.seed<0||wood.seed>4294967295)throw Error('invalid deterministic seed');
  if(!['plain-sawn','quarter-sawn','rift-sawn','end-grain'].includes(cut))throw Error('unknown cut');
  for(const key of ['early_srgb','late_srgb'])if(!Array.isArray(wood[key])||wood[key].length!==3||wood[key].some(v=>!Number.isFinite(v)||v<0||v>255))throw Error('bounded RGB palette required');
  if(!Number.isFinite(wood.ring_pitch_mm)||wood.ring_pitch_mm<.1||wood.ring_pitch_mm>20||!Number.isFinite(wood.ray_strength)||wood.ray_strength<0||wood.ray_strength>1)throw Error('invalid grain scale');
  const patch=cut==='end-grain'?[100,100]:[100,250],height=new Float32Array(n*n),color=new Float32Array(n*n*3),rough=new Float32Array(n*n);
  const a=wood.early_srgb.map(x=>decode(x/255)),b=wood.late_srgb.map(x=>decode(x/255));let min=Infinity,max=-Infinity;
  for(let j=0;j<n;j++)for(let i=0;i<n;i++){
    const k=j*n+i,f=field((i+.5)*patch[0]/n,(1-(j+.5)/n)*patch[1],wood,cut);
    height[k]=f.h;rough[k]=f.roughness;min=Math.min(min,f.h);max=Math.max(max,f.h);
    for(let c=0;c<3;c++)color[k*3+c]=clamp(mix(a[c],b[c],f.tone)*(1-.4*f.pore)*(.96+.08*f.fine)+.025*f.ray);
  }
  if(min<-.12||max>.12)throw Error('height exceeds declared scale');
  return{n,patch,height,color,rough,min,max};
}
function downsample(f){
  if(f.n%2)throw Error('even dimensions required');const n=f.n/2,h=new Float32Array(n*n),c=new Float32Array(n*n*3),r=new Float32Array(n*n);
  for(let y=0;y<n;y++)for(let x=0;x<n;x++){const o=y*n+x;for(let yy=0;yy<2;yy++)for(let xx=0;xx<2;xx++){const p=(2*y+yy)*f.n+2*x+xx;h[o]+=f.height[p]/4;r[o]+=f.rough[p]/4;for(let ch=0;ch<3;ch++)c[3*o+ch]+=f.color[3*p+ch]/4;}}
  return{n,patch:f.patch,height:h,color:c,rough:r,min:f.min,max:f.max};
}
function maps(f,folder){
  const n=f.n,count=n*n,base=Buffer.alloc(count*3),normal=Buffer.alloc(count*3),dx=Buffer.alloc(count*3),orm=Buffer.alloc(count*3),height=Buffer.alloc(count*2),rough=Buffer.alloc(count);
  const spacingX=f.patch[0]/n,spacingY=f.patch[1]/n;
  for(let y=0;y<n;y++)for(let x=0;x<n;x++){
    const k=y*n+x,left=Math.max(0,x-1),right=Math.min(n-1,x+1),up=Math.max(0,y-1),down=Math.min(n-1,y+1);
    const dhU=(f.height[y*n+right]-f.height[y*n+left])/((right-left)*spacingX);
    // +V points up; row index points down. Finite board edges use one-sided derivatives.
    const dhV=(f.height[up*n+x]-f.height[down*n+x])/((down-up)*spacingY);
    const len=Math.hypot(dhU,dhV,1),ns=[-dhU/len,-dhV/len,1/len];
    for(let c=0;c<3;c++){base[3*k+c]=Math.round(255*encode(f.color[3*k+c]));normal[3*k+c]=Math.round(255*(ns[c]*.5+.5));dx[3*k+c]=c===1?255-normal[3*k+c]:normal[3*k+c];}
    rough[k]=Math.round(f.rough[k]*255);orm[3*k]=255;orm[3*k+1]=rough[k];orm[3*k+2]=0;
    height.writeUInt16BE(Math.round((f.height[k]+.12)/.24*65535),2*k);
  }
  const out={};for(const [name,channels,depth,data,srgb] of [['base_color',3,8,base,true],['normal_opengl',3,8,normal,false],['normal_directx',3,8,dx,false],['orm',3,8,orm,false],['roughness',1,8,rough,false],['height_mm_u16',1,16,height,false]])out[name]=png(path.join(folder,name+'.png'),n,n,channels,depth,data,srgb);
  return out;
}
function preview(f,finish,output){
  const w=240,h=f.patch[0]===f.patch[1]?240:360,b=Buffer.alloc(w*h*3);
  for(let y=0;y<h;y++)for(let x=0;x<w;x++){
    const edge=Math.min(x,w-1-x,y,h-1-y),inside=edge>=9;
    const ix=Math.min(f.n-1,Math.floor((x-9)/(w-18)*f.n)),iy=Math.min(f.n-1,Math.floor((y-9)/(h-18)*f.n));
    const k=Math.max(0,iy)*f.n+Math.max(0,ix);const gloss=finish.clearcoat*.13*Math.exp(-Math.pow((x/w-.68)/(.045+finish.clearcoat_roughness*.35),2));
    for(let c=0;c<3;c++){
      let v=inside?f.color[k*3+c]*finish.color_multiplier_linear[c]*(.91+.09*y/h)+gloss:decode([28,33,38][c]/255);
      if(inside&&edge<12)v*=.65;
      b[(y*w+x)*3+c]=Math.round(255*encode(v));
    }
  }
  return png(output,w,h,3,8,b,true);
}
function build(wood,cut,finishes,out,n){
  const folder=path.join(out,'maps',wood.id,cut),f=generateFields(wood,cut,n),sets={};
  sets['master-'+n]=maps(f,path.join(folder,'master-'+n));let small=f;
  if(n>=2048){small=downsample(f);sets['runtime-'+small.n]=maps(small,path.join(folder,'runtime-'+small.n));}
  const info={id:wood.id+'/'+cut,physical_profile_id:wood.physical_profile_id,patch_mm:f.patch,wrap:'clamp_to_edge',seamless:false,height_encoding:{offset_mm:-.12,range_mm:.24,zero_u16:32767.5},normal_basis:'OpenGL: +U right, +V image-up, +N out. DirectX differs only in the green channel.',roughness:'authored perceptual roughness; not measured',metallic:0,ao:1,sets,observed_height_mm:[f.min,f.max],fidelity:'original procedural finite board; species appearance is illustrative',source_phenomena_certified:false};
  save(path.join(folder,'map-contract.json'),info);
  for(const finish of finishes)preview(small,finish,path.join(out,'previews',wood.id,cut,finish.id+'.png'));
  return info;
}
function main(){
  const woods=load(path.join(A,'data/woods.json')),finishes=load(path.join(A,'data/finishes.json')).finishes;
  const n=Number(process.env.WOOD_SIZE||2048);if(![256,512,1024,2048].includes(n))throw Error('supported sizes: 256,512,1024,2048');
  const out=path.resolve(process.env.WOOD_OUTPUT||path.join(A,'build'));
  const selected=process.env.WOOD_SPECIES?woods.woods.filter(w=>w.id===process.env.WOOD_SPECIES):woods.woods;
  if(selected.length===0)throw Error('unknown species');
  const cuts=process.env.WOOD_CUT?[process.env.WOOD_CUT]:woods.cuts;
  if(cuts.some(c=>!woods.cuts.includes(c)))throw Error('unknown cut');
  const records=[];const start=Date.now();for(const w of selected)for(const cut of cuts){records.push(build(w,cut,finishes,out,n));console.log('WOOD_MAPS',records.length,w.id,cut);}
  save(path.join(out,'map-index.json'),{status:'generated_not_native_qualified',resolution:n,mapsets:records.length,preview_count:records.length*finishes.length,seconds:(Date.now()-start)/1000,records});
}
if(require.main===module)main();
module.exports={field,generateFields,downsample,maps,preview,crc32,png,decode,encode};
