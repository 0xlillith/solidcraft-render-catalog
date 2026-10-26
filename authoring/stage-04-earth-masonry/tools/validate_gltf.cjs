'use strict';
const fs=require('node:fs'),path=require('node:path');
const GV=require(process.env.GLTF_VALIDATOR_MODULE||'gltf-validator');
const root=path.resolve(__dirname,'..','build','materials');
async function main(){let total=0,errors=[];for(const folder of fs.readdirSync(root)){
 const dir=path.join(root,folder);if(!fs.statSync(dir).isDirectory())continue;
 for(const name of ['material.glb','material.gltf']){
  const file=path.join(dir,name),bytes=fs.readFileSync(file);
  const result=await GV.validateBytes(new Uint8Array(bytes),{uri:name,maxIssues:1000,externalResourceFunction:async uri=>new Uint8Array(fs.readFileSync(path.resolve(dir,decodeURIComponent(uri))))});
  const e=result.issues.numErrors||0,w=result.issues.numWarnings||0;
  if(e||w) errors.push({file,errors:e,warnings:w,messages:result.issues.messages?.slice(0,5)});
  total++;
 }
}const output={validated:total,errors};fs.writeFileSync(path.resolve(root,'..','..','reports','gltf-validation.json'),JSON.stringify(output,null,2)+'\n');
if(total!==336||errors.length){console.error(JSON.stringify(output).slice(0,4000));process.exitCode=1;}else console.log('OFFICIAL_GLTF_PASS',total);
}main().catch(e=>{console.error(e);process.exitCode=1});