"""Acceptance on real public-domain prose re-typeset as simple PDFs.
Sources stay outside the repository. No automatic network or uploads.
Usage: PYTHONPATH=. python acceptance/run_public_texts.py INPUT_DIRECTORY OUTPUT_DIRECTORY JAR
INPUT_DIRECTORY must contain alice.txt and pride.txt from the URLs in evidence.md.
"""
import json
import re
import sys
from pathlib import Path
from hashlib import sha256
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit
from book_epub.pipeline import convert

inputs, root, jar = map(Path, sys.argv[1:])
root.mkdir(exist_ok=False, parents=True)
results=[]
for filename,title,author,start in [('alice','Alice’s Adventures in Wonderland','Lewis Carroll','CHAPTER I.\nDown the Rabbit-Hole'),('pride','Pride and Prejudice','Jane Austen','Chapter I.]')]:
    raw=(inputs/(filename+'.txt')).read_bytes()
    text=raw.decode('utf-8-sig')
    first=text.index(start)
    second=text.index('CHAPTER II.',first+len(start))
    sections=[text[first+len(start):second],text[second+len('CHAPTER II.'):]]
    cs=[]
    for index,section in enumerate(sections,1):
        paragraphs=[' '.join(p.split()) for p in re.split(r'\n\s*\n',section.strip())]
        # Alice chapter II has a standalone subtitle. Excerpts use first two prose paragraphs.
        paragraphs=[p for p in paragraphs if len(p)>100 and not p.startswith('[')][:2]
        cs.append((f'Chapter {index}',paragraphs))
    pdf=root/(filename+'.pdf');c=canvas.Canvas(str(pdf),pagesize=(612,792),invariant=1)
    expected=[]
    for heading,paras in cs:
        c.setFont('Times-Bold',18);c.drawString(72,720,heading);y=675
        expected.append(heading)
        for para in paras:
            expected.append(para);c.setFont('Times-Roman',12)
            for line in simpleSplit(para,'Times-Roman',12,468):
                c.drawString(72,y,line);y-=16
            y-=18
        c.showPage()
    c.save()
    out=root/filename
    report=convert(pdf,out,title=title,author=author,language='en',command=['java','-jar',str(jar)])
    model=json.loads((out/'model.json').read_text())
    exact=[b['text'] for b in model['blocks']]==expected
    check=next(f for f in report['findings'] if f['code']=='epubcheck')
    results.append(dict(source=filename,source_sha256=sha256(raw).hexdigest(),pdf_sha256=sha256(pdf.read_bytes()).hexdigest(),state=report['state'],expected_paragraphs=4,exact_blocks=exact,blocks=len(model['blocks']),epubcheck=check['status'],findings=sorted({f['code'] for f in report['findings'] if f['status']!='pass'})))
(root/'results.json').write_text(json.dumps(results,indent=2))
print(json.dumps(results,indent=2))
if not all(r['exact_blocks'] and r['epubcheck']=='pass' for r in results):
    raise SystemExit(1)
