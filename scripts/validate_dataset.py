#!/usr/bin/env python3
"""Validate the Moroccan Darija lexicon and its context examples."""
import argparse, json, sys
from collections import Counter
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker

REQUIRED=("id","category","darija_ar","darija_latin","fusha_ar","fr")
ENTRY_TYPES={"word","expression","sentence","proverb","question","conversational","unknown"}
REVIEW={"pending","in_review","reviewed","rejected","needs_correction","unknown"}
PERMISSIONS={"allowed","not_allowed","unknown","not_applicable"}

def validate_schema(data, schema, label="data"):
    Draft202012Validator.check_schema(schema)
    validator=Draft202012Validator(schema, format_checker=FormatChecker())
    errors=[]
    for error in sorted(validator.iter_errors(data), key=lambda e:(list(map(str,e.absolute_path)),e.message)):
        location=".".join(str(part) for part in error.absolute_path) or "$"
        errors.append(f"{label}.{location}: {error.message}")
    return errors

def validate(data):
    """Project-specific integrity checks complementing JSON Schema."""
    errors=[]
    if not isinstance(data,dict): return ["root: expected a JSON object"]
    for key in ("meta","categories","entries"):
        if key not in data: errors.append(f"root: missing required key '{key}'")
    if errors: return errors
    meta,categories,entries=data["meta"],data["categories"],data["entries"]
    if not isinstance(meta,dict): return ["meta: expected an object"]
    if not isinstance(categories,list): return ["categories: expected an array"]
    if not isinstance(entries,list): return ["entries: expected an array"]
    declared,actual={},Counter()
    for i,item in enumerate(categories):
        if not isinstance(item,dict) or not isinstance(item.get("category"),str) or not isinstance(item.get("count"),int) or isinstance(item.get("count"),bool):
            errors.append(f"categories[{i}]: expected category string and integer count"); continue
        name=item["category"]
        if not name.strip(): errors.append(f"categories[{i}].category: empty")
        if name in declared: errors.append(f"categories[{i}]: duplicate category '{name}'")
        declared[name]=item["count"]
        if item["count"]<0: errors.append(f"categories[{i}].count: must be >= 0")
    ids=set()
    for i,e in enumerate(entries):
        p=f"entries[{i}]"
        if not isinstance(e,dict): errors.append(f"{p}: expected object"); continue
        for field in REQUIRED:
            if field not in e: errors.append(f"{p}: missing '{field}'")
            elif field!="id" and (not isinstance(e[field],str) or not e[field].strip()): errors.append(f"{p}.{field}: expected non-empty string")
        ident=e.get("id")
        if isinstance(ident,bool) or not isinstance(ident,int) or ident<1: errors.append(f"{p}.id: expected positive integer")
        elif ident in ids: errors.append(f"{p}.id: duplicate id {ident}")
        else: ids.add(ident)
        cat=e.get("category")
        if isinstance(cat,str):
            actual[cat]+=1
            if cat not in declared: errors.append(f"{p}.category: unknown category '{cat}'")
        if "entry_type" in e and (not isinstance(e["entry_type"],str) or e["entry_type"] not in ENTRY_TYPES):
            errors.append(f"{p}.entry_type: unsupported value")
        if "review" in e:
            review=e["review"]
            if not isinstance(review,dict) or not isinstance(review.get("status"),str) or review.get("status") not in REVIEW:
                errors.append(f"{p}.review.status: missing or unsupported status")
        if "provenance" in e:
            prov=e["provenance"]
            if not isinstance(prov,dict): errors.append(f"{p}.provenance: expected object")
            else:
                for field in ("redistribution_permission","training_permission","commercial_permission"):
                    if field in prov and (not isinstance(prov[field],str) or prov[field] not in PERMISSIONS):
                        errors.append(f"{p}.provenance.{field}: unsupported permission")
    if len(entries)!=meta.get("entries_count"): errors.append(f"meta.entries_count: declared {meta.get('entries_count')}, actual {len(entries)}")
    if len(categories)!=meta.get("categories_count"): errors.append(f"meta.categories_count: declared {meta.get('categories_count')}, actual {len(categories)}")
    for cat,count in declared.items():
        if count!=actual[cat]: errors.append(f"categories['{cat}'].count: declared {count}, actual {actual[cat]}")
    extra=set(actual)-set(declared)
    if extra: errors.append("entries: undeclared categories: "+", ".join(sorted(extra)))
    return errors

def validate_context_links(context_data,dataset):
    errors=[]
    if not isinstance(context_data,dict) or not isinstance(dataset,dict): return ["contexts: expected objects"]
    meta=context_data.get("meta",{}); examples=context_data.get("examples",[])
    if isinstance(meta,dict) and meta.get("examples_count")!=len(examples):
        errors.append(f"contexts.meta.examples_count: declared {meta.get('examples_count')}, actual {len(examples)}")
    entries=dataset.get("entries",[])
    if not isinstance(entries,list) or not isinstance(examples,list):
        return ["contexts: 'entries' and 'examples' must be arrays"]
    entry_ids={e.get("id") for e in entries if isinstance(e,dict) and isinstance(e.get("id"),int) and not isinstance(e.get("id"),bool)}
    seen=set()
    for i,example in enumerate(examples):
        if not isinstance(example,dict): continue
        example_id=example.get("id")
        if isinstance(example_id,str):
            if example_id in seen: errors.append(f"contexts.examples[{i}].id: duplicate id {example_id}")
            seen.add(example_id)
        entry_id=example.get("entry_id")
        if isinstance(entry_id,bool) or not isinstance(entry_id,int) or entry_id not in entry_ids:
            errors.append(f"contexts.examples[{i}].entry_id: unknown or invalid lexicon entry {entry_id!r}")
    return errors

def read_json(path): return json.loads(Path(path).read_text(encoding="utf-8"))

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("dataset",nargs="?",default="data/moroccan-darija.json")
    ap.add_argument("--schema",default="data/schema.json")
    ap.add_argument("--contexts",default="data/context-examples.json")
    ap.add_argument("--context-schema",default="data/context-schema.json")
    args=ap.parse_args()
    try:
        dataset=read_json(args.dataset); schema=read_json(args.schema)
        errors=validate_schema(dataset,schema,"dataset")+validate(dataset)
        contexts_path=Path(args.contexts)
        if contexts_path.exists():
            contexts=read_json(contexts_path); context_schema=read_json(args.context_schema)
            errors+=validate_schema(contexts,context_schema,"contexts")
            errors+=validate_context_links(contexts,dataset)
    except (OSError,UnicodeError,json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read valid UTF-8 JSON: {exc}",file=sys.stderr); return 2
    except Exception as exc:
        print(f"ERROR: validation setup failed: {exc}",file=sys.stderr); return 2
    if errors:
        print(f"FAILED: {len(errors)} validation error(s)")
        for error in errors: print("- "+error)
        return 1
    context_count=len(contexts.get("examples",[])) if contexts_path.exists() else 0
    print(f"OK: {len(dataset['entries'])} entries; {len(dataset['categories'])} categories; {context_count} context examples")
    print("JSON Schema: Draft 2020-12 — valid")
    return 0

if __name__=="__main__": raise SystemExit(main())
