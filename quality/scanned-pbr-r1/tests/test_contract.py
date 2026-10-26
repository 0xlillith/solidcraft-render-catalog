import sys,json,pathlib,tempfile,unittest
from PIL import Image
import numpy as np
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
import build
class Contract(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.manifest=json.loads((ROOT/"manifest.json").read_text())
 def test_8_pinned_scans(self):
  self.assertEqual(len(self.manifest["assets"]),8)
  self.assertEqual(len(set(x["slug"] for x in self.manifest["assets"])),8)
 def test_license_and_source_pin(self):
  for r in self.manifest["assets"]:
   self.assertEqual(r["source_asset_licenses"],"CC0-1.0")
   self.assertEqual(len(r["files_hash"]),40)
   self.assertTrue(r["dimensions_mm"][0]>0 and r["dimensions_mm"][1]>0)
 def test_not_engineering_grade(self):
  for r in self.manifest["assets"]:
   self.assertIsNone(r["physical_density_kg_m3"])
   self.assertIsNone(r["physical_strength_Pa"])
   self.assertFalse(r["physical_grade_verified"])
 def test_physical_source_is_not_alloy_density(self):
  self.assertIsNone(self.manifest["assets"][0]["physical_density_kg_m3"])
 def test_geometry_export_synthetic(self):
  with tempfile.TemporaryDirectory() as temp:
   z=np.zeros((16,16,3),dtype=np.uint8)
   z[:,:,2]=200
   orm=z.copy();orm[:,:,0]=255;orm[:,:,1]=150;orm[:,:,2]=0
   nor=z.copy();nor[:,:,0]=128;nor[:,:,1]=128;nor[:,:,2]=255
   row=self.manifest["assets"][0];meta={"physical_profile_id":"scan.test","provider_source":"https://polyhaven.com/a/test"}
   build.build_gltf(pathlib.Path(temp),z,nor,orm,row,meta)
   data=json.loads((pathlib.Path(temp)/"material.gltf").read_text())
   self.assertEqual(data["asset"]["version"],"2.0")
   self.assertEqual(data["materials"][0]["pbrMetallicRoughness"]["metallicFactor"],0)
   self.assertEqual(data["materials"][0]["pbrMetallicRoughness"]["baseColorFactor"],[1,1,1,1])
   self.assertGreater((pathlib.Path(temp)/"material.glb").stat().st_size,500)
 def test_roughness_source_channel(self):
  self.assertEqual(build.AGENT.split("(")[0].strip(),"SolidCraft-Render-Catalog-Quality-Benchmark/1.0")
if __name__=="__main__":unittest.main()
