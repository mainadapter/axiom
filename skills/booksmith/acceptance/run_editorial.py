"""Authored editorial acceptance; outputs are private scratch files, never repository inputs.
Usage: PYTHONPATH=. python acceptance/run_editorial.py NEW_OUTPUT /path/epubcheck.jar
"""
import json
from pathlib import Path
import sys
import zipfile
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader,simpleSplit
from book_epub.pipeline import convert,refine
from book_epub.validate import audit_model

root=Path(sys.argv[1]);root.mkdir(parents=True,exist_ok=False)
jar=Path(sys.argv[2]);source=root/'editorial.pdf'
c=canvas.Canvas(str(source),pagesize=(600,800),invariant=1)
art=Image.new('RGB',(120,160),'#153e52')
for x in range(30,90):
    for y in range(40,120):art.putpixel((x,y),(232,182,90))
c.drawImage(ImageReader(art),0,0,600,800);c.showPage()
c.setFont('Times-Roman',12);c.drawCentredString(300,740,'THE GARDEN')
c.drawCentredString(300,700,'I')
paragraph='The gate had been open for years, but nobody remembered who had left it so. A narrow path led from the gate to a quiet garden, where the windows of the old house reflected the evening light.'
y=660
for i,line in enumerate(simpleSplit(paragraph,'Times-Roman',12,450)):
    c.drawString(68 if i==0 else 50,y,line);y-=16
turns=['—Hello, said the visitor.','—Goodbye, answered the gardener.']
for turn in turns:c.drawString(68,y,turn);y-=16
c.drawImage(ImageReader(art),240,390,90,120)
c.drawCentredString(300,340,'II')
c.setFont('Times-Italic',12);c.drawString(50,300,'An italic memory.')
c.setFont('Times-Roman',12);c.drawCentredString(300,260,'* * *')
c.drawString(50,220,'The garden remained quiet.');c.showPage()
c.setFont('Times-Bold',20);c.drawString(80,740,'A second beginning')
c.setFont('Times-Bold',16);c.drawString(80,690,'The small door')
c.setFont('Times-Roman',12);c.drawString(80,640,'A new paragraph at a different page margin.')
c.showPage();c.save()
report=convert(source,root/'v1',title='The garden',language='en',command=['java','-jar',str(jar)])
m=json.loads((root/'v1/model.json').read_text())
expected=['','THE GARDEN','I',paragraph,*turns,'','II','An italic memory.','* * *','The garden remained quiet.','A second beginning','The small door','A new paragraph at a different page margin.']
if [b['text'] for b in m['blocks']]!=expected:
    raise ValueError('Authored ground truth mismatch')
if not all(f['status']=='pass' for f in audit_model(m)):raise ValueError('Source audit failed')
revised=refine(root/'v1',root/'v2',paragraph_gap=1,command=['java','-jar',str(jar)])
with zipfile.ZipFile(root/'v1/book.epub') as a,zipfile.ZipFile(root/'v2/book.epub') as b:
    changes=[n for n in a.namelist() if a.read(n)!=b.read(n)]
if changes!=['EPUB/style.css']:raise ValueError(changes)
result=dict(state=report['state'],blocks=len(expected),exact_authored_blocks=True,images=len(m['assets']),
            headings=[dict(text=b['text'],level=b['level']) for b in m['blocks'] if b['kind']=='heading'],
            epubcheck=next(f for f in report['findings'] if f['code']=='epubcheck')['status'],refinement_changed=changes,
            model_unchanged=(root/'v1/model.json').read_bytes()==(root/'v2/model.json').read_bytes())
(root/'results.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
if result['epubcheck']!='pass':raise SystemExit(1)
