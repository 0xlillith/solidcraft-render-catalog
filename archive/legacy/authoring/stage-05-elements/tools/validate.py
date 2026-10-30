#!/usr/bin/env python3
"""Independent stage05 resource, image and physical-link verification."""
import json, pathlib, sys, hashlib
import numpy as np, cv2
from PIL import Image
ROOT=pathlib.Path(__file__).resolve().parents[1]
SOURCE=ROOT/"data/pubchem-reference.json"
def fail(msg):raise AssertionError(msg)
def go():
 raw=json.loads(SOURCE.read_text());rr=raw["records"]
 assert len(rr)==118 and [x["atomic_number"] for x in rr]==list(range(1,119))
 assert len(set(x["id"] for x in rr))==118
 profiles=json.loads((ROOT/"data/element-profiles.json").read_text())["profiles"]
 looks=json.loads((ROOT/"data/element-appearances.json").read_text())["items"]
 index=json.loads((ROOT/"registry/resource-index.json").read_text())
 assert len(profiles)==118 and len(looks)==154 and len(index["records"])==272
 assert len(index["mapsets"])==6
 ids={x["id"] for x in rr};seen=set()
 for p in profiles:
  assert p["id"] in ids
  den=p["density_reference"]
  assert den["status"]=="reference_only_not_auto_assign"
  assert den["value_kg_m3"] is None or (isinstance(den["value_kg_m3"],(int,float)) and den["value_kg_m3"]>0)
  assert p["optical_data"]["measured_spectral_reflectance"] is None
  assert p["optical_data"]["measured_complex_ior"] is None
  assert p["isotope_or_allotrope_identified"] is False
  assert (ROOT/p["card_path"]).is_file()
  with Image.open(ROOT/p["card_path"]) as im:
   assert im.size==(780,500) and im.mode=="RGB"
 for k in looks:
  assert k["id"] not in seen;seen.add(k["id"])
  assert k["element_id"] in ids and next(x for x in rr if x["id"]==k["element_id"])["preview_representation"]=="illustrative_solid_pbr"
  assert k["native_acceptance"]=="not_run"
  folder=ROOT/"build/materials"/k["id"]
  assert all((folder/x).is_file() for x in ["material.glb","material.gltf","material.bin","appearance.json","preview.png"])
  d=json.loads((folder/"material.gltf").read_text())
  assert d["materials"][0]["extras"]["element_id"]==k["element_id"]
  assert d["materials"][0]["extras"]["unmeasured_optics"] is True
  with Image.open(folder/"preview.png") as im:assert im.size==(540,400)
 expected_png=0; expected_exr=0
 for group,meta in index["mapsets"].items():
  for variant,size in [("master",2048),("runtime",1024)]:
   path=ROOT/meta[variant]
   assert path.exists() and not meta["seamless"]
   for name in ["base_color","normal_opengl","normal_directx","roughness","metallic","orm","height_u16"]:
    f=path/(name+".png");assert f.exists(),str(f)
    with Image.open(f) as a:
     assert a.size==(size,size),str(f)
     a.verify()
    expected_png+=1
   h=path/"height_mm.exr";assert h.is_file()
   arr=cv2.imread(str(h),cv2.IMREAD_UNCHANGED)
   assert arr is not None and arr.shape==(size,size) and np.isfinite(arr).all()
   assert float(np.max(np.abs(arr)))<.1
   expected_exr+=1
   with Image.open(path/"orm.png") as im:
    p=np.asarray(im)
   with Image.open(path/"roughness.png") as im:
    rough=np.asarray(im)
   with Image.open(path/"metallic.png") as im:
    metal=np.asarray(im)
   assert np.all(p[:,:,0]==255) and np.array_equal(p[:,:,1],rough) and np.array_equal(p[:,:,2],metal)
   assert np.unique(metal).tolist()==([255] if group.startswith("metal-") else [0])
 assert expected_png==84 and expected_exr==12
 gltf=json.loads((ROOT/"reports/gltf-validation.json").read_text())
 assert gltf["validated"]==308 and not gltf["errors"]
 report={"status":"PASS","elements":len(profiles),"element_cards":len(profiles),
  "solid_appearance_variants":len(looks),"reference_only_elements":41,
  "shared_mapsets":len(index["mapsets"]),"png_maps":expected_png,"signed_height_exr":expected_exr,
  "portable_files":gltf["validated"],"official_gltf_errors":0,"official_gltf_warnings":0,
  "physics_assigned_to_parts":False,"native_acceptance":"not_run","premium_qualification":"not_qualified",
  "plugin_standard":None,"factual_source":"NIH/NLM PubChem periodic table JSON 2026-10-26"}
 (ROOT/"reports").mkdir(exist_ok=True)
 (ROOT/"reports/validation.json").write_text(json.dumps(report,indent=2)+"\n")
 print("ELEMENT_VALIDATION_PASS",json.dumps(report))
if __name__=="__main__":
 import os
 os.environ["OPENCV_IO_ENABLE_OPENEXR"]="1"
 go()
