import copy,pathlib,sys,tempfile,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'tools'))
from native_matrix import batch_fingerprint
class ReceiptIdentity(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.path=pathlib.Path(self.tmp.name)/'map.png';self.path.write_bytes(b'original source bytes')
  self.rows=[{'id':'original.material','maps':{'base_color':str(self.path)},'color_srgb':[123,120,119],'dielectric_ior':1.5}]
 def tearDown(self):self.tmp.cleanup()
 def test_same_inputs_are_stable(self):self.assertEqual(batch_fingerprint(self.rows,16,'binary-A'),batch_fingerprint(copy.deepcopy(self.rows),16,'binary-A'))
 def test_sampling_or_executable_invalidates_old_result(self):
  old=batch_fingerprint(self.rows,16,'binary-A')
  self.assertNotEqual(old,batch_fingerprint(self.rows,64,'binary-A'));self.assertNotEqual(old,batch_fingerprint(self.rows,16,'binary-B'))
 def test_ior_coat_or_color_cannot_reuse_old_receipt(self):
  old=batch_fingerprint(self.rows,16,'binary-A')
  for key,value in [('dielectric_ior',1.41),('clearcoat',{'weight':.7}),('color_srgb',[200,190,180])]:
   rows=copy.deepcopy(self.rows);rows[0][key]=value;self.assertNotEqual(old,batch_fingerprint(rows,16,'binary-A'))
 def test_changed_map_bytes_invalidate_receipt(self):
  old=batch_fingerprint(self.rows,16,'binary-A');self.path.write_bytes(b'a revised source map')
  self.assertNotEqual(old,batch_fingerprint(self.rows,16,'binary-A'))
 def test_nonfinite_recipe_is_not_a_valid_cache_key(self):
  self.rows[0]['dielectric_ior']=float('nan')
  with self.assertRaises(ValueError):batch_fingerprint(self.rows,16,'binary-A')
if __name__=='__main__':unittest.main()
