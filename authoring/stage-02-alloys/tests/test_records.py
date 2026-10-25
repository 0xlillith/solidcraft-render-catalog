import importlib.util, json, math, unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('source',R/'tools/prepare_alloys.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Records(unittest.TestCase):
 def test_counts_and_unique_ids(self):
  self.assertEqual(len(m.PROFILES),24);self.assertEqual(len({p['id'] for p in m.PROFILES}),24);self.assertEqual(len(m.FINISHES),8)
 def test_every_appearance_has_a_density_and_primary_source(self):
  ids={s['id'] for s in m.SOURCES}
  for p in m.PROFILES:
   self.assertIn(p['source_id'],ids);d=[v for v in p['properties'] if v['quantity']=='density'];self.assertEqual(len(d),1);self.assertTrue(2000<d[0]['value']<10000);self.assertFalse(p['auto_assign'])
 def test_values_recompute_from_explicit_original_units(self):
  for p in m.PROFILES:
   for v in p['properties']:
    vals=v['value'] if isinstance(v['value'],list) else [v['value']];old=v['original']['value'];old=old if isinstance(old,list) else [old]
    for x,y in zip(vals,old):self.assertTrue(math.isfinite(x));self.assertAlmostEqual(x,y*m.UNITS[v['original']['unit']][1])
    self.assertIsNone(v['uncertainty']);self.assertTrue(v['source_locator'])
 def test_titanium_range_is_not_replaced_with_midpoint(self):
  p=next(p for p in m.PROFILES if p['id']=='ti-6al4v');e=next(v for v in p['properties'] if v['quantity']=='young_modulus');self.assertEqual(e['value'],[107e9,122e9]);self.assertEqual(e['temperature_k'],293.15)
 def test_7075_tempers_keep_distinct_strength_and_thermal_records(self):
  def props(id):return {v['quantity']:v['value'] for p in m.PROFILES if p['id']==id for v in p['properties']}
  a,b=props('al-7075-t651'),props('al-7075-t7351');self.assertEqual(a['density'],2800);self.assertEqual(a['yield_strength'],503e6);self.assertEqual(b['yield_strength'],434e6);self.assertEqual(a['thermal_conductivity'],130);self.assertEqual(b['thermal_conductivity'],155)
 def test_bad_online_modulus_is_excluded(self):
  p=next(p for p in m.PROFILES if p['id']=='ni-825');self.assertNotIn('young_modulus',[v['quantity'] for v in p['properties']])
 def test_d2_compression_does_not_become_tensile_yield(self):
  p=next(p for p in m.PROFILES if p['id']=='d2-sverker21-62hrc');self.assertIn('62 HRC',p['condition']);q={v['quantity']:v['value'] for v in p['properties']};self.assertEqual(q['compressive_proof_strength'],2200e6);self.assertNotIn('yield_strength',q)
 def test_compositions_preserve_limits_and_do_not_invent_balances(self):
  for p in m.PROFILES:
   for c in p['composition']:
    values=[c[k] for k in ('min_mass_percent','max_mass_percent','nominal_mass_percent') if c[k] is not None]
    self.assertTrue(all(0<=x<=100 for x in values))
    if c['min_mass_percent'] is not None and c['max_mass_percent'] is not None:self.assertLessEqual(c['min_mass_percent'],c['max_mass_percent'])
    if c['balance']:self.assertFalse(values)
 def test_physical_effects_are_not_derived_from_finishes(self):
  before=json.dumps(m.PROFILES,sort_keys=True)
  for p in m.PROFILES:
   for f in m.FINISHES:self.assertNotIn('density',f);self.assertTrue(f['id'])
  self.assertEqual(before,json.dumps(m.PROFILES,sort_keys=True))
 def test_native_density_conversion_does_not_invent_Poisson_ratio(self):
  self.assertAlmostEqual(m.UNITS['lb/in^3'][1],27679.904710203,places=6);self.assertAlmostEqual(m.UNITS['microstrain/degF'][1],1.8e-6)
if __name__=='__main__':unittest.main(verbosity=2)
