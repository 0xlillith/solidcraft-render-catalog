import pathlib,sys,unittest,json
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
import build
class ElementTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.rows=json.loads((ROOT/"data/pubchem-reference.json").read_text())["records"]
 def test_all_118_identity(self):
  self.assertEqual(len(self.rows),118)
  self.assertEqual([x["atomic_number"] for x in self.rows],list(range(1,119)))
  self.assertEqual(len(set(x["symbol"] for x in self.rows)),118)
  self.assertEqual(self.rows[-1]["symbol"],"Og")
 def test_states_are_not_fabricated_bulk_solids(self):
  for x in self.rows:
   if x["standard_state_reported"].startswith("Expected") or x["atomic_number"]>=95 or x["atomic_number"] in (61,84,85,87):
    self.assertNotEqual(x["preview_representation"],"illustrative_solid_pbr")
 def test_not_false_engineering_data(self):
  for x in self.rows:
   self.assertEqual(x["density_reference"]["status"],"reference_only_not_auto_assign")
   self.assertIsNone(x["optical_data"]["measured_complex_ior"])
   self.assertIsNone(x["optical_data"]["measured_spectral_reflectance"])
   self.assertFalse(x["isotope_or_allotrope_identified"])
 def test_physical_density_nonnegative(self):
  for x in self.rows:
   a=x["density_reference"]["value_kg_m3"]
   self.assertTrue(a is None or (a>0 and a<30000))
 def test_gas_is_not_a_solid_specimen(self):
  for x in self.rows:
   if x["standard_state_reported"]=="Gas":self.assertEqual(x["preview_representation"],"gas_reference_only")
 def test_nonmetal_not_accidentally_metallic(self):
  self.assertFalse(build.metallic("Nonmetal"))
  self.assertFalse(build.metallic("Metalloid"))
  self.assertTrue(build.metallic("Transition metal"))
  self.assertTrue(build.metallic("Lanthanide"))
  self.assertTrue(build.metallic("Actinide"))
 def test_surface_fields_bounded_and_deterministic(self):
  for surface in ["metal-polished","metal-brushed","metalloid-cleaved","metalloid-matte","nonmetal-crystal","nonmetal-grain"]:
   h,r,a=build.fields(surface,128)
   self.assertEqual(h.shape,(128,128))
   self.assertTrue((r>=.055).all() and (r<=.92).all())
   self.assertTrue((abs(h)<.1).all())
   self.assertTrue((h==build.fields(surface,128)[0]).all())
 def test_appearance_coverage(self):
  self.assertEqual(sum(x["preview_representation"]=="illustrative_solid_pbr" for x in self.rows),77)
  self.assertEqual(sum(len(build.group_style(x)) for x in self.rows if x["preview_representation"]=="illustrative_solid_pbr"),154)
 def test_cpk_color_not_bulk_material(self):
  self.assertNotIn("CPKHexColor",self.rows[0])
  self.assertEqual(build.palette(next(x for x in self.rows if x["symbol"]=="Au")),[211,157,59])
if __name__=="__main__":unittest.main()
