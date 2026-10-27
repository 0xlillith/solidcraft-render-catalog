"""Independent analytic planes catch swapped axes and missing mm-per-texel scaling."""
import importlib.util,pathlib,unittest,numpy as np
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('metric_preview_builder',ROOT/'tools/build.py')
B=importlib.util.module_from_spec(spec);spec.loader.exec_module(B)
class MetricPreview(unittest.TestCase):
 def plane(self,n,width=120,height=240):
  y,x=np.mgrid[0:n,0:n]
  return (.1*(x+.5)*width/n+.2*(y+.5)*height/n).astype(np.float32)
 def test_metric_slope_and_normal_sign(self):
  n=B.preview_normals(self.plane(128),(120,240),64)
  expected=np.array([-.1,.2,1]);expected/=np.linalg.norm(expected)
  np.testing.assert_allclose(n[2:-2,2:-2],np.broadcast_to(expected,(60,60,3)),atol=1e-5)
 def test_resolution_is_not_physical_relief(self):
  a=B.preview_normals(self.plane(128),(120,240),64)
  b=B.preview_normals(self.plane(256),(120,240),64)
  np.testing.assert_allclose(a[2:-2,2:-2],b[2:-2,2:-2],atol=1e-5)
 def test_double_patch_size_halves_slopes(self):
  a=B.preview_normals(self.plane(128),(240,480),64)
  expected=np.array([-.05,.1,1]);expected/=np.linalg.norm(expected)
  np.testing.assert_allclose(a[2:-2,2:-2],np.broadcast_to(expected,(60,60,3)),atol=1e-5)
 def test_flat_field_and_bad_inputs(self):
  a=B.preview_normals(np.zeros((16,16)),(40,40),16)
  np.testing.assert_array_equal(a,np.broadcast_to([0,0,1],(16,16,3)))
  for scale in [(0,1),(-1,2),(float('nan'),2),(1,)]:
   with self.assertRaises(ValueError):B.preview_normals(self.plane(16),scale,16)
  with self.assertRaises(ValueError):B.preview_normals(np.full((2,2),np.nan),(1,1),16)
if __name__=='__main__':unittest.main()
