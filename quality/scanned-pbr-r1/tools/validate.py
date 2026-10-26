#!/usr/bin/env python3
"""Independently validate source-pinned scanned CC0 resources and glTF output."""
from __future__ import annotations
import hashlib,json,os,pathlib,numpy as np
from PIL import Image
ROOT=pathlib.Path(__file__).resolve().parents[1]
def hash_file(path,algorithm):
 m=hashlib.new(algorithm)
 with open(path,"rb") as f:
  for b in iter(lambda:f.read(1024*1024),b""):m.update(b)
 return m.hexdigest()
def main():
 manifest=json.loads((ROOT/"manifest.json").read_text())
 rows=manifest["assets"]
 records=json.loads((ROOT/"registry/resource-index.json").read_text())["records"]
 assert len(rows)==len(records)==8
 assert len({r["slug"] for r in rows})==8
 gltf=json.loads((ROOT/"reports/gltf-validation.json").read_text())
 assert gltf["count"]==16 and gltf["errors"]==0 and gltf["warnings"]==0
 report=[]
 for row in rows:
  slug=row["slug"]
  info=json.loads((ROOT/"data/appearance-records"/(slug+".json")).read_text())
  phys=json.loads((ROOT/"data/physical-profiles"/(slug+".json")).read_text())
  assert info["id"]=="scan."+slug and phys["reference_id"]==info["physical_profile_id"]
  assert info["source_hash"]==row["files_hash"]
  assert phys["density_kg_m3"] is None and phys["strength_Pa"] is None
  assert phys["bulk_material_assignment"] is False and info["license"]=="CC0-1.0"
  assert info["scan_extent_mm"]==row["dimensions_mm"]
  assert info["runtime_resolution_px"]==2048 and info["source_resolution_px"]==4096
  for v in info["roles"].values():
   path=ROOT/v["file"];assert path.is_file()
   assert hash_file(path,"md5")==v["source_md5"]
   assert hash_file(path,"sha256")==v["sha256"]
  folder=ROOT/"build/maps"/slug/"runtime-2048"
  vals={}
  for name in ["base_color","normal_opengl","normal_directx","roughness","orm"]:
   p=folder/(name+".png");assert p.is_file(),p
   with Image.open(p) as im:
    assert im.size==(2048,2048)
    im.verify()
   with Image.open(p) as im:vals[name]=np.asarray(im)
  assert vals["base_color"].shape==(2048,2048,3)
  assert np.array_equal(vals["normal_opengl"][:,:,0],vals["normal_directx"][:,:,0])
  assert np.array_equal(vals["normal_opengl"][:,:,2],vals["normal_directx"][:,:,2])
  assert np.all(vals["normal_opengl"][:,:,1].astype(np.uint16)+vals["normal_directx"][:,:,1].astype(np.uint16)==255)
  n=vals["normal_opengl"].astype(np.float32)/255*2-1
  length=np.linalg.norm(n,axis=2)
  assert np.quantile(np.abs(length-1),.99)<.025
  assert np.all(vals["orm"][:,:,0]==255) and np.all(vals["orm"][:,:,2]==0)
  assert np.array_equal(vals["orm"][:,:,1],vals["roughness"])
  doc=json.loads((ROOT/"build/materials"/slug/"material.gltf").read_text())
  mat=doc["materials"][0];pbr=mat["pbrMetallicRoughness"]
  assert pbr["metallicFactor"]==0 and pbr["roughnessFactor"]==1
  assert pbr["baseColorFactor"]==[1,1,1,1] # Never double-tint a captured albedo.
  assert mat["extras"]["scan_extent_mm"]==row["dimensions_mm"]
  for fname in ["sample.bin","material.gltf","material.glb","preview.png"]:
   assert (ROOT/"build/materials"/slug/fname).is_file()
  with Image.open(ROOT/"build/materials"/slug/"preview.png") as im: assert im.size==(1000,590)
  report.append({"id":slug,"source_roles":list(info["roles"]),"scan_extent_mm":row["dimensions_mm"],
                 "std_albedo_luma":float(vals["base_color"].astype(np.float32).mean(axis=2).std()/255),
                 "std_roughness":float(vals["roughness"].astype(np.float32).std()/255),
                 "native_acceptance":"not_run","premium_visual_qualification":"pending"})
 result={"status":"PASS","assets":len(rows),"portable_count":gltf["count"],
         "source_verified":True,"per_source_original_md5_sha256":True,
         "source_size":4096,"runtime_size":2048,
         "physical_scale_verified":True,"color_space_declared":True,
         "normal_handedness_verified":True,"PBR_channel_integrity_verified":True,
         "native_acceptance":"not_run","premium_qualification":"pending",
         "plugin_standard":None,"items":report}
 (ROOT/"reports").mkdir(exist_ok=True)
 (ROOT/"reports/validation.json").write_text(json.dumps(result,indent=2)+"\n")
 print("CC0_SCANNED_QUALITY_CONTRACT_PASS",len(rows),gltf["count"])
if __name__=="__main__":main()
