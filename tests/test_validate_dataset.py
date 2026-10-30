import importlib.util, unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location("validator",Path(__file__).parents[1]/"scripts"/"validate_dataset.py")
module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
class Tests(unittest.TestCase):
 def fixture(self):
  return {"meta":{"entries_count":1,"categories_count":1},"categories":[{"category":"تحيات","count":1}],"entries":[{"id":1,"category":"تحيات","darija_ar":"سلام","darija_latin":"salam","fusha_ar":"سلام","fr":"salut"}]}
 def test_legacy_entry_is_valid(self): self.assertEqual(module.validate(self.fixture()),[])
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
if __name__=="__main__": unittest.main()
