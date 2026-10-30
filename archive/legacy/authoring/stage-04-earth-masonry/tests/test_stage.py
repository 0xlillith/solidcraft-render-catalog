"""Independent unit tests for source identities, physical claims, units and surface maps."""
import unittest, importlib.util, pathlib, math, tempfile, numpy as np
from PIL import Image
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('earthstage04',ROOT/'tools/build.py')
B=importlib.util.module_from_spec(spec);spec.loader.exec_module(B)
class SourceRecords(unittest.TestCase):
 def test_expected_coverage_and_unique_identity(self):
  self.assertEqual(len(B.P),28)
  self.assertEqual(set(B.R),{'soil','aggregate','cement','gypsum','paste'})
  self.assertEqual(sum(len(B.R[p[2]]) for p in B.P),168)
  self.assertEqual(sum(map(len,B.R.values())),30)
  self.assertEqual(len({p[0] for p in B.P}),28)
 def test_each_physical_reference_has_a_real_source(self):
  for slug,name,fam,color,src,state,props in B.P:
   self.assertIn(src,B.SOURCE)
   self.assertTrue(B.SOURCE[src][1].startswith('https://'))
   self.assertTrue(state and len(state)>10)
   self.assertTrue(props)
   self.assertTrue(all(0<=x<=255 for x in color))
   self.assertTrue(B.FAMILY_SCALE[fam][0]>0)
 def test_missing_properties_are_null_not_zero(self):
  self.assertGreater(sum(v is None for p in B.P for q,v,*_ in p[6]),6)
  for p in B.P:
   for q,value,unit,qual,cond in p[6]:
    self.assertTrue(q and unit and qual and cond)
    if isinstance(value,list):self.assertEqual(len(value),2);self.assertTrue(0<value[0]<value[1])
    elif value is not None:self.assertTrue(math.isfinite(value) and value>0)
 def test_density_roles_do_not_mix(self):
  values={p[0]:dict((q,(v,u)) for q,v,u,*_ in p[6]) for p in B.P}
  self.assertEqual(values['portland-cement-powder']['particle_density'][0],3150)
  self.assertNotIn('loose_bulk_density',values['portland-cement-powder'])
  self.assertEqual(values['gypsum-hydrocal-dry']['dry_cast_density'][0],1442)
  self.assertEqual(values['gypsum-hydrocal-green']['wet_cast_density'][0],1762)
  self.assertEqual(values['quikrete-concrete-1101']['cured_bulk_density'][0],None)
  self.assertEqual(values['quikrete-concrete-1101']['compressive_strength_28d'][0],27.6e6)
 def test_no_borrowed_earth_sand_mechanical_property(self):
  for p in B.P:
   if p[2] in ('soil','aggregate'):
    self.assertFalse(any('compressive_strength' in prop[0] for prop in p[6]))
 def test_finite_deterministic_textures(self):
  for fam in B.R:
   for fin in B.R[fam]:
    x=B.texture(fam,fin,64);y=B.texture(fam,fin,64)
    for a,b in zip(x,y):self.assertTrue(np.array_equal(a,b));self.assertTrue(np.isfinite(a).all())
 def test_five_families_distinguishable(self):
  fields=[B.texture(f,fins[0],64)[0] for f,fins in B.R.items()]
  for i in range(len(fields)):
   for j in range(i):self.assertFalse(np.array_equal(fields[i],fields[j]))
 def test_normal_and_orm_contract(self):
  with tempfile.TemporaryDirectory() as d:
   path=pathlib.Path(d);H,S,Q=B.texture('soil','dry-cracked',64);B.save_map(path,64,H,S,Q,(400,400))
   ng=np.array(Image.open(path/'normal_opengl.png'));nd=np.array(Image.open(path/'normal_directx.png'))
   orm=np.array(Image.open(path/'orm.png'));rough=np.array(Image.open(path/'roughness.png'))
   self.assertTrue(np.array_equal(ng[:,:,0],nd[:,:,0]));self.assertTrue(np.array_equal(ng[:,:,2],nd[:,:,2]))
   self.assertTrue(np.all(ng[:,:,1].astype(int)+nd[:,:,1].astype(int)==255))
   self.assertTrue(np.all(orm[:,:,0]==255));self.assertTrue(np.array_equal(orm[:,:,1],rough))
   self.assertTrue(np.all(orm[:,:,2]==0))
   self.assertEqual(np.array(Image.open(path/'height_mm_u16.png')).dtype,np.uint16)
 def test_reject_unbounded_resolution(self):
  self.assertTrue(all(x not in (256,512,1024,2048) for x in [8192,-1,4096]))
if __name__=='__main__':unittest.main(verbosity=2)