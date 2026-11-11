"""Private source-specific oracle, never used by the reconstruction motor.

Usage: PYTHONPATH=. python acceptance/check_novel.py NEW_BUNDLE OLD_BUNDLE
Expectations come from the original contents and the recorded 56 bad headings.
No private narrative text is committed or printed.
"""
import json
from pathlib import Path
import sys
import zipfile
from xml.etree import ElementTree as ET
from collections import Counter
from book_epub.validate import audit_model, audit_editorial
from book_epub.common import classify

SOURCE='1ea6d7fc34a67469c6fc27177c8a16638ee7d7dab455dd2c12048b136b39d3dd'
LABELS=['CAPÍTULO '+s for s in ['PRIMEIRO','SEGUNDO','TERCEIRO','QUARTO','QUINTO','SEXTO','SÉTIMO']]
PAGES=[4,33,57,83,122,154,188]
NS={'h':'http://www.w3.org/1999/xhtml','o':'http://www.idpf.org/2007/opf'}


def check(bundle,previous):
    m=json.loads((bundle/'model.json').read_text());r=json.loads((bundle/'report.json').read_text())
    old=json.loads((previous/'model.json').read_text())
    assert m['source_sha256']==old['source_sha256']==SOURCE
    assert old['lines']==m['lines'] and old['assets']==m['assets'], 'Source/image ledger changed'
    assert len(m['pages'])==231 and len(m['assets'])==3
    by_id={l['id']:l for l in m['lines']};by_source={s:b for b in m['blocks'] for s in b['source']}
    hs=[b for b in m['blocks'] if b['kind']=='heading']
    assert [(b['text'],b['level']) for b in hs]==[(s,1) for s in LABELS]
    assert [by_id[b['source'][0]]['page'] for b in hs]==PAGES
    bad=[b for b in old['blocks'] if b['kind']=='heading' and
         122<=by_id[b['source'][0]]['page']<=125 and b['id']!='b1785']
    assert len(bad)==56
    assert all(by_source[s]['kind'] in ('paragraph','quote') for b in bad for s in b['source'])
    # Specific observed wrapped prose/dialogue must be reconstructed, not just
    # retagged into one paragraph per formerly false heading.
    assert by_source['p122-l15']['id']==by_source['p122-l16']['id']
    assert by_source['p122-l17']['id']==by_source['p122-l18']['id']
    assert by_source['p122-l17'].get('dialogue')
    assert by_source['p122-l14']['id']!=by_source['p122-l17']['id']
    assert all(f['status']=='pass' for f in audit_model(m)+audit_editorial(m))
    legacy_audit=audit_editorial(old)
    assert classify(legacy_audit)=='Intervenção necessária'
    for reason in ['explicit_level','frontmatter_role','narrative_heading','heading_density']:
        assert any(f['evidence'].get('reason')==reason for f in legacy_audit)
    with zipfile.ZipFile(bundle/'book.epub') as z:
        opf=ET.fromstring(z.read('EPUB/package.opf'))
        manifest={e.get('id'):e.get('href') for e in opf.findall('o:manifest/o:item',NS)}
        spine=[manifest[e.get('idref')] for e in opf.findall('o:spine/o:itemref',NS)]
        assert len(spine)==9
        bodies=[ET.fromstring(z.read('EPUB/'+n)).find('h:body',NS) for n in spine]
        assert all(not bodies[i].findall('h:h1',NS) and not bodies[i].findall('h:h2',NS) for i in [0,8])
        assert [[''.join(e.itertext()) for e in body.findall('h:h1',NS)] for body in bodies[1:8]]==[[s] for s in LABELS]
        assert all(not b.findall('h:h2',NS) for b in bodies)
        actual=[(e.get('id'),''.join(e.itertext())) for body in bodies for e in body]
        assert actual==[(b['id'],b['text']) for b in m['blocks']]
        roots=ET.fromstring(z.read('EPUB/nav.xhtml')).findall('.//h:nav/h:ol/h:li',NS)
        assert len(roots)==9 and all(not e.findall('h:ol/h:li',NS) for e in roots)
        for a in ET.fromstring(z.read('EPUB/nav.xhtml')).findall('.//h:a',NS):
            name,ident=a.get('href').split('#');assert name in spine
            assert any(e.get('id')==ident for e in ET.fromstring(z.read('EPUB/'+name)).iter())
        assert len([e for body in bodies for e in body.findall('.//h:img',NS)])==3
    for code in ['source_accounting','source_text','source_images_semantics','serialized_text','serialized_images_semantics','package_navigation_css','editorial_structure']:
        assert all(f['status']=='pass' for f in r['findings'] if f['code']==code),code
    checker=next(f for f in r['findings'] if f['code']=='epubcheck')['evidence']['report']['checker']
    assert all(checker[k]==0 for k in ['nError','nFatal','nWarning','nUsage'])
    result=dict(source_sha256=SOURCE,pages=231,chapter_pages=PAGES,main_chapters=7,xhtmls=9,
                false_headings_removed=56,images=3,source_ledger_and_images_identical=True,
                paragraphs_and_dialogue_samples=True,old_bundle_state=classify(legacy_audit),
                old_bundle_findings=dict(Counter(f['evidence'].get('reason','other') for f in legacy_audit)),
                state=r['state'],epub_sha256=r['epub_sha256'],
                epubcheck={k:checker[k] for k in ['checkerVersion','nFatal','nError','nWarning','nUsage']})
    print(json.dumps(result,ensure_ascii=False,indent=2));return result

if __name__=='__main__':check(Path(sys.argv[1]),Path(sys.argv[2]))
