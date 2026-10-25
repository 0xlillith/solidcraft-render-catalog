'use strict';
const fs=require('node:fs'),path=require('node:path');
const V=require(process.env.GLTF_VALIDATOR_MODULE||'gltf-validator');
const root=path.resolve(__dirname,'..'),build=path.join(root,'build');
function walk(p){return fs.readdirSync(p,{withFileTypes:true}).flatMap(e=>e.isDirectory()?walk(path.join(p,e.name)):[path.join(p,e.name)]);}
async function main(){
 const files=walk(path.join(build,'materials')).filter(f=>/\.(gltf|glb)$/.test(f)).sort();
 if(files.length!==476)throw Error('Expected all 476 opaque/closed-transmission glTF and GLB files');
 const results=[];
 for(const file of files){const r=await V.validateBytes(new Uint8Array(fs.readFileSync(file)),{uri:path.basename(file),maxIssues:1000,externalResourceFunction:uri=>{const p=path.resolve(path.dirname(file),decodeURIComponent(uri));if(!p.startsWith(build+path.sep)||!fs.statSync(p).isFile())throw Error('Resource escapes build');return Promise.resolve(new Uint8Array(fs.readFileSync(p)));}});results.push({file:path.relative(root,file).split(path.sep).join('/'),errors:r.issues.numErrors,warnings:r.issues.numWarnings,messages:r.issues.messages});}
 const report={validator:V.version(),files:files.length,errors:results.reduce((s,r)=>s+r.errors,0),warnings:results.reduce((s,r)=>s+r.warnings,0),results};fs.mkdirSync(path.join(root,'reports'),{recursive:true});fs.writeFileSync(path.join(root,'reports/gltf-validation.json'),JSON.stringify(report,null,2)+'\n');if(report.errors||report.warnings)throw Error('Portable validation failed');console.log('GLTF_PASS',files.length);
}
main().catch(e=>{console.error(e);process.exitCode=1});
