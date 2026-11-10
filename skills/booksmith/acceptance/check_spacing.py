"""Reproduce spacing evidence locally; PDFs/narrative are never committed.

Usage: PYTHONPATH=. python acceptance/check_spacing.py ORIGINAL OLD_BUNDLE NEW_BUNDLE OUTPUT_JSON
Writes private per-boundary examples, page/region counts and regression assertions.
Region names are supplied by the human source review, not reconstruction rules.
"""
import json
import sys
from collections import Counter
from pathlib import Path
from book_epub.spacing import audit_spacing
from book_epub.common import compact, classify


def check(source, old_bundle, new_bundle, output):
    old=json.loads((old_bundle/'model.json').read_text())
    new=json.loads((new_bundle/'model.json').read_text())
    assert old['source_sha256']==new['source_sha256']
    before=audit_spacing(old,source)
    after=audit_spacing(new,source)
    assert not any(f['status']=='fail' for f in after)
    assert [(l['id'],l['page'],l['x0'],l['x1'],l['top'],l['bottom'],l.get('excluded')) for l in old['lines']]==[
        (l['id'],l['page'],l['x0'],l['x1'],l['top'],l['bottom'],l.get('excluded')) for l in new['lines']]
    assert [compact(l['text']) for l in old['lines']]==[compact(l['text']) for l in new['lines']]
    for a,b in zip(old['blocks'],new['blocks']):
        assert {k:v for k,v in a.items() if k not in ('text','spans')}=={k:v for k,v in b.items() if k not in ('text','spans')}
    assert len(old['blocks'])==len(new['blocks']) and old['assets']==new['assets']
    # Only newly logged, literal-space insertions may differ in source text.
    transforms=[t for t in new['transformations'] if t['kind']=='preserve_explicit_space']
    by_id={l['id']:l for l in new['lines']}
    restored={l['id']:l['text'] for l in new['lines']}
    for t in sorted(transforms,key=lambda t:t['offset'],reverse=True):
        key=t['source'][0];offset=t['offset']
        assert restored[key][offset]==' '
        restored[key]=restored[key][:offset]+restored[key][offset+1:]
    assert [restored[l['id']] for l in new['lines']]==[l['text'] for l in old['lines']]
    result=dict(source_sha256=new['source_sha256'],
                old_spacing_state=classify(before),new_spacing_state=classify(after),
                before=dict(Counter(f['evidence'].get('reason',f['status']) for f in before)),
                after=dict(Counter(f['evidence'].get('reason',f['status']) for f in after)),
                inserted_literal_spaces=len(transforms),
                page_counts=[dict(page=p,confirmed=sum(f['status']=='fail' and f['evidence']['page']==p for f in before),
                                  punctuation=sum(f['evidence'].get('reason')=='punctuation_difference' and f['evidence']['page']==p for f in before))
                             for p in range(1,len(new['pages'])+1)],
                findings_before=before,findings_after=after,
                invariants='geometry, nonspace text, blocks, hierarchy, images and reading order preserved')
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print(json.dumps({k:v for k,v in result.items() if not k.startswith('findings') and k!='page_counts'},ensure_ascii=False,indent=2))
    return result

if __name__=='__main__':check(*(Path(p) for p in sys.argv[1:]))
