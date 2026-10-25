'use strict';
/** Original PNG writer and deterministic field utilities shared with the wood authoring work. */
const fs=require('node:fs'), path=require('node:path'), zlib=require('node:zlib'), crypto=require('node:crypto');
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
module.exports={png,crc32,sha,clamp,mix,decode,encode,noise};
