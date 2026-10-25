'use strict';
/** Original finite machining/finish fields; no imported photographs or renderer code. */
const fs=require('node:fs'),path=require('node:path');
const I=require('./image_io.cjs'),{png,sha,clamp,encode,decode,noise}=I;
const A=path.resolve(__dirname,'..'),load=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const save=(p,v)=>{fs.mkdirSync(path.dirname(p),{recursive:true});fs.writeFileSync(p,JSON.stringify(v,null,2)+'\n');};
const normalize=a=>{const l=Math.hypot(...a);if(!Number.isFinite(l)||l<1e-15)throw Error('degenerate vector');return a.map(x=>x/l);};
const dot=(a,b)=>a.reduce((s,x,i)=>s+x*b[i],0),cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
function field(x,y,f){
  const s=127+f.pattern.length*17;
  const grain=noise(x*2.3,y*2.3,s)-.5,fine=noise(x*23,y*23,s+9)-.5;
  const streak=noise(x*.13,y*13,s+41)-.5;
  let h,structure;
  switch(f.pattern){
    case 'polished':h=.35*fine+.12*streak;structure=.03*grain;break;
    case 'brushed':h=.6*Math.sin(2*Math.PI*(y/.22+.035*noise(x*.3,y,s)))+.35*streak+.08*fine;structure=.08*streak;break;
    case 'cross':h=.35*Math.sin(2*Math.PI*(y/.27+x*.04))+.35*Math.sin(2*Math.PI*(x/.31-y*.025))+.18*fine;structure=.1*grain;break;
    case 'ground':h=.7*Math.sin(2*Math.PI*y/.105)+.2*noise(x*.1,y*9,s+12)+.08*fine;structure=.06*streak;break;
    case 'turned':{const r=Math.hypot(x+8,y-20);h=.72*Math.cos(2*Math.PI*(r/.28+.01*grain))+.06*fine;structure=.06*grain;break;}
    case 'milled':{const row=Math.floor(y/5),cx=Math.floor((x+(row%2)*3)/6)*6+3-(row%2)*3,cy=row*5+2.5,r=Math.hypot(x-cx,y-cy);h=.68*Math.cos(2*Math.PI*r/.24)+.14*Math.cos(2*Math.PI*y/5)+.06*fine;structure=.1*grain;break;}
    case 'blasted':h=.7*grain+.26*noise(x*8,y*8,s+31)+.08*fine;structure=.11*grain;break;
    case 'scuffed':{let scratches=0;for(let i=0;i<7;i++){const angle=i*.42+.13,offset=2+i*5.2,d=x*Math.cos(angle)+y*Math.sin(angle)-offset;scratches+=Math.exp(-d*d/(.035*.035))*Math.max(0,1-Math.abs(y-17)/20);}h=.3*grain+.15*fine-.48*scratches;structure=.06*grain-.035*scratches;break;}
    default:throw Error('unknown finish pattern');
  }
  return {h:h*f.height_amplitude_mm,tone:clamp(.98+structure,.75,1),rough:clamp(f.roughness+.04*grain+.035*streak,.045,.95)};
}
function fields(f,n){
  if(!Number.isInteger(n)||n<32||n>2048||(n&(n-1)))throw Error('Power-of-two size 32..2048 required');
  if(!Number.isFinite(f.height_amplitude_mm)||f.height_amplitude_mm<0||f.height_amplitude_mm>.02||!Number.isFinite(f.roughness)||f.roughness<.045||f.roughness>1)throw Error('bounded finish required');
  const h=new Float32Array(n*n),t=new Float32Array(n*n),r=new Float32Array(n*n);
  for(let j=0;j<n;j++)for(let i=0;i<n;i++){const k=j*n+i,v=field((i+.5)*40/n,(1-(j+.5)/n)*40,f);h[k]=v.h;t[k]=v.tone;r[k]=v.rough;}
  return {n,h,t,r,patch_mm:[40,40]};
}
function downsample(f){
  if(f.n%2||f.n<2)throw Error('Even field size required');const n=f.n/2,o={n,h:new Float32Array(n*n),t:new Float32Array(n*n),r:new Float32Array(n*n),patch_mm:f.patch_mm};
  for(let y=0;y<n;y++)for(let x=0;x<n;x++){const k=y*n+x,p=2*y*f.n+2*x;for(const key of ['h','t','r'])o[key][k]=(f[key][p]+f[key][p+1]+f[key][p+f.n]+f[key][p+f.n+1])/4;}return o;
}
function normalAt(f,x,y){const n=f.n,x0=Math.max(0,x-1),x1=Math.min(n-1,x+1),y0=Math.max(0,y-1),y1=Math.min(n-1,y+1);const du=(f.h[y*n+x1]-f.h[y*n+x0])/((x1-x0)*f.patch_mm[0]/n),dv=(f.h[y0*n+x]-f.h[y1*n+x])/((y1-y0)*f.patch_mm[1]/n);return normalize([-du,-dv,1]);}
function maps(f,folder){
  const n=f.n,b=Buffer.alloc(n*n*3),g=Buffer.alloc(n*n*3),d=Buffer.alloc(n*n*3),orm=Buffer.alloc(n*n*3),rough=Buffer.alloc(n*n),height=Buffer.alloc(n*n*2),metal=Buffer.alloc(n*n,255);
  for(let y=0;y<n;y++)for(let x=0;x<n;x++){const k=y*n+x;if(!Number.isFinite(f.h[k])||f.h[k]<-.05||f.h[k]>.05)throw Error('Height out of encoding');const normal=normalAt(f,x,y);for(let c=0;c<3;c++){b[3*k+c]=Math.round(encode(f.t[k])*255);g[3*k+c]=Math.round((normal[c]*.5+.5)*255);d[3*k+c]=c===1?255-g[3*k+c]:g[3*k+c];}rough[k]=Math.round(f.r[k]*255);orm[3*k]=255;orm[3*k+1]=rough[k];orm[3*k+2]=255;height.writeUInt16BE(Math.round((f.h[k]+.05)/.1*65535),2*k);}
  let result={};for(const [name,channels,depth,data,srgb] of [['base_color',3,8,b,true],['normal_opengl',3,8,g,false],['normal_directx',3,8,d,false],['roughness',1,8,rough,false],['metallic',1,8,metal,false],['orm',3,8,orm,false],['height_mm_u16',1,16,height,false]])result[name]=png(path.join(folder,name+'.png'),n,n,channels,depth,data,srgb);
  return result;
}
function preview(p,f,small,file){
  const w=480,h=300,out=Buffer.alloc(w*h*3),V=[0,0,1],lights=[{l:normalize([-.7,.5,1]),power:1.8},{l:normalize([.8,.25,.8]),power:.9},{l:normalize([-.1,-.9,.5]),power:.45}];
  for(let y=0;y<h;y++)for(let x=0;x<w;x++){
    let nx=(x-155)/124,ny=(145-y)/124;let mask=nx*nx+ny*ny<1,N,tx,ty;
    if(mask){N=[nx,ny,Math.sqrt(Math.max(0,1-nx*nx-ny*ny))];tx=clamp(.5+Math.atan2(nx,N[2])/(2*Math.PI));ty=clamp(.5-Math.asin(ny)/Math.PI);}
    else if(x>=315&&x<461&&y>38&&y<260){mask=true;N=normalize([.05,.15,1]);tx=(x-315)/146;ty=(y-38)/222;}
    if(!mask){const j=3*(y*w+x);out[j]=22;out[j+1]=27;out[j+2]=35;continue;}
    const ix=Math.min(small.n-1,Math.floor(tx*small.n)),iy=Math.min(small.n-1,Math.floor(ty*small.n)),k=iy*small.n+ix,t=normalAt(small,ix,iy);
    const T=normalize(Math.abs(N[1])<.99?cross([0,1,0],N):cross([1,0,0],N)),B=cross(N,T);N=normalize(N.map((v,i)=>T[i]*t[0]+B[i]*t[1]+v*t[2]));
    const nv=Math.max(.001,dot(N,V)),rough=small.r[k],a=rough*rough,aa=a*a;let rgb=p.appearance_palette_linear.map(v=>v*small.t[k]*(.035+.10*Math.max(0,N[1])+.035*nv));
    for(const {l,power} of lights){const nl=Math.max(0,dot(N,l));if(!nl)continue;const H=normalize(l.map((v,i)=>v+V[i])),nh=Math.max(0,dot(N,H)),vh=Math.max(0,dot(V,H)),D=aa/(Math.PI*Math.pow(nh*nh*(aa-1)+1,2)),G=2*nv/(nv+Math.sqrt(aa+(1-aa)*nv*nv))*2*nl/(nl+Math.sqrt(aa+(1-aa)*nl*nl));for(let c=0;c<3;c++){const f0=p.appearance_palette_linear[c]*small.t[k],F=f0+(1-f0)*Math.pow(1-vh,5);rgb[c]+=power*D*G*F/(4*Math.max(nv,.001));}}
    for(let c=0;c<3;c++){const v=rgb[c]*1.3;out[3*(y*w+x)+c]=Math.round(encode(v/(1+v))*255);}
  }
  return png(file,w,h,3,8,out,true);
}
function sphereGeometry(){
  const pos=[],norm=[],uv=[],tan=[],indices=[],cols=48,rows=24;
  for(let y=0;y<=rows;y++)for(let x=0;x<=cols;x++){const v=y/rows,u=x/cols,ph=2*Math.PI*u,th=Math.PI*v,s=Math.sin(th),c=Math.cos(th);pos.push(.02*s*Math.cos(ph),.02*c,.02*s*Math.sin(ph));norm.push(s*Math.cos(ph),c,s*Math.sin(ph));uv.push(u,v);tan.push(-Math.sin(ph),0,Math.cos(ph),1);}
  for(let y=0;y<rows;y++)for(let x=0;x<cols;x++){const a=y*(cols+1)+x,b=a+cols+1;if(y>0)indices.push(a,a+1,b);if(y<rows-1)indices.push(a+1,b+1,b);}
  return {pos,norm,uv,tan,indices};
}
function gltf(p,f,dir,mapsDir){
  const data=sphereGeometry(),parts=[],views=[],accessors=[];let size=0;
  function add(array,type,n,typeName,target){let raw=type==='float'?Buffer.from(new Float32Array(array).buffer):Buffer.from(new Uint32Array(array).buffer);const pad=(4-size%4)%4;if(pad){parts.push(Buffer.alloc(pad));size+=pad;}const offset=size;parts.push(raw);size+=raw.length;views.push({buffer:0,byteOffset:offset,byteLength:raw.length,target});let a={bufferView:views.length-1,componentType:type==='float'?5126:5125,count:array.length/n,type:typeName};if(typeName==='VEC3'&&accessors.length===0){a.min=[-.02,-.02,-.02];a.max=[.02,.02,.02];}accessors.push(a);return accessors.length-1;}
  const attrs={POSITION:add(data.pos,'float',3,'VEC3',34962),NORMAL:add(data.norm,'float',3,'VEC3',34962),TEXCOORD_0:add(data.uv,'float',2,'VEC2',34962),TANGENT:add(data.tan,'float',4,'VEC4',34962)},idx=add(data.indices,'uint',1,'SCALAR',34963),bin=Buffer.concat(parts);
  fs.mkdirSync(dir,{recursive:true});fs.writeFileSync(path.join(dir,'sample.bin'),bin);
  const uri=name=>path.relative(dir,path.join(mapsDir,name+'.png')).split(path.sep).join('/');
  const doc={asset:{version:'2.0',generator:'Original alloy-authoring-stage02/1'},scene:0,scenes:[{nodes:[0]}],nodes:[{name:p.name+' / '+f.name,mesh:0}],meshes:[{primitives:[{attributes:attrs,indices:idx,material:0}]}],materials:[{name:p.name+' / '+f.name,pbrMetallicRoughness:{baseColorFactor:[...p.appearance_palette_linear,1],baseColorTexture:{index:0},metallicFactor:1,roughnessFactor:1,metallicRoughnessTexture:{index:1}},normalTexture:{index:2},extras:{physical_profile_id:p.id,source_condition:p.condition,patch_mm:[40,40],mapping:'Spherical illustration only. Actual flat patch scale 40 mm, no global CAD UV claim. The normal data green is converted for this explicit top-left UV/tangent basis; native +V-up maps remain separate.',premium_qualification:'pending',optical_constants:'unmeasured illustrative RGB'}}],textures:[{source:0,sampler:0},{source:1,sampler:0},{source:2,sampler:0}],images:[{uri:uri('base_color')},{uri:uri('orm')},{uri:uri('normal_directx')}],samplers:[{magFilter:9729,minFilter:9729,wrapS:33071,wrapT:33071}],buffers:[{uri:'sample.bin',byteLength:bin.length}],bufferViews:views,accessors};
  save(path.join(dir,'material.gltf'),doc);
  const embedded=JSON.parse(JSON.stringify(doc));delete embedded.buffers[0].uri;
  let binary=Buffer.from(bin);for(let i=0;i<doc.images.length;i++){const raw=fs.readFileSync(path.resolve(dir,doc.images[i].uri)),pad=(4-binary.length%4)%4;if(pad)binary=Buffer.concat([binary,Buffer.alloc(pad)]);const offset=binary.length;binary=Buffer.concat([binary,raw]);embedded.bufferViews.push({buffer:0,byteOffset:offset,byteLength:raw.length});embedded.images[i]={bufferView:embedded.bufferViews.length-1,mimeType:'image/png'};}
  embedded.buffers[0].byteLength=binary.length;binary=Buffer.concat([binary,Buffer.alloc((4-binary.length%4)%4)]);
  const j=Buffer.from(JSON.stringify(embedded)),jb=Buffer.concat([j,Buffer.alloc((4-j.length%4)%4,32)]),head=Buffer.alloc(12),jh=Buffer.alloc(8),bh=Buffer.alloc(8);head.write('glTF');head.writeUInt32LE(2,4);head.writeUInt32LE(12+8+jb.length+8+binary.length,8);jh.writeUInt32LE(jb.length);jh.writeUInt32LE(0x4e4f534a,4);bh.writeUInt32LE(binary.length);bh.writeUInt32LE(0x004e4942,4);fs.writeFileSync(path.join(dir,'material.glb'),Buffer.concat([head,jh,jb,bh,binary]));
}
function native(p,f){
  const density=p.properties.find(x=>x.quantity==='density');if(typeof density.value!=='number')throw Error('Point density required');
  const color=p.appearance_palette_linear.map(x=>Math.round(encode(x)*255));
  const properties=[{data:{kind:'density',kg_m3:density.value},source_id:p.source_id,conditions:{temperature_k:density.temperature_k,moisture_dry_basis_kg_kg:null,strain_rate_per_s:null,state:p.condition+'; reference only, not verified identity of a manufactured part'}}];
  return {scope:'Proposed existing-engine commands, NOT executed/native accepted. No automatic body assignment.',source_profile:p.id,commands:[{command:'material.create',params:{name:p.name+' / '+f.name,density_g_cm3:density.value/1000,color,opacity:1,pbr:{metallic:1,roughness:f.roughness,dielectric_ior:1.5},physical_card:{schema_version:1,designation:p.name,family:'metal',sources:[{id:p.source_id,title:p.name+' primary reference',kind:'public_reference',license:null,reference:load(path.join(A,'data/sources.json')).items.find(s=>s.id===p.source_id).url}],properties}}}],remaining_extended_properties:'Retained in physical-profile.json. No guessed Poisson ratio or constitutive tensor is exported.'};
}
function main(){
  const n=Number(process.env.ALLOY_SIZE||2048),out=path.resolve(process.env.ALLOY_OUTPUT||path.join(A,'build')),profiles=load(path.join(A,'data/physical-profiles.json')).profiles,finishes=load(path.join(A,'data/finishes.json')).finishes;let contracts=[],files=[],start=Date.now();
  for(const f of finishes){const big=fields(f,n),small=n>=2048?downsample(big):big,dir=path.join(out,'maps',f.id);const sets={};sets['master-'+n]=maps(big,path.join(dir,'master-'+n));if(n>=2048)sets['runtime-'+small.n]=maps(small,path.join(dir,'runtime-'+small.n));
    const info={finish_id:f.id,sets,patch_mm:[40,40],wrap:'clamp_to_edge',seamless:false,height_encoding:{offset_mm:-.05,range_mm:.1},metallic:1,ambient_occlusion:1,base_color_semantics:'sRGB texture is a linear modulation field multiplied by separately authored alloy RGB conductor palette; no baked lighting',normals:'OpenGL +U right +V image-up; DirectX green inverted',physical_surface_roughness_measurement:false};save(path.join(dir,'map-contract.json'),info);contracts.push(info);
    const mapDir=path.join(dir,(n>=2048?'runtime-':'master-')+small.n);
    for(const p of profiles){const id='alloy.'+p.id+'.'+f.id,folder=path.join(out,'materials',id);fs.mkdirSync(folder,{recursive:true});preview(p,f,small,path.join(folder,'preview.png'));gltf(p,f,folder,mapDir);save(path.join(folder,'physical-profile.json'),p);save(path.join(folder,'appearance.json'),{id,physical_profile_id:p.id,finish:f,map_contract:'../../maps/'+f.id+'/map-contract.json',base_color_linear:p.appearance_palette_linear,metallic:1,roughness_map:'../../maps/'+f.id+'/'+(n>=2048?'runtime-':'master-')+small.n+'/roughness.png',engineering_properties_changed:false,native_acceptance:'not_run'});save(path.join(folder,'native-material-commands.json'),native(p,f));files.push({id,name:p.name+' / '+f.name,family:p.family,physical_profile:p.id,path:'build/materials/'+id,preview:'build/materials/'+id+'/preview.png'});}
    console.log('ALLOY_FINISH',f.id,'profiles',profiles.length,'elapsed_s',Math.round((Date.now()-start)/1000));
  }
  save(path.join(out,'map-index.json'),{status:'generated_not_native_qualified',resolution:n,mapsets:contracts.length,contracts,variants:files.length,seconds:(Date.now()-start)/1000});save(path.join(out,'resource-index.json'),{plugin_standard:null,items:files});
}
if(require.main===module)main();module.exports={field,fields,normalAt,downsample,maps,preview,sphereGeometry,gltf,native};
