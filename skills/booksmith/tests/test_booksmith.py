"""Independent authored fixtures and package corruption regressions."""
import base64
import copy
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile
from xml.etree import ElementTree as ET

from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader, simpleSplit

from book_epub.pipeline import convert,refine,report_markdown
from book_epub.package import css,write_epub
from book_epub.validate import audit_model,validate

JAR=os.environ.get('EPUBCHECK_JAR')
COMMAND=['java','-jar',JAR] if JAR else ['/missing/epubcheck']


class BooksmithTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        self.src=self.root/'source.pdf'
    def tearDown(self): self.tmp.cleanup()
    def convert(self, draw):
        c=canvas.Canvas(str(self.src),pagesize=(600,800),invariant=1)
        draw(c)
        c.save()
        report=convert(self.src,self.root/'v1',title='Booksmith fixture',language='en',command=COMMAND)
        self.model=json.loads((self.root/'v1/model.json').read_text())
        self.report=report
        return report
    def members(self):
        with zipfile.ZipFile(self.root/'v1/book.epub') as z:return {n:z.read(n) for n in z.namelist()}
    def baseline(self,c):
        c.setFont('Times-Bold',20);c.drawString(50,740,'Chapter 1')
        c.setFont('Times-Roman',12);c.drawString(50,700,'Ordinary paragraph before the illustration.')
        c.drawString(50,400,'Ordinary paragraph after the illustration.')
    def test_inline_style_exact_and_corruption(self):
        def draw(c):
            c.setFont('Times-Bold',20);c.drawString(50,740,'Chapter 1')
            x=50;y=690
            for font,text in [('Times-Roman','Ordinary '),('Times-Italic','italic'),('Times-Roman',' and '),('Times-BoldItalic','both'),('Times-Roman',' words.')]:
                c.setFont(font,12);c.drawString(x,y,text);x+=c.stringWidth(text,font,12)
            c.drawString(50,650,'Another paragraph.')
        self.convert(draw)
        p=self.model['blocks'][1]
        self.assertEqual(p['text'],'Ordinary italic and both words.')
        self.assertTrue(all(f['status']=='pass' for f in audit_model(self.model)))
        members=self.members()
        chapter=members['EPUB/chapter-0001.xhtml']
        self.assertIn(b'<em> italic</em>',chapter)
        self.assertIn(b'<strong><em> both</em></strong>',chapter)
        bad=dict(members);bad['EPUB/chapter-0001.xhtml']=chapter.replace(b'<em> italic</em>',b' italic')
        write_epub(self.root/'bad.epub',bad)
        self.assertTrue(any(f['status']=='fail' for f in validate(self.root/'bad.epub',self.model,'generic',css()[1],command=['/missing/check'])))
        bad_model=copy.deepcopy(self.model)
        next(s for s in bad_model['blocks'][1]['spans'] if s.get('italic'))['italic']=False
        self.assertTrue(any(f['status']=='fail' for f in audit_model(bad_model)))
    def test_uppercase_romans_and_nested_navigation(self):
        def draw(c):
            c.setFont('Times-Roman',12)
            c.drawCentredString(300,740,'THE GARDEN')
            c.drawCentredString(300,700,'I')
            c.drawString(50,660,'A long ordinary paragraph marks the normal body style.')
            c.drawString(50,620,'Another ordinary paragraph marks the left margin.')
            c.drawCentredString(300,560,'II')
            c.drawString(50,520,'A final paragraph under the second section.')
        self.convert(draw)
        hs=[(b['text'],b['level']) for b in self.model['blocks'] if b['kind']=='heading']
        self.assertEqual(hs,[('THE GARDEN',1),('I',2),('II',2)])
        members=self.members()
        self.assertEqual(len([n for n in members if n.startswith('EPUB/chapter-')]),1)
        ns={'h':'http://www.w3.org/1999/xhtml'}
        nav=ET.fromstring(members['EPUB/nav.xhtml'])
        self.assertEqual(len(nav.findall('.//h:ol/h:li/h:ol/h:li',ns)),2)
        bad=dict(members)
        bad['EPUB/chapter-0001.xhtml']=bad['EPUB/chapter-0001.xhtml'].replace(b'<h2',b'<h1').replace(b'</h2>',b'</h1>')
        write_epub(self.root/'bad.epub',bad)
        self.assertTrue(any(f['status']=='fail' for f in validate(self.root/'bad.epub',self.model,'generic',css()[1],command=['/missing/check'])))
    def test_dialogue_separate_wrapped_lines_without_extra_spacing(self):
        def draw(c):
            c.setFont('Times-Bold',20);c.drawString(50,740,'Chapter 1')
            c.setFont('Times-Roman',12)
            for x,y,t in [(68,700,'– The first speaker begins and continues'),(50,684,'on the next ordinary wrapped line.'),(68,668,'– A second speaker answers.'),(68,652,'– The third speaker replies.')]:
                c.drawString(x,y,t)
        self.convert(draw)
        self.assertEqual([b['text'] for b in self.model['blocks'][1:]],[
            '– The first speaker begins and continues on the next ordinary wrapped line.',
            '– A second speaker answers.','– The third speaker replies.'])
        self.assertEqual(sum(bool(b.get('dialogue')) for b in self.model['blocks']),3)
    def test_typography_hierarchy(self):
        def draw(c):
            c.setFont('Times-Bold',22);c.drawString(50,740,'A quiet beginning')
            c.setFont('Times-Bold',16);c.drawString(50,690,'An early memory')
            c.setFont('Times-Roman',12);c.drawString(50,640,'Ordinary text in a conventional book.')
            c.drawString(50,600,'Another ordinary paragraph.')
        self.convert(draw)
        self.assertEqual([b['level'] for b in self.model['blocks'] if b['kind']=='heading'],[1,2])
    def test_page_local_body_margins(self):
        paragraphs=['This deliberately long authored paragraph spans enough lines to establish the body margin on this page. It continues with several ordinary words about a quiet garden and the old house beyond its gate.','The next paragraph begins with a conventional first line indentation. It has several wrapped lines as well, so that a normal indentation is not mistaken for a block quotation in this fixture.']
        def draw(c):
            for page,left in enumerate([50,95]):
                c.setFont('Times-Bold',20);c.drawString(left,740,'Chapter '+str(page+1))
                c.setFont('Times-Roman',12);y=700
                for p in paragraphs:
                    for i,line in enumerate(simpleSplit(p,'Times-Roman',12,380)):
                        c.drawString(left+18 if i==0 else left,y,line);y-=16
                c.showPage()
        self.convert(draw)
        self.assertEqual([b['text'] for b in self.model['blocks'] if b['kind']=='paragraph'],paragraphs*2)
        self.assertFalse(any(f['code']=='indented_run' for f in self.report['findings']))
    def test_image_preserved_manifest_order_hash_and_refine(self):
        def draw(c):
            self.baseline(c)
            c.drawImage(ImageReader(Image.new('RGB',(40,30),'blue')),50,500,80,60)
        self.convert(draw)
        self.assertIsNotNone(self.report['epub_sha256'])
        self.assertEqual([b['kind'] for b in self.model['blocks']],['heading','paragraph','image','paragraph'])
        self.assertTrue(all(f['status']=='pass' for f in audit_model(self.model)))
        a=self.model['assets'][0];members=self.members()
        self.assertEqual(members['EPUB/images/p1-img1.png'],base64.b64decode(a['data_base64']))
        self.assertEqual((a['width'],a['height']),(160,120))
        if JAR:self.assertEqual(self.report['state'],'Aprovado',self.report['findings'])
        refine(self.root/'v1',self.root/'v2',paragraph_gap=1.2,command=COMMAND)
        with zipfile.ZipFile(self.root/'v2/book.epub') as z:
            self.assertEqual([n for n in members if members[n]!=z.read(n)],['EPUB/style.css'])
        self.assertEqual((self.root/'v1/model.json').read_bytes(),(self.root/'v2/model.json').read_bytes())
        bad=dict(members);bad['EPUB/images/p1-img1.png']=b'corrupted'
        write_epub(self.root/'bad.epub',bad)
        self.assertTrue(any(f['status']=='fail' for f in validate(self.root/'bad.epub',self.model,'generic',css()[1],command=['/missing/check'])))
        for alteration in ('drop','duplicate','move'):
            model=copy.deepcopy(self.model)
            if alteration=='drop':model['blocks'].pop(2)
            elif alteration=='duplicate':model['blocks'].append(copy.deepcopy(model['blocks'][2]))
            else:model['blocks'].append(model['blocks'].pop(2))
            self.assertTrue(any(f['status']=='fail' for f in audit_model(model)),alteration)
    def test_cover_image_only_page_followed_by_prose(self):
        def draw(c):
            c.drawImage(ImageReader(Image.new('RGB',(60,80),'green')),0,0,600,800)
            c.showPage();self.baseline(c)
        self.convert(draw)
        self.assertEqual(len(self.model['assets']),1)
        self.assertTrue(self.model['assets'][0]['cover'])
        self.assertIsNotNone(self.report['epub_sha256'])
        self.assertIn(b'cover-image',self.members()['EPUB/package.opf'])
    def test_cover_reflows_at_two_portrait_widths(self):
        import fitz
        for source_height in (800,900,1200):
            with self.subTest(source_height=source_height):
                src=self.root/f'cover-{source_height}.pdf'
                c=canvas.Canvas(str(src),pagesize=(600,source_height),invariant=1)
                c.drawImage(ImageReader(Image.new('RGB',(60,source_height//10),'green')),0,0,600,source_height)
                c.showPage();self.baseline(c);c.save()
                out=self.root/f'cover-{source_height}'
                report=convert(src,out,title='Cover ratios',language='en',command=COMMAND)
                self.assertIsNotNone(report['epub_sha256'])
                for width,height in [(360,640),(768,900)]:
                    with fitz.open(out/'book.epub') as doc:
                        doc.layout(width=width,height=height,fontsize=12)
                        images=doc[0].get_image_info()
                        self.assertEqual(len(images),1)
                        x0,y0,x1,y1=images[0]['bbox']
                        self.assertTrue(0<=x0<x1<=width and 0<=y0<y1<=height,(source_height,width,(x0,y0,x1,y1)))
                        self.assertEqual(doc.page_count,2)

    def test_interior_scan_still_blocked(self):
        def draw(c):
            self.baseline(c);c.showPage()
            c.drawImage(ImageReader(Image.new('RGB',(60,80),'white')),0,0,600,800)
        self.convert(draw)
        self.assertEqual(self.report['state'],'Intervenção necessária')
        self.assertTrue(any(f['code']=='possible_scan' for f in self.report['findings']))
    def test_image_text_overlap_blocked(self):
        def draw(c):
            self.baseline(c);c.drawImage(ImageReader(Image.new('RGB',(40,30),'blue')),45,690,200,40)
        self.convert(draw)
        self.assertEqual(self.report['state'],'Intervenção necessária')
        self.assertTrue(any(f['code']=='image_composition' for f in self.report['findings']))
    def test_failed_image_capture_blocked(self):
        with patch('book_epub.images.Image.open',side_effect=OSError('broken')):
            self.convert(lambda c:(self.baseline(c),c.drawImage(ImageReader(Image.new('RGB',(20,20),'red')),50,500,60,60)))
        self.assertEqual(self.report['state'],'Intervenção necessária')
        self.assertFalse((self.root/'v1/book.epub').exists())
    def test_separator_preserves_original_glyphs(self):
        def draw(c):
            self.baseline(c);c.drawCentredString(300,600,'* * *')
        self.convert(draw)
        self.assertEqual(next(b['text'] for b in self.model['blocks'] if b['kind']=='separator'),'* * *')
    def test_allcaps_inside_prose_is_not_heading(self):
        def draw(c):
            self.baseline(c);c.drawString(50,684,'THIS IS AN ORDINARY WRAPPED LINE')
            c.drawString(50,668,'continuing the preceding ordinary paragraph.')
        self.convert(draw)
        self.assertEqual(sum(b['kind']=='heading' for b in self.model['blocks']),1)
    def test_diagnostics_group_examples_and_keep_ledger(self):
        self.convert(self.baseline)
        report=copy.deepcopy(self.report)
        findings=[dict(code='paragraph_boundary',status='inconclusive',impact='review',detail='A repeated ambiguity.',evidence=dict(source=['p1-l2'],page=1)) for _ in range(1000)]
        from book_epub.pipeline import diagnostic_summary
        report['findings']=findings;report['summary']=diagnostic_summary(findings,self.model)
        md=report_markdown(report)
        self.assertEqual(len(report['findings']),1000)
        self.assertEqual(len(report['summary']),1)
        self.assertLess(len(md),2000)
        self.assertEqual(len(report['summary'][0]['examples']),3)
        self.assertIn('p1-l2',md)
    def test_heading_prefix_in_body_sentence_is_not_a_chapter(self):
        sentence='Chapter 2 was the hardest part of the story to understand.'
        def draw(c):
            self.baseline(c);c.drawString(50,650,sentence)
        self.convert(draw)
        self.assertEqual([b['text'] for b in self.model['blocks'] if b['kind']=='heading'],['Chapter 1'])
        self.assertIn(sentence,[b['text'] for b in self.model['blocks'] if b['kind']=='paragraph'])
    def test_unspaced_em_dash_turns_are_separate(self):
        turns=['—Hello, he said without a question or a full stop','—Goodbye, she replied without pausing']
        def draw(c):
            self.baseline(c)
            for y,t in zip([620,604],turns):c.drawString(50,y,t)
        self.convert(draw)
        self.assertTrue(all(t in [b['text'] for b in self.model['blocks']] for t in turns))
    def test_sentence_ending_page_boundary_requires_review(self):
        def draw(c):
            self.baseline(c);c.drawString(50,100,'The first sentence ends here.')
            c.showPage();c.setFont('Times-Roman',12)
            c.drawString(50,740,'The second sentence continues the same paragraph.')
            c.drawString(50,650,'Another independent paragraph.')
        self.convert(draw)
        self.assertTrue(any(f['code']=='page_boundary' for f in self.report['findings']))
        self.assertEqual(self.report['state'],'Revisão recomendada')
    def test_extra_serialized_image_is_rejected(self):
        def draw(c):
            self.baseline(c);c.drawImage(ImageReader(Image.new('RGB',(20,20),'red')),50,500,60,60)
        self.convert(draw);members=self.members()
        members['EPUB/chapter-0001.xhtml']=members['EPUB/chapter-0001.xhtml'].replace(b'</p>',b'<img src="images/p1-img1.png" alt=""/></p>',1)
        write_epub(self.root/'extra.epub',members)
        self.assertTrue(any(f['status']=='fail' for f in validate(self.root/'extra.epub',self.model,'generic',css()[1],command=['/missing/check'])))

    def test_visible_bleed_is_clipped_and_recorded(self):
        def draw(c):
            c.drawImage(ImageReader(Image.new('RGB',(60,80),'green')),-2,-2,604,804)
            c.showPage();self.baseline(c)
        self.convert(draw)
        a=self.model['assets'][0]
        self.assertEqual(a['bbox'],[0,0,600,800])
        self.assertLess(a['source_bbox'][0],0)
        self.assertEqual(a['width'],1200)
        self.assertIsNotNone(self.report['epub_sha256'])
    def test_masked_image_preserves_background(self):
        im=Image.new('RGBA',(20,20),(255,0,0,0))
        for x in range(10):
            for y in range(20):im.putpixel((x,y),(0,0,255,255))
        def draw(c):
            self.baseline(c);c.drawImage(ImageReader(im),50,500,60,60,mask='auto')
        self.convert(draw)
        a=self.model['assets'][0]
        with Image.open(io.BytesIO(base64.b64decode(a['data_base64']))) as output:
            self.assertEqual(output.getpixel((20,60)),(0,0,255))
            self.assertEqual(output.getpixel((100,60)),(255,255,255))
    def test_rotated_image_preserves_visible_orientation(self):
        im=Image.new('RGB',(20,20),'red')
        for x in range(10):
            for y in range(20):im.putpixel((x,y),(0,0,255))
        def draw(c):
            self.baseline(c);c.saveState();c.translate(150,500);c.rotate(90)
            c.drawImage(ImageReader(im),0,0,60,60);c.restoreState()
        self.convert(draw)
        a=self.model['assets'][0]
        with Image.open(io.BytesIO(base64.b64decode(a['data_base64']))) as output:
            self.assertEqual(output.getpixel((60,20)),(255,0,0))
            self.assertEqual(output.getpixel((60,100)),(0,0,255))
    def test_repeated_raster_resource_keeps_both_occurrences(self):
        im=ImageReader(Image.new('RGB',(20,20),'red'))
        def draw(c):
            self.baseline(c);c.drawImage(im,50,500,60,60);c.drawImage(im,150,500,60,60)
        self.convert(draw)
        self.assertEqual(len(self.model['assets']),2)
        self.assertTrue(all(f['status']=='pass' for f in audit_model(self.model)))
    def test_failed_serialized_validation_withholds_package(self):
        with patch('book_epub.pipeline.validate',return_value=[dict(code='broken',status='fail',impact='blocking',detail='proven defect',evidence={})]):
            self.convert(self.baseline)
        self.assertEqual(self.report['state'],'Intervenção necessária')
        self.assertFalse((self.root/'v1/book.epub').exists())
        self.assertIsNotNone(self.report['rejected_epub_sha256'])

    def test_legacy_bundle_refinement_keeps_model_bytes(self):
        # Generate an actual 0.1.0 bundle with the unchanged historical module.
        import subprocess
        self.src=self.root/'legacy.pdf'
        c=canvas.Canvas(str(self.src),pagesize=(600,800),invariant=1);self.baseline(c);c.save()
        legacy=self.root/'historical'
        (legacy/'book_epub').mkdir(parents=True)
        for filename in ('__init__.py','__main__.py','common.py','extract.py','package.py','pipeline.py','validate.py'):
            data=subprocess.check_output(['git','show','856e4a70e2312568161876cb3737ba4622432cb7:skills/book-to-epub/book_epub/'+filename],cwd=Path(__file__).resolve().parents[3])
            (legacy/'book_epub'/filename).write_bytes(data)
        command=['python3','-m','book_epub','convert',str(self.src),str(self.root/'old'),'--title','Legacy','--language','en']
        result=subprocess.run(command,cwd=legacy,capture_output=True)
        self.assertIn(result.returncode,(0,1))
        refine(self.root/'old',self.root/'new',paragraph_gap=1,command=COMMAND)
        self.assertEqual((self.root/'old/model.json').read_bytes(),(self.root/'new/model.json').read_bytes())

if __name__=='__main__':unittest.main()
