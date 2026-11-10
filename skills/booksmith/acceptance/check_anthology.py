"""Private full-book acceptance against an editorial oracle, not inferred helpers.

Usage: python acceptance/check_anthology.py BUNDLE [PREVIOUS_BUNDLE]
No source text or conversion bundle is written to the repository.
"""
import hashlib
import json
from pathlib import Path
import sys
import zipfile
from xml.etree import ElementTree as ET

TITLES = ['O LIMITE DO POSSÍVEL', 'UM FRAGMENTO DE GELO', 'O FOGO ETERNO',
          'UM PEQUENO SACRIFÍCIO', 'A ESPADA DO DESTINO', 'ALGO MAIS']
COUNTS = [8, 9, 4, 10, 8, 9]
PAGES = [4, 54, 81, 114, 152, 194]
ROMANS = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X']
SOURCE = 'a66781bdf21e4655ec577cc096608b282bd08ca49a01e523f5dacd214b330861'
NS = {'h':'http://www.w3.org/1999/xhtml','o':'http://www.idpf.org/2007/opf'}

def check(bundle, previous=None):
    m=json.loads((bundle/'model.json').read_text())
    r=json.loads((bundle/'report.json').read_text())
    assert m['source_sha256']==SOURCE, 'Unexpected private source; oracle is source-specific'
    hs=[b for b in m['blocks'] if b['kind']=='heading']
    expected=[]
    for title,count in zip(TITLES,COUNTS):expected.extend([(title,1)]+[(roman,2) for roman in ROMANS[:count]])
    assert [(b['text'],b['level']) for b in hs]==expected, 'Editorial headings differ from oracle'
    by_line={l['id']:l for l in m['lines']}
    assert [by_line[b['source'][0]]['page'] for b in hs if b['level']==1]==PAGES
    with zipfile.ZipFile(bundle/'book.epub') as z:
        opf=ET.fromstring(z.read('EPUB/package.opf'))
        manifest={e.get('id'):e.get('href') for e in opf.findall('o:manifest/o:item',NS)}
        spine=[manifest[e.get('idref')] for e in opf.findall('o:spine/o:itemref',NS)]
        assert len(spine)==8, 'Expected front matter, six tales and publishing information'
        bodies=[ET.fromstring(z.read('EPUB/'+n)).find('h:body',NS) for n in spine]
        front=bodies[0]
        assert front.findall('h:h1',NS)==[] and front.findall('h:h2',NS)==[]
        front_ids={e.get('id') for e in front}
        assert all(b.get('content_role')=='frontmatter' for b in m['blocks'] if b['id'] in front_ids)
        assert [by_line[s]['page'] for b in m['blocks'] if b['id'] in front_ids for s in b['source']]==[2]*3+[3]*7
        back=bodies[-1]
        back_ids={e.get('id') for e in back}
        assert all(b.get('content_role')=='backmatter' for b in m['blocks'] if b['id'] in back_ids)
        assert {by_line[s]['page'] for b in m['blocks'] if b['id'] in back_ids for s in b['source']}=={231,232}
        narrative_lengths=[]
        for body,title,count in zip(bodies[1:],TITLES,COUNTS):
            assert [''.join(e.itertext()) for e in body.findall('h:h1',NS)]==[title]
            assert [''.join(e.itertext()) for e in body.findall('h:h2',NS)]==ROMANS[:count]
            narrative_lengths.append(sum(len(''.join(e.itertext())) for e in body))
        assert min(narrative_lengths)>1000, 'Narrative was concentrated or emptied'
        nav=ET.fromstring(z.read('EPUB/nav.xhtml'))
        roots=nav.findall('.//h:nav/h:ol/h:li',NS)
        assert len(roots)==8
        assert [len(e.findall('h:ol/h:li',NS)) for e in roots]==[0]+COUNTS+[0]
        for link in nav.findall('.//h:a',NS):
            name,ident=link.get('href').split('#')
            assert name in spine
            assert any(e.get('id')==ident for e in ET.fromstring(z.read('EPUB/'+name)).iter())
        actual=[(e.get('id'),''.join(e.itertext())) for body in bodies for e in body]
        assert actual==[(b['id'],b['text']) for b in m['blocks']], 'Serialized text/order mismatch'
        assert len(m['assets'])==2
        assert len([e for body in bodies for e in body.findall('.//h:img',NS)])==2
        for a in m['assets']:
            assert hashlib.sha256(z.read('EPUB/images/'+a['id']+'.png')).hexdigest()==a['sha256']
    for code in ['source_accounting','source_text','source_images_semantics','serialized_text','serialized_images_semantics','package_navigation_css','editorial_structure']:
        fs=[f for f in r['findings'] if f['code']==code]
        assert fs and all(f['status']=='pass' for f in fs), code
    checker=next(f for f in r['findings'] if f['code']=='epubcheck')['evidence']['report']['checker']
    assert all(checker[k]==0 for k in ['nError','nFatal','nWarning','nUsage'])
    if previous:
        old=json.loads((previous/'model.json').read_text())
        assert old['lines']==m['lines'], 'Source ledger changed'
        assert old['assets']==m['assets'], 'Image bytes/provenance changed'
        assert [s for b in old['blocks'] for s in b['source']]==[s for b in m['blocks'] for s in b['source']]
        # Heading/pre-text paragraph boundaries may change; every retained character must remain.
        compact=lambda model: ''.join(c for b in model['blocks'] for c in b['text'] if not c.isspace())
        assert compact(old)==compact(m), 'Retained textual characters changed'
    result=dict(source_sha256=SOURCE, pages=len(m['pages']), state=r['state'], chapters=len(spine),
                roman_counts=COUNTS, narrative_characters=narrative_lengths, images=2,
                editorial_oracle=True, previous_source_ledger_and_images_identical=bool(previous),
                epubcheck={k:checker[k] for k in ['checkerVersion','nFatal','nError','nWarning','nUsage']},
                epub_sha256=r['epub_sha256'])
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return result

if __name__=='__main__':check(Path(sys.argv[1]),Path(sys.argv[2]) if len(sys.argv)>2 else None)
