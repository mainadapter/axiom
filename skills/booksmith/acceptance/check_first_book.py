"""Private 190-page regression: text/image integrity, not a hierarchy oracle.

Usage: PYTHONPATH=. python acceptance/check_first_book.py NEW_BUNDLE OLD_SCHEMA1_BUNDLE
The old diagnostic bundle was blocked on images and has no accepted EPUB.
"""
import json
from pathlib import Path
import sys
from book_epub.validate import audit_model


def check(bundle,previous):
    m=json.loads((bundle/'model.json').read_text());r=json.loads((bundle/'report.json').read_text())
    old=json.loads((previous/'model.json').read_text())
    assert m['source_sha256']==old['source_sha256']=='950d810c1d6eee93ae7c79d7662c17f635fe465fa85356b3e7440d38b35c5d25'
    assert len(m['pages'])==190 and len(m['lines'])==len(old['lines'])==7649
    assert all(all(n.get(k)==v for k,v in o.items()) for o,n in zip(old['lines'],m['lines']))
    assert m['image_sources']==['p1-img1','p2-img1','p188-img1']
    assert [a['id'] for a in m['assets']]==m['image_sources']
    assert all(f['status']=='pass' for f in audit_model(m))
    for code in ['source_accounting','source_text','source_images_semantics','serialized_text','serialized_images_semantics','package_navigation_css']:
        fs=[f for f in r['findings'] if f['code']==code];assert fs and all(f['status']=='pass' for f in fs),code
    checker=next(f for f in r['findings'] if f['code']=='epubcheck')['evidence']['report']['checker']
    assert all(checker[k]==0 for k in ['nFatal','nError','nWarning','nUsage'])
    result=dict(pages=190,source_lines=7649,old_source_fields_identical=True,images=3,
                source_text_order_emphasis_and_images='pass',state=r['state'],epub_sha256=r['epub_sha256'],
                full_editorial_hierarchy_verified=False,
                epubcheck={k:checker[k] for k in ['checkerVersion','nFatal','nError','nWarning','nUsage']})
    print(json.dumps(result,ensure_ascii=False,indent=2));return result

if __name__=='__main__':check(Path(sys.argv[1]),Path(sys.argv[2]))
