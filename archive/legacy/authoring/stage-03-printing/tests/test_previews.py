import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import numpy as np
import render_previews as p
from build import enc,dec
class PreviewTests(unittest.TestCase):
 def test_texel_center_and_linear_average(self):
  a=np.array([[0.,1.],[2.,3.]],np.float32);u=np.array([[.25,.75,.5]]);v=np.array([[.25,.75,.5]])
  np.testing.assert_allclose(p.sample(a,u,v),[[0,3,1.5]])
 def test_finite_patch_clamps_not_wraps(self):
  a=np.array([[0.,1.],[2.,3.]],np.float32)
  np.testing.assert_allclose(p.sample(a,np.array([[-1.,2.]]),np.array([[-1.,2.]])),[[0,3]])
 def test_rgb_channels_share_weights(self):
  a=np.arange(12,dtype=np.float32).reshape(2,2,3)
  np.testing.assert_allclose(p.sample(a,np.array([[.5]]),np.array([[.5]]))[0,0],a.mean((0,1)))
 def test_linear_material_tint_does_not_tint_dielectric_specular(self):
  d=np.ones((2,2,3),np.float32)*.3;s=np.ones((2,2),np.float32)*.2;c=np.ones((2,2),np.float32)
  black=p.finish({'appearance_palette_srgb':[0,0,0]},(d,s,c));expected=round(float(enc(.2/1.2))*255)
  self.assertTrue(np.all(black==expected))
 def test_background_is_not_material_tint(self):
  d=np.zeros((2,2,3),np.float32);s=np.zeros((2,2),np.float32);c=np.zeros((2,2),np.float32)
  np.testing.assert_array_equal(p.finish({'appearance_palette_srgb':[255,0,0]},(d,s,c)),p.finish({'appearance_palette_srgb':[0,255,255]},(d,s,c)))
if __name__=='__main__':unittest.main(verbosity=2)
