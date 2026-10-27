"""Bounded stdio MCP client for isolated, actual SolidCraft material qualification.

No app source changes, live document replacement, silent GPU fallback, or test bypass.
"""
from __future__ import annotations
import hashlib,json,os,pathlib,queue,subprocess,threading,time
class NativeMCP:
    def __init__(self,cli:pathlib.Path,workspace:pathlib.Path,*,gpu:bool=True,design:pathlib.Path|None=None):
        self.workspace=workspace.resolve();self.workspace.mkdir(parents=True,exist_ok=True)
        self.cli=cli.resolve();self.serial=0;self.lines=queue.Queue()
        with self.cli.open('rb') as binary:self.executable_sha256=hashlib.file_digest(binary,'sha256').hexdigest()
        self.stderr=(self.workspace/'mcp-stderr.log').open('ab')
        args=[str(self.cli),'mcp','--headless','--allow-path',str(self.workspace)]
        if gpu:args.append('--render-gpu')
        if design:args+=['--in',str(design.resolve())]
        env=dict(os.environ,SOLIDCRAFT_GPU='hardware',WGPU_BACKEND='vulkan')
        self.proc=subprocess.Popen(args,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=self.stderr,text=True,encoding='utf8',bufsize=1,env=env)
        def receive():
            for line in self.proc.stdout:self.lines.put(line)
            self.lines.put(None)
        threading.Thread(target=receive,daemon=True).start()
        try:
            self.server=self.request('initialize',{'protocolVersion':'2025-06-18','capabilities':{},'clientInfo':{'name':'catalog-native-qa','version':'1'}},timeout=600).get('serverInfo')
            self.request('notifications/initialized',notify=True)
        except BaseException:
            self.close()
            raise
    def request(self,method:str,params:dict|None=None,*,notify:bool=False,timeout:float=180):
        self.serial+=1;message={'jsonrpc':'2.0','method':method}
        if not notify:message['id']=self.serial
        if params is not None:message['params']=params
        self.proc.stdin.write(json.dumps(message,ensure_ascii=False)+'\n');self.proc.stdin.flush()
        if notify:return None
        until=time.monotonic()+timeout
        while time.monotonic()<until:
            try:line=self.lines.get(timeout=max(.1,until-time.monotonic()))
            except queue.Empty:raise TimeoutError(f'MCP {method} did not reply; do not repeat a mutation blindly')
            if line is None:raise RuntimeError(f'MCP exited with {self.proc.poll()}')
            reply=json.loads(line)
            if reply.get('id')==self.serial:
                if 'error' in reply:raise RuntimeError(f'MCP {method}: {reply["error"]}')
                return reply.get('result',{})
        raise TimeoutError('MCP response timeout')
    def tool(self,name:str,args:dict|None=None):
        result=self.request('tools/call',{'name':name,'arguments':args or {}})
        text=''.join(x.get('text','') for x in result.get('content',[]) if x.get('type')=='text')
        if result.get('isError'):raise RuntimeError(f'{name}: {text}')
        try:return json.loads(text)
        except ValueError:return text
    def execute(self,name:str,params:dict|None=None):return self.tool('execute',{'command':name,'params':params or {}})
    def render(self,params:dict,path:pathlib.Path,*,timeout:float=300):
        if path.exists():raise FileExistsError(path)
        before=time.monotonic();pre=self.execute('render.preflight',params)
        job=self.execute('render.start',params)['job'];last=None
        while time.monotonic()-before<timeout:
            status=self.execute('render.status',{'job':job});progress=status.get('progress',{})
            phase=progress.get('phase')
            if phase!=last:print('NATIVE_PHASE',path.name,phase,flush=True);last=phase
            if phase=='completed':break
            if phase in ('failed','cancelled'):raise RuntimeError(json.dumps(status))
            time.sleep(.3)
        else:
            self.execute('render.cancel',{'job':job})
            raise TimeoutError(f'Cancelled timed-out image {job}')
        export=self.execute('render.export',{'job':job,'path':str(path),'overwrite':False})
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        if digest!=status['frame']['png_sha256']:raise RuntimeError('Exported bytes do not match the completed job')
        return {'server':self.server,'request':params,'preflight':pre,'job':job,'export':export,'png_sha256':digest,'elapsed_s':round(time.monotonic()-before,3)}
    def close(self):
        try:self.proc.stdin.close();self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:self.proc.terminate();self.proc.wait(timeout=10)
        finally:self.stderr.close()
    def __enter__(self):return self
    def __exit__(self,*args):self.close()
