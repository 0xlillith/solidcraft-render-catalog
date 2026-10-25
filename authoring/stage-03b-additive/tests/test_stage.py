import sys,unittest,tempfile,copy,math,json,struct
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import inputs as D, build as B
class Data(unittest.TestCase):
 def setUp(self):self.ps=D.records();self.rs=D.recipes();self.vs=D.variants(self.ps,self.rs)
 def test_complete_categories(self):
  self.assertEqual(len(self.ps),24);self.assertEqual(len(self.vs),198);self.assertEqual(len(self.rs),50)
  self.assertEqual({p['family'] for p in self.ps},{'fff','vat','powder-polymer','metal-am'})
  self.assertEqual({p['brand'] for p in self.ps if p['family']=='fff'},{'Bambu Lab','Polymaker','UltiMaker'})
  self.assertTrue({'SLA','SLS','MJF','LPBF','bound-metal','FFF'} <= {p['manufacturing_process'] for p in self.ps})
 def test_source_links(self):
  for p in self.ps:
   self.assertIn(p['source_id'],D.SOURCES);self.assertGreaterEqual(len(p['properties']),6)
   for v in p['properties']:self.assertIn(v['source_id'],D.SOURCES);self.assertTrue(v['source_locator']);self.assertTrue(v['conditions']['state'])
 def test_every_appearance_has_physical_and_visual(self):
  pp={p['id'] for p in self.ps};rr={r['id'] for r in self.rs};self.assertEqual(len({v['id'] for v in self.vs}),198)
  for v in self.vs:self.assertIn(v['physical_profile_id'],pp);self.assertIn(v['recipe_id'],rr);self.assertTrue(v['source_condition_not_replaced_by_visual_recipe'])
 def test_source_conversion(self):
  for p in self.ps:
   for v in p['properties']:
    o=v['original'];self.assertTrue(math.isfinite(v['value']));self.assertAlmostEqual(v['value'],o['value']*o['scale_to_si']+o['offset_to_si'])
 def test_thermal_cures_not_collapsed(self):
  ps=[p for p in self.ps if 'high-temp' in p['id']]
  for p in ps:
   for v in p['properties']:
    if v['quantity']=='hdt':self.assertNotEqual(v['conditions']['state'],p['condition']);self.assertIn('120 min at 80',v['conditions']['state'])
 def test_no_borrowed_density(self):
  for p in self.ps:
   if 'markforged' in p['id']:self.assertEqual([x['quantity'] for x in p['properties'] if 'density' in x['quantity']],['relative_density'])
   if 'eos.316l' in p['id'] or 'eos.in718' in p['id']:
    self.assertEqual(next(x for x in p['properties'] if x['quantity']=='part_density')['qualifier'],'lower_bound')
 def test_liquid_and_powder_density_are_separate(self):
  hp=next(p for p in self.ps if p['id']=='am.hp.tpu01.balanced');d={v['quantity']:v['value'] for v in hp['properties']}
  self.assertEqual(d['printed_part_density'],1110);self.assertEqual(d['loose_powder_bulk_density'],500)
  tough=next(p for p in self.ps if 'tough2000' in p['id']);self.assertEqual({v['value'] for v in tough['properties'] if 'density' in v['quantity']},{1090,1030})
 def test_elastomer_stress_not_modulus(self):
  for p in self.ps:
   if 'flex80' in p['id'] or 'elastic.v1' in p['id']:self.assertNotIn('tensile_modulus',[v['quantity'] for v in p['properties']])
 def test_no_silent_source_corrections(self):
  p=next(p for p in self.ps if 'polymaker' in p['id']);self.assertFalse(any(v['quantity']=='tensile_strength' and v['conditions']['orientation']=='X-Y' for v in p['properties']));self.assertGreaterEqual(len(D.AUDIT),9)
 def test_metal_process_layers_match(self):
  pp={p['id']:p for p in self.ps};rr={r['id']:r for r in self.rs}
  for v in self.vs:
   p=pp[v['physical_profile_id']];r=rr[v['recipe_id']]
   if p['manufacturing_process']=='LPBF' and r['layer_mm']:self.assertEqual(p['source_layer_mm'],r['layer_mm'])
class Fields(unittest.TestCase):
 def test_repeatability(self):
  r=D.recipes()[0];np.testing.assert_array_equal(B.fields(r,64)['height'],B.fields(r,64)['height'])
 def test_bounds_and_different_families(self):
  signatures=set()
  for r in D.recipes():
   f=B.fields(r,32);self.assertTrue(np.isfinite(f['height']).all());self.assertLess(abs(f['height']).max(),.25);self.assertTrue(((f['rough']>=.045)&(f['rough']<=.95)).all());signatures.add(f['height'].tobytes())
  self.assertEqual(len(signatures),50)
 def test_bad_input(self):
  for n in [0,16,33,4096,True,float('nan')]:
   with self.assertRaises(ValueError):B.fields(D.recipes()[0],n)
  r=copy.deepcopy(D.recipes()[0]);r['layer_mm']=-1
  with self.assertRaises(ValueError):B.fields(r,32)
 def test_downsample_linear(self):
  f=B.fields(D.recipes()[0],64);s=B.smaller(f)
  for k in ['height','tone','rough']:self.assertAlmostEqual(float(s[k][0,0]),float(f[k][:2,:2].mean()),places=6)
 def test_known_plane_normals(self):
  y,x=np.mgrid[:32,:32];z=.02*x/32+.04*(1-y/32);n=B.normals(z,[1,1]);np.testing.assert_allclose(n,B.unit(np.array([-.02,-.04,1]))[None,None,:]+np.zeros_like(n),atol=1e-6)
 def test_metric_layer_period(self):
  r=D.recipes()[0];f=B.fields(r,1024);a=f['height'][:,500];self.assertLess(np.mean(abs(a[64:]-a[:-64])),.002)
 def test_srgb(self):
  a=np.array([0,.001,.0031308,.1,.8,1]);np.testing.assert_allclose(B.dec(B.enc(a)),a,atol=1e-8)
 def test_geometry_winding_tangents(self):
  for closed in [False,True]:
   pos,norm,uv,tan,idx=B.geometry([6.4,6.4],closed);p=np.array(pos);N=np.array(norm);T=np.array(tan)[:,:3];self.assertLess(abs((N*T).sum(1)).max(),1e-10)
   for a,b,c in np.array(idx).reshape(-1,3):self.assertGreater(np.dot(np.cross(p[b]-p[a],p[c]-p[a]),N[a]),0)
 def test_closed_slab_volume(self):
  p,n,u,t,i=B.geometry([6.4,6.4],True);p=np.array(p);tri=np.array(i).reshape(-1,3);vol=sum(np.dot(p[a],np.cross(p[b],p[c]))/6 for a,b,c in tri);self.assertAlmostEqual(vol,.0064**2*.002,places=14)
 def test_sampling_is_linear_and_clamps(self):
  a=np.array([[0.,1.],[2.,3.]]);self.assertEqual(float(B.sample(a,np.array(.5),np.array(.5))),1.5);self.assertEqual(float(B.sample(a,np.array(-10.),np.array(10.))),2.)
 def test_png_exr_and_channels(self):
  old=B.ROOT
  with tempfile.TemporaryDirectory() as td:
   B.ROOT=Path(td)
   try:
    r=next(r for r in D.recipes() if r['family']=='metal-am');f=B.fields(r,64);B.maps(f,Path(td)/'maps');g=lambda n:np.asarray(Image.open(Path(td)/'maps'/(n+'.png')))
    gl=g('normal_opengl');dx=g('normal_directx');np.testing.assert_array_equal(dx[:,:,1],255-gl[:,:,1]);np.testing.assert_array_equal(g('orm')[:,:,1],g('roughness'));self.assertTrue((g('metallic')==255).all());self.assertTrue((g('orm')[:,:,0]==255).all());z=B.cv2.imread(str(Path(td)/'maps/height_mm.exr'),B.cv2.IMREAD_UNCHANGED);np.testing.assert_array_equal(z,f['height']);self.assertLess(abs(g('height_mm_u16').astype(float)/65535*.5-.25-z).max(),.5/65535)
   finally:B.ROOT=old
if __name__=='__main__':unittest.main(verbosity=2)
