'use strict';
const fs=require('node:fs'),path=require('node:path');
const validator=require(process.env.GLTF_VALIDATOR_MODULE||'gltf-validator');
const root=path.resolve(__dirname,'..'),folder=path.join(root,'build','materials');
async function main(){
 const issues=[];let count=0;
 for(const slug of fs.readdirSync(folder)){
  const dir=path.join(folder,slug);
  if(!fs.statSync(dir).isDirectory())continue;
  for(const name of ['material.glb','material.gltf']){
   const bytes=fs.readFileSync(path.join(dir,name));
   const out=await validator.validateBytes(new Uint8Array(bytes),{
    uri:name,maxIssues:300,externalResourceFunction:async url=>new Uint8Array(fs.readFileSync(path.resolve(dir,decodeURIComponent(url))))
   });
   const errors=out.issues.numErrors||0,warnings=out.issues.numWarnings||0;
   if(errors||warnings)issues.push({slug,name,errors,warnings,messages:out.issues.messages?.slice(0,8)});
   count++;
  }
 }
 const report={count,errors:issues.reduce((s,x)=>s+x.errors,0),
 warnings:issues.reduce((s,x)=>s+x.warnings,0),issues};
 fs.mkdirSync(path.join(root,'reports'),{recursive:true});
 fs.writeFileSync(path.join(root,'reports','gltf-validation.json'),JSON.stringify(report,null,2)+'\n');
 if(count!==16||issues.length){console.error(JSON.stringify(report).slice(0,6000));process.exitCode=1;}
 else console.log("OFFICIAL_GLTF_PASS",count);
}main().catch(err=>{console.error(err);process.exitCode=1});
