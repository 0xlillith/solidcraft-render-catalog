'use strict';
// Offline official Khronos validator. No network callback, script hooks, or file writes in assets.
const fs=require('fs'),path=require('path');
const validator=require('./validator/package');
(async()=>{
 const root=path.resolve(process.argv[2]);
 const files=process.argv.slice(3);
 const results=[];
 for (const file of files){
  const full=path.resolve(root,file);if(!full.startsWith(root+path.sep))throw Error('path escape');
  const bytes=fs.readFileSync(full);
  const report=await validator.validateBytes(new Uint8Array(bytes),{uri:path.basename(full),maxIssues:100,externalResourceFunction:uri=>{
    const target=path.resolve(path.dirname(full),decodeURIComponent(uri));if(!target.startsWith(root+path.sep))return Promise.reject(Error('URI escape'));
    return Promise.resolve(new Uint8Array(fs.readFileSync(target)));
  }});
  const entry={file,errors:report.issues.numErrors,warnings:report.issues.numWarnings,info:report.issues.numInfos,messages:report.issues.messages};
  results.push(entry);
 }
 console.log(JSON.stringify({validator:validator.version(),results}));
 if(results.some(x=>x.errors))process.exitCode=1;
})().catch(e=>{console.error(e.stack);process.exitCode=2;});
