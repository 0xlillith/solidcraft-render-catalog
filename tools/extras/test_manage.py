"""Offline regression tests for the folder-authoring/restoration boundary."""
from pathlib import Path
import copy, hashlib, importlib.util, json, tempfile, unittest, zipfile
spec=importlib.util.spec_from_file_location('extras_manage',Path(__file__).with_name('manage.py'))
manage=importlib.util.module_from_spec(spec);spec.loader.exec_module(manage)

def put(path,obj):
 path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(obj),encoding='utf-8')

class WorkspaceTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)/'extras';self.cache=Path(self.temp.name)/'cache';self.cache.mkdir()
  self.data=b'original independent specimen bytes'
  archive=self.cache/'historical.zip'
  with zipfile.ZipFile(archive,'w') as z:z.writestr('source/specimen.dat',self.data)
  self.source={'archive':archive.name,'sha256':manage.sha(archive),'bytes':archive.stat().st_size,'url':'https://github.com/0xlillith/solidcraft-render-catalog/releases/download/history/historical.zip'}
  put(self.root/'ARCHIVE-SOURCES.json',{'archives':[self.source]})
  put(self.root/'INDEX.json',{'count':1,'items':[{'id':'test.extra','folder':'test.extra'}]})
  self.folder=self.root/'test.extra'
  put(self.folder/'definition.json',{'id':'test.extra','property':None,'qualification':'not_run'})
  put(self.folder/'extra.json',{'id':'test.extra','source_id':'test.extra','depends_on':[],'packaging_decision':None,'entrypoints':[],'previews':[]})
  self.file={'path':'files/specimen.dat','archive':'historical.zip','member':'source/specimen.dat','sha256':hashlib.sha256(self.data).hexdigest(),'bytes':len(self.data)}
  put(self.folder/'FILES.json',{'files':[self.file]})
 def tearDown(self):self.temp.cleanup()
 def test_valid_directory_contract(self):self.assertEqual(manage.validate(self.root)['extras'],1)
 def test_unknown_resource_refuses(self):
  with self.assertRaises(ValueError):manage.entries(['missing'],self.root)
 def test_path_escape_refuses(self):
  for value in ['../elsewhere','/absolute','C:/drive','some\\windows','nested/../../outside']:
   with self.subTest(value=value),self.assertRaises(ValueError):manage.confined(self.root,value)
 def test_unresolved_physical_identity_refuses(self):
  m=manage.read_json(self.folder/'extra.json');m['depends_on']=['missing.physical'];put(self.folder/'extra.json',m)
  with self.assertRaises(ValueError):manage.validate(self.root)
 def test_missing_files_are_not_claimed_complete(self):
  result=manage.verify(root=self.root);self.assertEqual(result['status'],'DIFFERENCES');self.assertEqual(len(result['missing']),1)
 def test_restore_is_create_only_and_idempotent(self):
  first=manage.restore([], [self.cache],False,self.root);second=manage.restore([], [self.cache],False,self.root)
  self.assertEqual(first['copied'],1);self.assertEqual(second['already_identical'],1)
  self.assertEqual(manage.verify(root=self.root)['status'],'PASS')
 def test_modified_work_survives_restore(self):
  manage.restore([], [self.cache],False,self.root);target=self.folder/self.file['path'];target.write_bytes(b'hand-authored improvement')
  with self.assertRaises(FileExistsError):manage.restore([], [self.cache],False,self.root)
  self.assertEqual(target.read_bytes(),b'hand-authored improvement')
  self.assertEqual(len(manage.verify(root=self.root)['changed']),1)
 def test_archive_corruption_is_not_trusted(self):
  with (self.cache/'historical.zip').open('ab') as f:f.write(b'bad trailer')
  with self.assertRaises(ValueError):manage.restore([], [self.cache],False,self.root)
 def test_member_hash_is_verified(self):
  bad=copy.deepcopy(self.file);bad['sha256']='0'*64;put(self.folder/'FILES.json',{'files':[bad]})
  with self.assertRaises(ValueError):manage.restore([], [self.cache],False,self.root)
  self.assertFalse((self.folder/self.file['path']).exists())
 def test_definition_and_reference_qualifiers_survive(self):
  before=(self.folder/'definition.json').read_bytes();manage.restore([], [self.cache],False,self.root)
  self.assertEqual(before,(self.folder/'definition.json').read_bytes())
  self.assertIsNone(manage.read_json(self.folder/'definition.json')['property'])
 def test_bad_json_is_rejected(self):
  (self.folder/'definition.json').write_text('{"id":"test.extra","density":NaN}',encoding='utf-8')
  with self.assertRaises(ValueError):manage.validate(self.root)
 def test_independent_files_are_not_hardlinked(self):
  manage.restore([], [self.cache],False,self.root)
  self.assertEqual((self.folder/self.file['path']).stat().st_nlink,1)

if __name__=='__main__':unittest.main(verbosity=2)
