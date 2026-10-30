"""Gate published thumbnails on exact runtime-map inputs and complete coverage."""
from data import ROOT,records,dump
from validate_stage import load,require,digest

def main():
 pp,recipes,vv=records();byid={r['id']:r for r in recipes}
 report=load(ROOT/'reports/preview-validation.json');require(report['status']=='PASS' and report['count']==280,'incomplete preview production')
 require(report['runtime_map_resolution']==1024 and report['pixel_supersampling']==2,'preview sampling quality')
 hashes={r['id']:r['sha256'] for r in report['outputs']};require(len(hashes)==280,'preview output identities')
 for v in vv:
  r=byid[v['process_id']];folder=ROOT/'build/materials'/v['id'];receipt=load(folder/'preview-receipt.json');contract=load(ROOT/'build/maps'/r['group']/r['id']/'map-contract.json')
  require(receipt['id']==v['id'] and receipt['sha256']==hashes[v['id']]==digest(folder/'preview.png'),'preview output hash')
  require(receipt['native_acceptance']=='not_run','false native claim')
  for role in ('base_color_modulation','normal_opengl','roughness'):
   require(receipt['input_map_sha256'][role]==contract['exports']['runtime'][role]['sha256'],'preview input map hash')
 validation=load(ROOT/'reports/validation.json');require(validation['status']=='PASS','full stage gate not passed')
 validation['filtered_preview_validation']={'status':'PASS','count':280,'input_maps':'actual 1024-square runtime resources','supersampling':2,'averaging':'linear-before-tonemapping','native_rendering':False}
 dump(ROOT/'reports/validation.json',validation);print('PREVIEW_INPUT_OUTPUT_VERIFIED 280')
if __name__=='__main__':main()
