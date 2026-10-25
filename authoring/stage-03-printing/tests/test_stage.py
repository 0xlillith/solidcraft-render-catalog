"""Numerical/data tests independent of the generated catalog counts alone."""
import unittest,sys,math,tempfile,json,struct
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import numpy as np
from PIL import Image
import data,build
class DataTests(unittest.TestCase):
 def setUp(self):self.pp,self.rr,self.vv=data.records()
 def test_unique_linked_identity(self):
  self.assertEqual((len(self.pp),len(self.rr),len(self.vv)),(11,73,280))
  for rows in [self.pp,self.rr,self.vv]:self.assertEqual(len(rows),len({r['id'] for r in rows}))
  ps={p['id'] for p in self.pp};rs={r['id'] for r in self.rr}
  for v in self.vv:self.assertIn(v['profile_id'],ps);self.assertIn(v['process_id'],rs)
 def test_every_variant_has_physical_and_visual_record(self):
  for v in self.vv:
   self.assertEqual(len(v['visual_parameters']['base_color_srgb']),3);self.assertFalse(v['engineering_assignment']);self.assertIsNone(v['effective_printed_density_kg_m3'])
  for p in self.pp:self.assertTrue(any(x['quantity']=='material_density' for x in p['properties']));self.assertIsNone(p['full_mechanical_model'])
 def test_source_units_and_conversions(self):
  for p in self.pp:
   for x in p['properties']:
    self.assertEqual(x['source_id'],p['source']['id']);self.assertTrue(math.isfinite(x['value']));self.assertAlmostEqual(x['value'],x['source_value']*x['conversion']['scale']+x['conversion']['offset'],places=6)
    if x['quantity']=='material_density':self.assertAlmostEqual(x['value'],x['source_value']*1000)
 def test_mechanical_context_not_visual_recipe(self):
  for p in self.pp:
   c=p['specimen_context'];self.assertEqual(c['layer_height_mm'],.2);self.assertEqual(c['infill_percent'],100);self.assertEqual(c['perimeters'],2)
   self.assertTrue(c['not_a_general_slicing_profile'])
  self.assertTrue(any(v['name'].endswith('0.08 mm') for v in self.vv))
 def test_orientation_not_automatically_build_z(self):
  for p in self.pp:
   labels={v['conditions'].get('orientation_as_reported') for v in p['properties']}
   self.assertTrue(labels<={None,'Horizontal','Vertical xz'})
 def test_tpu_not_generic_young_modulus(self):
  p=next(x for x in self.pp if x['key']=='tpu-95a');q={x['quantity']:x for x in p['properties']}
  self.assertNotIn('tensile_modulus',q);self.assertEqual(q['stress_at_100_percent_elongation']['value'],8.9e6);self.assertEqual(q['hardness_shore_a']['value'],92)
  self.assertTrue(p['excluded_source_rows']);self.assertNotIn(7264,[x['source_value'] for x in p['properties']])
 def test_hdt_loads_and_vicat_remain_distinct(self):
  for p in self.pp:
   for x in p['properties']:
    if x['quantity']=='heat_deflection_temperature':self.assertIn(x['conditions']['bending_stress_pa'],[450000,1800000]);self.assertGreater(x['value'],273.15)
  p=next(x for x in self.pp if x['key']=='tpu-95a');self.assertEqual(sum(x['quantity']=='vicat_softening_temperature' for x in p['properties']),1)
 def test_composite_fine_layers_not_enabled(self):
  for r in self.rr:
   if r['group']!='smooth':self.assertGreaterEqual(r['layer_height_mm'],.16)
 def test_smoothing_has_explicit_material_scope(self):
  ids=[v['profile_id'].split('.')[-1] for v in self.vv if v['process_id'].endswith('smoothed-wall')]
  self.assertEqual(sorted(ids),['asa','pvb'])
class FieldTests(unittest.TestCase):
 def setUp(self):self.r=data.process_recipes()[0]
 def test_invalid_input_before_allocation(self):
  for n in [True,0,16,33,2049,4096,math.inf,float('nan')]:
   with self.assertRaises(ValueError):build.fields(self.r,n)
  for key,value in [('layer_height_mm',-1),('extrusion_width_mm',float('nan')),('pattern','bad'),('nozzle_diameter_mm',True),('patch_mm',[1e99,1e99])]:
   with self.assertRaises(ValueError):build.fields({**self.r,key:value},32)
 def test_finite_metric_fields_all_recipes(self):
  for r in data.process_recipes():
   f=build.fields(r,32)
   for k in ('height','tone','rough'):self.assertEqual(f[k].shape,(32,32));self.assertTrue(np.isfinite(f[k]).all())
   self.assertLess(np.max(np.abs(f['height'])),.25)
 def test_layer_period_is_physical(self):
  # Wall bead term isolated from the explicitly authored micro field.
  for height in [.08,.12,.16,.20,.28]:
   r={**self.r,'layer_height_mm':height};x=np.full(100,.5);y=np.linspace(.01,1,100)
   def bead(y):return build.field_at(x,y,r)[0]-.0007*build.wave(x*2.5,y*2.5)
   self.assertLess(np.max(np.abs(bead(y+height)-bead(y))),1e-7)
 def test_deterministic_fields(self):
  a=build.fields(self.r,64);b=build.fields(self.r,64)
  for k in ('height','tone','rough'):np.testing.assert_array_equal(a[k],b[k])
 def test_linear_downsample(self):
  f=build.fields(self.r,64);small=build.smaller(f)
  for k in ('height','tone','rough'):self.assertAlmostEqual(float(small[k][0,0]),float(f[k][:2,:2].mean()),places=6)
 def test_known_plane_normal(self):
  n=64;u=(np.arange(n)[None,:]+.5)/n;v=1-(np.arange(n)[:,None]+.5)/n;z=.02*u+.04*v
  N=build.normals(z,[1,1]);expected=np.array([-.02,-.04,1]);expected/=np.linalg.norm(expected)
  np.testing.assert_allclose(N,np.broadcast_to(expected,N.shape),atol=1e-7)
 def test_srgb_roundtrip(self):
  a=np.array([0,.001,.0031308,.1,.5,1]);np.testing.assert_allclose(build.dec(build.enc(a)),a,atol=1e-7)
 def test_footprint_resolves_finest_layer(self):
  self.assertGreaterEqual(.08/(12.8/1024),6)
 def test_geometry_winding_and_tangent_basis(self):
  pos,norm,uv,tan,idx=build.material_geometry();p=np.array(pos);N=np.array(norm);T=np.array(tan)
  for a,b,c in np.array(idx).reshape(-1,3):
   self.assertGreater(np.dot(np.cross(p[b]-p[a],p[c]-p[a]),N[a]),0)
  np.testing.assert_allclose(np.sum(N*T[:,:3],axis=1),0,atol=1e-7)
  # The plane maps downward UV to -Z: increasing-v bitangent is -Z.
  np.testing.assert_allclose(np.cross(N[0],T[0,:3])*T[0,3],[0,0,-1],atol=1e-7)
 def test_map_encoding_and_exr(self):
  f=build.fields(self.r,64)
  # map_export requires outputs inside the authoring root for manifest paths.
  with tempfile.TemporaryDirectory(dir=data.ROOT) as td:
   d=Path(td);m=build.map_export(f,d);N=np.array(Image.open(d/'normal_opengl.png'));D=np.array(Image.open(d/'normal_directx.png'));H=np.array(Image.open(d/'height_mm_u16.png'));O=np.array(Image.open(d/'orm.png'));R=np.array(Image.open(d/'roughness.png'))
   self.assertTrue(np.all(N[:,:,1].astype(int)+D[:,:,1]==255));np.testing.assert_array_equal(O[:,:,1],R);self.assertTrue(np.all(O[:,:,0]==255));self.assertTrue(np.all(O[:,:,2]==0))
   self.assertLess(np.max(np.abs(H/65535*.5-.25-f['height'])),.5/65535)
   exr=build.cv2.imread(str(d/'height_mm.exr'),build.cv2.IMREAD_UNCHANGED);np.testing.assert_array_equal(exr,f['height'])
if __name__=='__main__':unittest.main(verbosity=2)
