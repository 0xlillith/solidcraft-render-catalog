'use strict';
const fs=require('node:fs'),path=require('node:path');
const validator=require(process.env.GLTF_VALIDATOR_MODULE||'gltf-validator');
const ROOT=path.resolve(__dirname,'..'),folder=path.join(ROOT,'build','materials');
async function main(){
 let count=0,issues=[];
 for(const dirName of fs.readdirSync(folder)){
  const dir=path.join(folder,dirName);
  if(!fs.statSync(dir).isDirectory())continue;
  for(const name of ['material.glb','material.gltf']){
   const b=fs.readFileSync(path.join(dir,name));
   const result=await validator.validateBytes(new Uint8Array(b),{
    uri:name,maxIssues:200,
    externalResourceFunction:async u=>new Uint8Array(fs.readFileSync(path.resolve(dir,decodeURIComponent(u))))
   });
   const errors=result.issues.numErrors||0,warnings=result.issues.numWarnings||0;
   if(errors||warnings)issues.push({name:dirName+'/'+name,errors,warnings,detail:result.issues.messages?.slice(0,4)});
   count++;
  }
 }
 const result={validated:count,errors:issues};
 fs.mkdirSync(path.join(ROOT,'reports'),{recursive:true});
 fs.writeFileSync(path.join(ROOT,'reports','gltf-validation.json'),JSON.stringify(result,null,2)+'\n');
 if(count!==308||issues.length){console.error(JSON.stringify(result).slice(0,6000));process.exitCode=1;}
 else console.log("OFFICIAL_GLTF_PASS",count);
}
main().catch(e=>{console.error(e);process.exitCode=1;});
