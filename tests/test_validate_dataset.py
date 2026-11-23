import importlib.util, json, unittest
from pathlib import Path

ROOT=Path(__file__).parents[1]
spec=importlib.util.spec_from_file_location("validator",ROOT/"scripts"/"validate_dataset.py")
module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
audit_spec=importlib.util.spec_from_file_location("provenance_audit",ROOT/"scripts"/"audit_provenance.py")
audit_module=importlib.util.module_from_spec(audit_spec); audit_spec.loader.exec_module(audit_module)

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
 def test_malformed_optional_values_return_errors_not_exceptions(self):
  d=self.fixture(); e=d["entries"][0]
  e["entry_type"]=[]; e["review"]={"status":[]}
  e["provenance"]={"training_permission":[]}
  errors=module.validate(d)
  self.assertTrue(any("entry_type" in x for x in errors))
  self.assertTrue(any("review.status" in x for x in errors))
  self.assertTrue(any("training_permission" in x for x in errors))
 def test_malformed_context_ids_return_errors_not_exceptions(self):
  d={"meta":{"lexicon_version":"1.3.0","version":"1.0.0","examples_count":1},"examples":[{"id":[],"entry_id":[]}]}
  errors=module.validate_context_links(d,self.fixture())
  self.assertTrue(any("entry_id" in x for x in errors))
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
  self.assertTrue(any("lexicon entry" in x for x in module.validate_context_links(d,self.fixture())))
 def test_real_north_regional_dataset_passes_schema_and_integrity(self):
  regional=json.loads((ROOT/"data"/"regions"/"north.json").read_text(encoding="utf-8"))
  schema=json.loads((ROOT/"data"/"schemas"/"regional-lexicon.schema.json").read_text(encoding="utf-8"))
  self.assertEqual(module.validate_schema(regional,schema,"regional"),[])
  self.assertEqual(module.validate_regional_integrity(regional),[])
 def test_regional_duplicate_ids_and_unknown_categories_fail(self):
  regional={"meta":{"entries_count":2},"categories":[{"id":"family","label_ar":"العائلة"}],"entries":[
   {"id":"north-001","category":"family"},{"id":"north-001","category":"unknown"}
  ]}
  errors=module.validate_regional_integrity(regional)
  self.assertTrue(any("duplicate id" in error for error in errors))
  self.assertTrue(any("unknown category" in error for error in errors))
 def test_provenance_audit_flags_missing_evidence_and_unknown_permissions(self):
  resource={"entries":[{"id":1,"provenance":{"source_type":"corpus","training_permission":"allowed","redistribution_permission":"unknown","commercial_permission":"unknown"}}]}
  summary,findings=audit_module.audit_resource(resource,"test",{"src-test"})
  self.assertEqual(summary["records"],1)
  self.assertEqual(summary["missing_or_unknown"]["source_id"],1)
  self.assertEqual(summary["missing_or_unknown"]["permission_evidence"],1)
  self.assertTrue(any("permission_evidence is absent" in item for item in findings))
 def test_provenance_audit_accepts_registry_source_and_evidence(self):
  resource={"entries":[{"id":1,"provenance":{
   "source_type":"dictionary","source_id":"src-test","source_locator":"file.json#entry-1",
   "permission_evidence":"https://example.org/license","rights_review_status":"cleared",
   "redistribution_permission":"allowed","training_permission":"allowed","commercial_permission":"not_allowed"
  }}]}
  summary,findings=audit_module.audit_resource(resource,"test",{"src-test"})
  self.assertEqual(summary["records_with_permission_evidence"],1)
  self.assertEqual(summary["records_with_source_locator"],1)
  self.assertEqual(summary["records_with_rights_review_status"],1)
  self.assertEqual(findings,[])
 def test_provenance_audit_rejects_unregistered_source_id(self):
  resource={"entries":[{"id":"x","provenance":{"source_type":"original","source_id":"src-absent"}}]}
  summary,findings=audit_module.audit_resource(resource,"test",{"src-known"})
  self.assertEqual(summary["unmapped_source_ids"],1)
  self.assertTrue(any("not present in the source registry" in item for item in findings))

if __name__=="__main__": unittest.main()
