import pathlib,sys,unittest,numpy as np
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'tools'))
import clasts
class ClastContract(unittest.TestCase):
 def test_physical_layout_is_resolution_independent(self):
  for recipe in clasts.RECIPES:
   before=clasts.layout(recipe);clasts.fields(recipe,64);clasts.fields(recipe,128)
   self.assertEqual(before,clasts.layout(recipe))
   self.assertEqual(len(before),clasts.RECIPES[recipe]['grid']**2)
 def test_deterministic_finite_bounded_morphology(self):
  for recipe in clasts.RECIPES:
   a=clasts.fields(recipe,96);b=clasts.fields(recipe,96)
   for x,y in zip(a,b):self.assertTrue(np.array_equal(x,y));self.assertTrue(np.isfinite(x).all())
   self.assertLess(float(a[0].max()-a[0].min()),3)
   self.assertGreater(float((a[3]>.5).mean()),.18)
   self.assertLess(float((a[3]>.5).mean()),.85)
 def test_normals_orm_and_height_contracts(self):
  for recipe in clasts.RECIPES:
   maps,height,cov=clasts.encoded(recipe,128);ng=maps['normal_opengl'];nd=maps['normal_directx']
   self.assertTrue(np.array_equal(ng[:,:,(0,2)],nd[:,:,(0,2)]));self.assertTrue((ng[:,:,1].astype(int)+nd[:,:,1].astype(int)==255).all())
   self.assertLess(float(np.abs(np.linalg.norm(ng.astype(float)/127.5-1,axis=-1)-1).max()),.009)
   self.assertTrue(np.array_equal(maps['orm'][:,:,1],maps['roughness']))
   self.assertTrue((maps['orm'][:,:,2]==0).all());self.assertTrue((maps['orm'][:,:,0]==255).all())
   decoded=maps['height_mm_u16'].astype(float)/65535*16-8
   self.assertLess(float(np.abs(decoded-height).max()),16/65535)
 def test_no_unknown_recipe_or_unbounded_allocations(self):
  for size in (0,1,16,4096,1.5,True):
   with self.assertRaises(ValueError):clasts.fields('aggregate.exposed-stones',size)
  with self.assertRaises(ValueError):clasts.fields('measured-granite',128)
if __name__=='__main__':unittest.main()
