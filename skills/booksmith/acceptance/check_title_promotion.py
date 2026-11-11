"""Five PRIVATE PDF regressions; literal structural oracles, never runtime inputs.

PYTHONPATH=. python acceptance/check_title_promotion.py BASELINE_ROOT NEW_ROOT
Roots contain bundles 1..5 from the same original PDFs. No source PDFs, book
models or book prose belong in Git. stdout contains only bounded audit metadata.
First-book hierarchy remains a preservation regression, not a new full oracle.
"""
import json
from pathlib import Path
import sys
import zipfile
from xml.etree import ElementTree as ET
from collections import Counter
from book_epub.validate import audit_model, audit_editorial
from book_epub.package import chapters
from check_anthology import TITLES,COUNTS,ROMANS

SOURCES=[
'950d810c1d6eee93ae7c79d7662c17f635fe465fa85356b3e7440d38b35c5d25',
'a66781bdf21e4655ec577cc096608b282bd08ca49a01e523f5dacd214b330861',
'1ea6d7fc34a67469c6fc27177c8a16638ee7d7dab455dd2c12048b136b39d3dd',
'a01d93268676bd5bb886f450c05e0d0adb12bd229f6ad575a58d0a3eadb24fa7',
'705ad221ff3b3a9ef96125c18b2a6a0a82d63eddf14b9753fc0c399b3529940b']
LABELS=['CAPÍTULO '+s for s in ['PRIMEIRO','SEGUNDO','TERCEIRO','QUARTO','QUINTO','SEXTO','SÉTIMO']]
PAGES={3:[4,33,57,83,122,154,188],4:[6,36,75,107,139,175,196],5:[6,39,81,110,140,180,216]}
NS={'h':'http://www.w3.org/1999/xhtml'}


def load(path,name):return json.loads((path/name).read_text())


def check(before,after):
    results=[]
    for n,pages,images in [(1,190,3),(2,232,2),(3,231,3),(4,227,6),(5,264,4)]:
        root=after/str(n);m=load(root,'model.json');old=load(before/str(n),'model.json');r=load(root,'report.json')
        assert m['source_sha256']==old['source_sha256']==SOURCES[n-1]
        assert len(m['pages'])==pages and len(m['assets'])==images
        for key in ['lines','pages','assets','image_sources']:
            assert m[key]==old[key],(n,key,'source extraction/image change')
        hs=[(b['text'],b['level']) for b in m['blocks'] if b['kind']=='heading']
        old_hs=[(b['text'],b['level']) for b in old['blocks'] if b['kind']=='heading']
        if n==1:assert hs==old_hs and len(hs)==62
        if n==2:
            expected=[]
            for t,count in zip(TITLES,COUNTS):expected.extend([(t,1)]+[(r,2) for r in ROMANS[:count]])
            assert hs==expected
        if n in PAGES:
            by_id={l['id']:l for l in m['lines']}
            assert hs==[(t,1) for t in LABELS]
            assert [by_id[b['source'][0]]['page'] for b in m['blocks'] if b['kind']=='heading']==PAGES[n]
        if n<5:
            # Text, paragraph joins, emphasis, hierarchy and roles must remain
            # byte-for-byte equivalent at the block level, apart from rationale.
            def content(blocks):return [{k:v for k,v in b.items() if k!='heading_evidence'} for b in blocks]
            assert content(m['blocks'])==content(old['blocks']),n
        else:
            assert old_hs==[(t,1) for t in LABELS]+[('15-08917 CDD-891.8',1)]
            target=next(b for b in m['blocks'] if 'p264-l8' in b['source'])
            assert target['kind']=='paragraph' and target['text']=='15-08917 CDD-891.8'
            assert target['spans']==next(b for b in old['blocks'] if 'p264-l8' in b['source'])['spans']
            def text_content(blocks):return [{k:v for k,v in b.items() if k not in ('kind','level','heading_evidence')} for b in blocks]
            assert text_content(m['blocks'])==text_content(old['blocks'])
            assert len(chapters(old))==9 and len(chapters(m))==8
            assert set(m['editorial_structure']['pending_titles'])=={'p264-l8'}
            fs=[f for f in audit_editorial(m) if f['evidence'].get('decision')=='deferred']
            assert len(fs)==1 and fs[0]['evidence']['source']==['p264-l8']
        assert all(f['status']=='pass' for f in audit_model(m))
        assert not [f for f in r['findings'] if f['status']=='fail']
        assert not [f for f in r['findings'] if f['code']=='word_spacing' and f['status']=='fail']
        def spacing(report):
            return Counter((f['status'],f['evidence'].get('reason','aligned')) for f in report['findings'] if f['code']=='word_spacing')
        assert spacing(r)==spacing(load(before/str(n),'report.json')),n
        for code in ['source_accounting','source_text','source_word_boundaries','source_images_semantics',
                     'serialized_text','serialized_images_semantics','package_navigation_css']:
            fs=[f for f in r['findings'] if f['code']==code];assert fs and all(f['status']=='pass' for f in fs),(n,code)
        with zipfile.ZipFile(root/'book.epub') as z:
            nav=ET.fromstring(z.read('EPUB/nav.xhtml'));links=nav.findall('.//h:a',NS)
            if n==5:
                assert [a.text for a in links]==['Material pré-textual']+LABELS
                assert not any('15-08917' in a.text for a in links)
                assert b'15-08917 CDD-891.8' in z.read('EPUB/chapter-0008.xhtml')
                assert 'EPUB/chapter-0009.xhtml' not in z.namelist()
            if n<5:
                with zipfile.ZipFile(before/str(n)/'book.epub') as previous:
                    assert z.namelist()==previous.namelist()
                    assert all(z.read(name)==previous.read(name) for name in z.namelist()),n
        checker=next(f for f in r['findings'] if f['code']=='epubcheck')['evidence']['report']['checker']
        assert checker['checkerVersion']=='5.3.0'
        assert all(checker[k]==0 for k in ['nError','nFatal','nWarning','nUsage'])
        results.append(dict(book=n,pages=pages,images=images,headings_before=len(old_hs),headings_after=len(hs),
                            xhtml_before=len(chapters(old)),xhtml_after=len(chapters(m)),
                            source_and_image_ledgers_identical=True,previous_epub_identical=n<5,
                            confirmed_spacing_losses=0,spacing_review=sum(v for (s,_),v in spacing(r).items() if s=='inconclusive'),
                            state=r['state'],epub_sha256=r['epub_sha256'],
                            epubcheck={k:checker[k] for k in ['checkerVersion','nError','nFatal','nWarning','nUsage']}))
    print(json.dumps(results,ensure_ascii=False,indent=2));return results

if __name__=='__main__':check(Path(sys.argv[1]),Path(sys.argv[2]))
