#!/usr/bin/env python3
"""Validate the Moroccan Darija JSON lexicon without third-party dependencies."""
import argparse, json, sys
from collections import Counter
from pathlib import Path
REQUIRED=("id","category","darija_ar","darija_latin","fusha_ar","fr")
ENTRY_TYPES={"word","expression","sentence","proverb","question","conversational","unknown"}
REVIEW={"pending","in_review","reviewed","rejected","needs_correction","unknown"}
PERMISSIONS={"allowed","not_allowed","unknown","not_applicable"}

def validate(data):
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
        if "entry_type" in e and e["entry_type"] not in ENTRY_TYPES: errors.append(f"{p}.entry_type: unsupported value")
        if "review" in e:
            r=e["review"]
            if not isinstance(r,dict) or r.get("status") not in REVIEW: errors.append(f"{p}.review.status: missing or unsupported status")
        if "provenance" in e:
            prov=e["provenance"]
            if not isinstance(prov,dict): errors.append(f"{p}.provenance: expected object")
            else:
                for field in ("redistribution_permission","training_permission","commercial_permission"):
                    if field in prov and prov[field] not in PERMISSIONS: errors.append(f"{p}.provenance.{field}: unsupported permission")
    if len(entries)!=meta.get("entries_count"): errors.append(f"meta.entries_count: declared {meta.get('entries_count')}, actual {len(entries)}")
    if len(categories)!=meta.get("categories_count"): errors.append(f"meta.categories_count: declared {meta.get('categories_count')}, actual {len(categories)}")
    for cat,count in declared.items():
        if count!=actual[cat]: errors.append(f"categories['{cat}'].count: declared {count}, actual {actual[cat]}")
    extra=set(actual)-set(declared)
    if extra: errors.append("entries: undeclared categories: "+", ".join(sorted(extra)))
    return errors

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("dataset",nargs="?",default="data/moroccan-darija.json")
    path=Path(ap.parse_args().dataset)
    try: data=json.loads(path.read_text(encoding="utf-8"))
    except (OSError,UnicodeError,json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read valid UTF-8 JSON from {path}: {exc}",file=sys.stderr); return 2
    errors=validate(data)
    if errors:
        print(f"FAILED: {len(errors)} validation error(s)")
        for e in errors: print("- "+e)
        return 1
    print(f"OK: {len(data['entries'])} entries; {len(data['categories'])} categories")
    return 0
if __name__=="__main__": raise SystemExit(main())
