import tempfile
import unittest
from pathlib import Path
import importlib.util

SPEC = importlib.util.spec_from_file_location(
    "awal_gate", Path(__file__).parents[1] / "scripts" / "awal_training_gate.py"
)
GATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GATE)


def registry(training="allowed", evaluation="allowed", status="verified"):
    return {"sources": [{
        "source_id": "src-test",
        "evidence_status": status,
        "declared_permissions": {"training": training, "evaluation": evaluation},
    }]}


def record(ident, split="train", **changes):
    item = {
        "record_id": ident, "text": f"darija phrase {ident}",
        "source_id": "src-test", "source_locator": "dataset.csv#row=1",
        "permission_evidence": "evidence://rights/approved-001",
        "rights_review_status": "cleared",
        "training_permission": "allowed", "evaluation_permission": "allowed",
        "split": split,
    }
    item.update(changes)
    return item


class EligibilityTests(unittest.TestCase):
    def test_valid_records_are_partitioned(self):
        errors, output = GATE.validate(
            [record("a", "train"), record("b", "validation"), record("c", "test")],
            registry(),
        )
        self.assertEqual(errors, [])
        self.assertEqual([r["record_id"] for r in output["train"]], ["a"])
        self.assertEqual([r["record_id"] for r in output["validation"]], ["b"])
        self.assertEqual([r["record_id"] for r in output["test"]], ["c"])

    def test_missing_source_is_rejected(self):
        errors, _ = GATE.validate([record("a", source_id="")], registry())
        self.assertTrue(any("source_id" in error for error in errors))

    def test_missing_permission_evidence_is_rejected(self):
        errors, _ = GATE.validate([record("a", permission_evidence=" ")], registry())
        self.assertTrue(any("permission_evidence" in error for error in errors))

    def test_unknown_rights_status_is_rejected(self):
        errors, _ = GATE.validate([record("a", rights_review_status="pending_verification")], registry())
        self.assertTrue(any("rights_review_status" in error for error in errors))

    def test_training_permission_is_required(self):
        errors, _ = GATE.validate([record("a", training_permission="unknown")], registry())
        self.assertTrue(any("training_permission" in error for error in errors))

    def test_source_must_be_independently_verified(self):
        errors, _ = GATE.validate([record("a")], registry(status="repository_metadata_only"))
        self.assertTrue(any("not independently verified" in error for error in errors))

    def test_source_level_training_permission_is_required(self):
        errors, _ = GATE.validate([record("a")], registry(training="unknown"))
        self.assertTrue(any("lacks explicit training permission" in error for error in errors))

    def test_evaluation_permission_is_independent(self):
        errors, _ = GATE.validate([record("a", "validation")], registry(evaluation="unknown"))
        self.assertTrue(any("lacks explicit evaluation permission" in error for error in errors))

    def test_train_evaluation_text_leakage_is_rejected(self):
        errors, _ = GATE.validate([
            record("a", "train", text="Salam 3likom"),
            record("b", "validation", text=" salam   3LIKOM "),
        ], registry())
        self.assertTrue(any("data leakage" in error for error in errors))

    def test_duplicate_ids_are_rejected(self):
        errors, _ = GATE.validate([record("same"), record("same", "test")], registry())
        self.assertTrue(any("duplicate record_id" in error for error in errors))

    def test_unrecognized_split_is_rejected(self):
        errors, _ = GATE.validate([record("a", split="training")], registry())
        self.assertTrue(any("split must be one of" in error for error in errors))

    def test_output_files_are_separate_jsonl(self):
        with tempfile.TemporaryDirectory() as directory:
            train = Path(directory) / "train.jsonl"
            evaluation = Path(directory) / "evaluation.jsonl"
            GATE.write_jsonl(train, [record("a", "train")])
            GATE.write_jsonl(evaluation, [record("b", "test")])
            self.assertEqual(GATE.load_records(train), [record("a", "train")])
            self.assertEqual(GATE.load_records(evaluation), [record("b", "test")])


if __name__ == "__main__":
    unittest.main()
