"""Independent resource edits must not rebuild packs or overwrite source bytes."""
import hashlib,importlib.util,json,pathlib,tempfile,unittest
import numpy as np
from PIL import Image
P=pathlib.Path(__file__).resolve().parents[2]/'improve.py'
spec=importlib.util.spec_from_file_location('single_extra_test',P);I=importlib.util.module_from_spec(spec);spec.loader.exec_module(I)
def put(p,o):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((json.dumps(o)+'\n').encode())
class SingleExtra(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=pathlib.Path(self.tmp.name);self.identity='wood.test.plain.raw';self.folder=self.root/'extras'/self.identity
  put(self.root/'extras/INDEX.json',{'items':[{'id':self.identity,'folder':self.identity}]})
  self.definition={'id':self.identity,'appearance':{'mapset':'test/plain','patch_mm':[100,250],'roughness_factor':1,'normal_scale':1,'color_multiplier_linear':[1,1,1],'clearcoat':0,'clearcoat_roughness':.4,'dielectric_ior':1.5}}
  put(self.folder/'definition.json',self.definition);files=[];self.source=self.folder/'files/build/maps/test/plain/runtime-1024';self.source.mkdir(parents=True)
  for role,a in [('base_color',np.full((8,8,3),188,np.uint8)),('normal_opengl',np.full((8,8,3),[128,128,255],np.uint8)),('roughness',np.full((8,8),180,np.uint8))]:
   p=self.source/(role+'.png');Image.fromarray(a).save(p);files.append({'path':p.relative_to(self.folder).as_posix(),'sha256':I.digest(p)})
  put(self.folder/'FILES.json',{'files':files})
 def tearDown(self):self.tmp.cleanup()
 def test_reads_edited_definition_not_stage(self):
  a=I.generate(self.identity,self.root/'raw',root=self.root)
  self.definition['appearance']['roughness_factor']=.22;put(self.folder/'definition.json',self.definition)
  b=I.generate(self.identity,self.root/'gloss',root=self.root)
  self.assertNotEqual(a['maps']['roughness']['sha256'],b['maps']['roughness']['sha256'])
  self.assertTrue((np.asarray(Image.open(self.root/'gloss/roughness.png'))==40).all())
 def test_does_not_overwrite(self):
  out=self.root/'out';I.generate(self.identity,out,root=self.root)
  with self.assertRaises(FileExistsError):I.generate(self.identity,out,root=self.root)
 def test_changed_original_refuses(self):
  (self.source/'base_color.png').write_bytes(b'modified')
  with self.assertRaises(ValueError):I.generate(self.identity,self.root/'out',root=self.root)
  self.assertFalse((self.root/'out').exists())
 def test_no_other_extra_or_global_data_changed(self):
  before=(self.folder/'definition.json').read_bytes();I.generate(self.identity,self.root/'out',root=self.root)
  self.assertEqual(before,(self.folder/'definition.json').read_bytes());self.assertFalse((self.root/'authoring').exists())
 def test_unknown_id_refuses(self):
  with self.assertRaises(ValueError):I.generate('../elsewhere',self.root/'out',root=self.root)
 def test_preview_requires_supported_kind(self):
  with self.assertRaises(ValueError):I.generate(self.identity,self.root/'out',root=self.root,metric_preview=True)
if __name__=='__main__':unittest.main()
