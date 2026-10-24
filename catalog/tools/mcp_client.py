"""Scoped local stdio client for the project's real headless renderer; no network."""
from core import *
import subprocess,threading,queue,time

class Client:
    def __init__(self,gpu=True):
        self.seq=0;self.q=queue.Queue();self.stderr=(ROOT/'reports/mcp-renderer.stderr.log').open('ab');self.transcript=(ROOT/'reports/mcp-renderer-transcript.jsonl').open('a',encoding='utf-8')
        args=[load(ROOT/'build.json')['native_cli'],'mcp','--headless','--allow-path',str(ROOT)]
        if gpu:args+=['--render-gpu']
        env=dict(os.environ,SOLIDCRAFT_CRASH_DIR=str(ROOT/'reports/native-crashes'))
        self.p=subprocess.Popen(args,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=self.stderr,text=True,encoding='utf-8',bufsize=1,env=env)
        def reader():
            for line in self.p.stdout:
                try:self.q.put(json.loads(line))
                except ValueError:self.q.put({'unparsed':line})
            self.q.put({'terminated':self.p.poll()})
        self.thread=threading.Thread(target=reader,daemon=True);self.thread.start()
        try:
            self.call('initialize',{'protocolVersion':'2025-03-26','capabilities':{},'clientInfo':{'name':'local-catalog-author','version':VERSION}},timeout=600 if gpu else 30)
        except Exception:
            self.p.terminate();self.p.wait(timeout=15);self.transcript.close();self.stderr.close();raise
        self.p.stdin.write(json.dumps({'jsonrpc':'2.0','method':'notifications/initialized'})+'\n');self.p.stdin.flush()
    def call(self,method,params,timeout=120):
        self.seq+=1;ident=self.seq;request={'jsonrpc':'2.0','id':ident,'method':method,'params':params};start=time.monotonic()
        self.p.stdin.write(json.dumps(request,allow_nan=False)+'\n');self.p.stdin.flush()
        while True:
            reply=self.q.get(timeout=max(.01,timeout-(time.monotonic()-start)))
            if 'terminated' in reply:raise RuntimeError('MCP process ended: '+str(reply))
            if reply.get('id')!=ident:continue
            self.transcript.write(json.dumps({'request':request,'reply':reply,'seconds':time.monotonic()-start},ensure_ascii=False)+'\n');self.transcript.flush()
            if reply.get('error'):raise RuntimeError(reply['error'])
            return reply.get('result')
    def execute(self,command,params=None):
        r=self.call('tools/call',{'name':'execute','arguments':{'command':command,'params':params or {}}})
        if r.get('isError'):raise RuntimeError(r)
        if 'structuredContent' in r:return r['structuredContent']
        content=r.get('content',[])
        for x in content:
            if x.get('type')=='text':
                try:return json.loads(x['text'])
                except ValueError:return x['text']
        return r
    def close(self):
        if self.p.stdin:self.p.stdin.close()
        self.p.wait(timeout=30);self.transcript.close();self.stderr.close()
    def __enter__(self):return self
    def __exit__(self,*args):self.close()

if __name__=='__main__':
    with Client() as c:
        print('BACKENDS',json.dumps(c.execute('render.backends')),flush=True)
        print('OPEN',json.dumps(c.execute('doc.open',{'path':str(ROOT/'materials/MAT-001/material.solidcraft')}))[:1000],flush=True)
        print('TARGETS',json.dumps(c.execute('render.library.targets')),flush=True)
