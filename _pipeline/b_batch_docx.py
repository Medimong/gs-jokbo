# -*- coding: utf-8 -*-
import os, json, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from b_parse_docx import parse
P = os.path.dirname(os.path.abspath(__file__))
inv = json.load(open(os.path.join(P, 'a0_files.json')))
all_q, blobs = [], {}
for f in inv['files']:
    if f['ext'] != '.docx': continue
    try:
        qs, rid_blob = parse(os.path.join(inv['drive'], f['rel']), f['rel'])
    except Exception as e:
        print(f"ERR {f['rel']}: {e}"); continue
    nopt = sum(1 for q in qs if len(q['options']) >= 4)
    nans = sum(1 for q in qs if q['answer'])
    nimg = sum(len(q['images']) for q in qs)
    print(f"{f['rel'][:58]:58s} Q={len(qs):4d} opt>=4:{nopt:4d} ans:{nans:4d} img:{nimg:4d}")
    all_q += qs
    for q in qs: q['year'] = f['year']
json.dump(all_q, open(os.path.join(P, 'b_raw_docx.json'), 'w'), ensure_ascii=False)
print(f"\n총 {len(all_q)}문항 -> b_raw_docx.json")
