import pathlib,sys,unittest
import numpy as np
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'tools'))
import channels as C
class ChannelContract(unittest.TestCase):
 def test_srgb_average_is_linear_not_encoded(self):
  a=np.array([[[0,0,0],[255,255,255]],[[255,255,255],[0,0,0]]],np.uint8)
  self.assertTrue(np.all(C.albedo(a,size=1)==188))
 def test_color_transform_applied_once_in_linear_space(self):
  a=np.full((2,2,3),188,np.uint8)
  out=C.albedo(a,multiplier=(.5,.5,.5))
  self.assertTrue(np.all(out==137))
 def test_flat_normals_survive_filtering(self):
  a=np.full((8,8,3),[128,128,255],np.uint8)
  self.assertTrue(np.array_equal(C.normals(a,size=4),a[:4,:4]))
 def test_smoothing_reduces_tangent_slope_and_renormalizes(self):
  a=np.full((2,2,3),[204,128,230],np.uint8)
  strong=C.normals(a);smooth=C.normals(a,strength=.15)
  self.assertLess(abs(float(smooth[0,0,0])-127.5),abs(float(strong[0,0,0])-127.5))
  self.assertTrue(np.max(np.abs(np.linalg.norm(smooth.astype(float)/127.5-1,axis=-1)-1))<.009)
 def test_finish_roughness_not_only_a_preview_multiplier(self):
  a=np.full((3,3),180,np.uint8)
  self.assertTrue(np.all(C.roughness(a,factor=.22)==40))
  self.assertTrue(np.all(C.roughness(a,factor=1)==180))
 def test_orm_uses_linear_green_and_no_fake_ao(self):
  r=np.array([[15,65],[180,230]],np.uint8);o=C.orm(r)
  self.assertTrue(np.array_equal(o[:,:,1],r));self.assertTrue((o[:,:,0]==255).all());self.assertTrue((o[:,:,2]==0).all())
 def test_baked_variant_retains_original_input_bytes(self):
  b=np.full((4,4,3),200,np.uint8);n=np.full((4,4,3),[128,128,255],np.uint8);r=np.full((4,4),180,np.uint8)
  originals=[x.copy() for x in (b,n,r)]
  maps,coat=C.materialize(b,n,r,{'color_multiplier_linear':[.88,.83,.75],'roughness_factor':.22,'normal_scale':.15,'clearcoat':1,'clearcoat_roughness':.075})
  for a,copy in zip((b,n,r),originals):self.assertTrue(np.array_equal(a,copy))
  self.assertEqual(coat['weight'],1);self.assertEqual(coat['roughness'],.075)
  self.assertTrue(np.all(maps['normal_opengl'][:,:,1].astype(int)+maps['normal_directx'][:,:,1].astype(int)==255))
 def test_no_automatic_upscale_or_oversized_native_map(self):
  a=np.full((8,8,3),128,np.uint8)
  for bad in (0,-1,16,2048,True,3.5):
   with self.assertRaises(ValueError):C.albedo(a,size=bad)
 def test_invalid_ranges_are_refused(self):
  a=np.full((8,8,3),128,np.uint8)
  for mul in ([float('nan'),1,1],[2,1,1],[-.2,1,1],[1,1]):
   with self.assertRaises(ValueError):C.albedo(a,multiplier=mul)
  with self.assertRaises(ValueError):C.normals(a,strength=2)
  with self.assertRaises(ValueError):C.roughness(a)
if __name__=='__main__':unittest.main()
