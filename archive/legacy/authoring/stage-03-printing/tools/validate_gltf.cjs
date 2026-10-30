'use strict';
// Official validator with strictly local external-resource resolution.
const fs=require('node:fs'),path=require('node:path');
const validator=require(process.env.GLTF_VALIDATOR_MODULE||'gltf-validator');
const root=path.resolve(__dirname,'..'),build=path.join(root,'build');
function files(dir){return fs.readdirSync(dir,{withFileTypes:true}).flatMap(e=>e.isDirectory()?files(path.join(dir,e.name)):[path.join(dir,e.name)]);}
async function main(){
 const inputs=files(path.join(build,'materials')).filter(f=>/\.(gltf|glb)$/.test(f)).sort(),results=[];
 if(inputs.length!==560)throw Error('Full 560-file portable collection required');
 for(const file of inputs){
  const r=await validator.validateBytes(new Uint8Array(fs.readFileSync(file)),{uri:path.basename(file),maxIssues:1000,externalResourceFunction:uri=>{
   const resolved=path.resolve(path.dirname(file),decodeURIComponent(uri));
   if(!resolved.startsWith(build+path.sep)||!fs.statSync(resolved).isFile())throw Error('External resource outside build');
   return Promise.resolve(new Uint8Array(fs.readFileSync(resolved)));
  }});
  results.push({file:path.relative(root,file).split(path.sep).join('/'),errors:r.issues.numErrors,warnings:r.issues.numWarnings,messages:r.issues.messages});
 }
 const report={validator:validator.version(),files:results.length,errors:results.reduce((n,r)=>n+r.errors,0),warnings:results.reduce((n,r)=>n+r.warnings,0),results};
 fs.mkdirSync(path.join(root,'reports'),{recursive:true});fs.writeFileSync(path.join(root,'reports/gltf-validation.json'),JSON.stringify(report,null,2)+'\n');
 if(report.errors||report.warnings)throw Error('glTF validation failed: '+report.errors+' errors / '+report.warnings+' warnings');
 console.log('OFFICIAL_GLTF_PASS',report.files);
}
main().catch(e=>{console.error(e);process.exitCode=1});
