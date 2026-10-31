import importlib.util, json, unittest
from pathlib import Path

ROOT=Path(__file__).parents[1]
spec=importlib.util.spec_from_file_location("validator",ROOT/"scripts"/"validate_dataset.py")
module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)

class ValidatorTests(unittest.TestCase):
 def fixture(self):
  return {"meta":{"entries_count":1,"categories_count":1},"categories":[{"category":"تحيات","count":1}],"entries":[{"id":1,"category":"تحيات","darija_ar":"سلام","darija_latin":"salam","fusha_ar":"سلام","fr":"salut"}]}
 def test_legacy_entry_is_valid_for_custom_checks(self): self.assertEqual(module.validate(self.fixture()),[])
 def test_duplicate_id_fails(self):
  d=self.fixture(); d["entries"].append(dict(d["entries"][0])); d["meta"]["entries_count"]=2; d["categories"][0]["count"]=2
  self.assertTrue(any("duplicate id" in x for x in module.validate(d)))
 def test_count_mismatch_fails(self):
  d=self.fixture(); d["categories"][0]["count"]=2
  self.assertTrue(any("declared 2, actual 1" in x for x in module.validate(d)))
 def test_unknown_provenance_is_explicit_and_valid(self):
  d=self.fixture(); d["entries"][0]["provenance"]={"source_type":"unknown","training_permission":"unknown","redistribution_permission":"unknown","commercial_permission":"unknown"}; d["entries"][0]["review"]={"status":"pending"}
  self.assertEqual(module.validate(d),[])
 def test_invalid_permission_fails(self):
  d=self.fixture(); d["entries"][0]["provenance"]={"training_permission":"maybe"}
  self.assertTrue(any("training_permission" in x for x in module.validate(d)))
 def test_real_1_3_0_dataset_passes_schema(self):
  d=json.loads((ROOT/"data"/"moroccan-darija.json").read_text(encoding="utf-8")); s=json.loads((ROOT/"data"/"schema.json").read_text(encoding="utf-8"))
  self.assertEqual(module.validate_schema(d,s),[]); self.assertEqual(module.validate(d),[])
 def test_schema_rejects_unknown_entry_property(self):
  d=json.loads((ROOT/"data"/"moroccan-darija.json").read_text(encoding="utf-8")); d["entries"][0]["unregistered_field"]="x"
  s=json.loads((ROOT/"data"/"schema.json").read_text(encoding="utf-8"))
  errors=module.validate_schema(d,s)
  self.assertTrue(any("unregistered_field" in error for error in errors))
 def test_empty_context_file_passes_schema(self):
  d={"meta":{"lexicon_version":"1.3.0","version":"1.0.0","examples_count":0},"examples":[]}; s=json.loads((ROOT/"data"/"context-schema.json").read_text(encoding="utf-8"))
  self.assertEqual(module.validate_schema(d,s,"contexts"),[]); self.assertEqual(module.validate_context_links(d,self.fixture()),[])
 def test_valid_context_example_passes_schema_and_link_check(self):
  d={"meta":{"lexicon_version":"1.3.0","version":"1.0.0","examples_count":1},"examples":[{
   "id":"ctx-000001","entry_id":1,"meaning_ar":"تحية","example_darija_ar":"سلام، كيداير؟",
   "example_darija_latin":["salam, kidayr?"],"provenance":{"source_type":"original","redistribution_permission":"allowed","training_permission":"allowed","commercial_permission":"unknown"},
   "review":{"status":"pending"}
  }]}
  s=json.loads((ROOT/"data"/"context-schema.json").read_text(encoding="utf-8"))
  self.assertEqual(module.validate_schema(d,s,"contexts"),[])
  self.assertEqual(module.validate_context_links(d,self.fixture()),[])
 def test_context_reference_must_exist(self):
  d={"meta":{"lexicon_version":"1.3.0","version":"1.0.0","examples_count":1},"examples":[{"id":"ctx-000001","entry_id":999}]}
  self.assertTrue(any("unknown lexicon entry" in x for x in module.validate_context_links(d,self.fixture())))

if __name__=="__main__": unittest.main()
