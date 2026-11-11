import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image
from book_epub.common import classify, finding
from book_epub.pipeline import convert, refine
from book_epub.package import write_epub, css
from book_epub.validate import audit_model, validate

JAR = os.environ.get('EPUBCHECK_JAR')
COMMAND = ['java', '-jar', JAR] if JAR else None

def fixture(path, kind='simple'):
    c = canvas.Canvas(str(path), pagesize=(600, 800), invariant=1)
    count = 3 if kind in ('margins', 'crosspage') else 1
    for p in range(1, count+1):
        if kind == 'scan':
            c.drawImage(ImageReader(Image.new('RGB', (200, 200), 'white')), 50, 300, 200, 200)
        elif kind == 'blank':
            pass
        elif kind == 'columns':
            c.setFont('Times-Roman', 12)
            for i in range(12):
                c.drawString(50, 700-i*16, 'Left column text.')
                c.drawString(330, 700-i*16, 'Right column text.')
        else:
            if kind != 'crosspage' or p == 1:
                c.setFont('Times-Bold', 20)
                c.drawString(50, 700, f'Capítulo {p}')
            c.setFont('Times-Roman', 12)
            if kind in ('hyphen', 'knownhyphen'):
                c.drawString(50, 660, 'Uma palavra no final de linha: transfor-')
                c.drawString(50, 644, 'mação precisa permanecer fiel.')
                if kind == 'knownhyphen':
                    c.drawString(50, 600, 'A transformação está registrada.')
            elif kind == 'crosspage':
                c.drawString(50, 660, 'Este texto segue na mesma linha e continua')
                c.drawString(50, 644, 'entre páginas sem mudar o conteúdo original')
            else:
                c.drawString(50, 660, 'Primeiro parágrafo. Mantém acentos e pontuação.')
                c.drawString(50, 620, 'Segundo parágrafo independente.')
            if kind == 'footnote':
                c.setFont('Times-Roman', 8)
                c.drawString(50, 90, '1 Nota de rodapé que deve permanecer.')
            if kind == 'image':
                c.drawImage(ImageReader(Image.new('RGB', (20, 20), 'blue')), 50, 300, 50, 50)
            if kind == 'margins':
                c.setFont('Times-Roman', 10)
                c.drawString(50, 775, 'Título corrente')
                c.drawString(50, 20, str(p))
        c.showPage()
    c.save()

class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
    def tearDown(self): self.tmp.cleanup()
    def run_case(self, kind='simple', name='v1', command=COMMAND):
        src = self.root / (kind+'.pdf')
        fixture(src, kind)
        r = convert(src, self.root/name, title='Livro de teste', language='pt-BR', command=command)
        return r, json.loads((self.root/name/'model.json').read_text())
    def test_wrapped_prose_paragraph_ground_truth(self):
        from reportlab.lib.utils import simpleSplit
        chapters = json.loads((Path(__file__).parent/'fixtures/prose.json').read_text())
        src = self.root/'prose.pdf'
        c = canvas.Canvas(str(src), pagesize=(612,792), invariant=1)
        for title, paragraphs in chapters:
            c.setFont('Times-Bold',18); c.drawString(72,720,title); y=675
            for paragraph in paragraphs:
                c.setFont('Times-Roman',12)
                for line in simpleSplit(paragraph,'Times-Roman',12,468):
                    c.drawString(72,y,line); y-=16
                y-=18
            c.showPage()
        c.save()
        r = convert(src,self.root/'prose',title='A Bridge in the Garden',language='en',command=COMMAND)
        m = json.loads((self.root/'prose/model.json').read_text())
        expected = [text for title, paragraphs in chapters for text in [title,*paragraphs]]
        self.assertEqual([b['text'] for b in m['blocks']],expected)
        if JAR: self.assertEqual(r['state'],'Aprovado',r['findings'])

    def test_indented_wrapped_paragraphs(self):
        from reportlab.lib.utils import simpleSplit
        paragraphs = json.loads((Path(__file__).parent/'fixtures/prose.json').read_text())[0][1]
        src = self.root/'indent.pdf'
        c = canvas.Canvas(str(src), pagesize=(612,792), invariant=1)
        c.setFont('Times-Bold',18); c.drawString(72,720,'Chapter 1'); y=675
        c.setFont('Times-Roman',12)
        for paragraph in paragraphs:
            # Fixed narrower wrap permits the first-line indent without overflow.
            for index, line in enumerate(simpleSplit(paragraph,'Times-Roman',12,440)):
                c.drawString(90 if index == 0 else 72,y,line); y-=16
        c.showPage(); c.save()
        r = convert(src,self.root/'indent',title='Indented prose',language='en',command=COMMAND)
        m = json.loads((self.root/'indent/model.json').read_text())
        self.assertEqual([b['text'] for b in m['blocks'] if b['kind']=='paragraph'], paragraphs)
        if JAR: self.assertEqual(r['state'],'Aprovado',r['findings'])
    def test_empty_validator_report_is_inconclusive(self):
        import sys
        from book_epub.validate import epubcheck
        script = self.root/'checker.py'
        script.write_text("import sys;from pathlib import Path;Path(sys.argv[-1]).write_text('{}')")
        f = epubcheck(self.root/'unused.epub',[sys.executable,str(script)])
        self.assertEqual(f['status'],'inconclusive')
    def test_emphasis_is_preserved(self):
        src=self.root/'emphasis.pdf'
        c=canvas.Canvas(str(src),pagesize=(600,800),invariant=1)
        c.setFont('Times-Bold',20);c.drawString(50,700,'Chapter 1')
        c.setFont('Times-Roman',12);c.drawString(50,660,'Ordinary text.')
        c.setFont('Times-Italic',12);c.drawString(50,620,'Meaningful emphasis.')
        c.showPage();c.save()
        r=convert(src,self.root/'emphasis',title='Emphasis',language='en',command=COMMAND)
        if JAR: self.assertEqual(r['state'],'Aprovado')
        with zipfile.ZipFile(self.root/'emphasis/book.epub') as z:
            self.assertIn(b'<em>Meaningful emphasis.</em>',z.read('EPUB/chapter-0001.xhtml'))
    def test_review_findings_survive_refinement(self):
        r,_=self.run_case('footnote')
        revised=refine(self.root/'v1',self.root/'v2',paragraph_gap=1,command=COMMAND)
        self.assertEqual(revised['state'],'Revisão recomendada')
        self.assertTrue(any(f['code']=='small_text' for f in revised['findings']))

    def test_indented_quote_run_requires_review(self):
        src=self.root/'quote.pdf';c=canvas.Canvas(str(src),pagesize=(600,800),invariant=1)
        c.setFont('Times-Bold',20);c.drawString(50,700,'Chapter 1')
        c.setFont('Times-Roman',12);c.drawString(50,660,'Ordinary introductory paragraph.')
        c.drawString(80,620,'An indented quotation continues')
        c.drawString(80,604,'across this second line.')
        c.showPage();c.save()
        r=convert(src,self.root/'quote',title='Quote',language='en',command=COMMAND)
        self.assertEqual(r['state'],'Revisão recomendada')
        self.assertTrue(any(f['code']=='indented_run' for f in r['findings']))

    def test_independent_extractor_unavailable_keeps_usable_output(self):
        with patch('book_epub.extract.PdfReader',side_effect=ValueError('unavailable')):
            r,_=self.run_case()
        self.assertEqual(r['state'],'Revisão recomendada')
        self.assertTrue((self.root/'v1/book.epub').exists())
        self.assertTrue(any(f['code']=='independent_extraction' and f['status']=='unavailable' for f in r['findings']))

    def test_unknown_page_offset_is_retained_and_flagged(self):
        src=self.root/'offset.pdf';c=canvas.Canvas(str(src),pagesize=(600,800),invariant=1)
        c.setFont('Times-Bold',20);c.drawString(50,700,'Chapter 1')
        c.setFont('Times-Roman',12);c.drawString(50,660,'A complete paragraph.')
        c.drawString(50,20,'iv');c.showPage();c.save()
        r=convert(src,self.root/'offset',title='Offset',language='en',command=COMMAND)
        m=json.loads((self.root/'offset/model.json').read_text())
        self.assertEqual(r['state'],'Revisão recomendada')
        self.assertTrue(any(b['text']=='iv' for b in m['blocks']))
        self.assertTrue(any(f['code']=='unresolved_pagination' for f in r['findings']))

    def test_uncued_paragraphs_never_approved(self):
        # Identical geometry can encode one paragraph or two: even full-width
        # endings must not establish paragraph fidelity without positive cues.
        for end in ['.', ',', '']:
            with self.subTest(end=end):
                src=self.root/f'ambiguous{len(end)}{ord(end) if end else 0}.pdf'
                c=canvas.Canvas(str(src),pagesize=(600,800),invariant=1)
                c.setFont('Times-Bold',20);c.drawString(50,700,'Chapter 1')
                c.setFont('Times-Roman',12)
                for i,line in enumerate(['A distinct paragraph ends here'+end,'Another distinct paragraph begins here.', 'Its continuation occupies the next line.']):
                    c.drawString(50,660-i*16,line)
                c.showPage();c.save()
                r=convert(src,self.root/f'out{ord(end) if end else 0}',title='Ambiguous',language='en',command=COMMAND)
                self.assertEqual(r['state'],'Revisão recomendada')
                self.assertTrue(any(f['code']=='paragraph_layout' for f in r['findings']))
    def test_subtitle_and_quotation_are_limitations(self):
        src=self.root/'semantic.pdf';c=canvas.Canvas(str(src),pagesize=(600,800),invariant=1)
        c.setFont('Times-Bold',20);c.drawString(50,700,'Chapter 1')
        c.setFont('Times-Bold',16);c.drawString(50,670,'A subordinate heading')
        c.setFont('Times-Roman',12);c.drawString(50,620,'"A quotation stays textual."')
        c.drawString(50,580,'A separate ordinary paragraph.')
        c.showPage();c.save()
        r=convert(src,self.root/'semantic',title='Semantics',language='en',command=COMMAND)
        self.assertEqual(r['state'],'Revisão recomendada')
        for code in ['quotation']:
            self.assertTrue(any(f['code']==code for f in r['findings']))

    def test_simple_exact_text(self):
        r, m = self.run_case()
        self.assertEqual([b['text'] for b in m['blocks']], ['Capítulo 1', 'Primeiro parágrafo. Mantém acentos e pontuação.', 'Segundo parágrafo independente.'])
        self.assertFalse([f for f in r['findings'] if f['status'] == 'fail'])
    @unittest.skipUnless(JAR, 'Set EPUBCHECK_JAR for real conformance validation')
    def test_simple_can_be_approved_with_real_epubcheck(self):
        r, _ = self.run_case()
        self.assertEqual(r['state'], 'Aprovado', r['findings'])
    def test_unavailable_not_failure(self):
        r, _ = self.run_case(command=['/missing/epubcheck'])
        self.assertEqual(r['state'], 'Revisão recomendada')
        self.assertEqual(next(f for f in r['findings'] if f['code'] == 'epubcheck')['status'], 'unavailable')
    def test_repeated_margins(self):
        r, m = self.run_case('margins')
        self.assertEqual(len([l for l in m['lines'] if l.get('excluded')]), 6)
        self.assertEqual(len([b for b in m['blocks'] if b['kind'] == 'heading']), 3)
        self.assertTrue(all(f['status'] == 'pass' for f in audit_model(m)))
    def test_crosspage_continuation(self):
        _, m = self.run_case('crosspage')
        self.assertTrue(any(len({s.split('-')[0] for s in b['source']}) > 1 for b in m['blocks']))
        self.assertTrue(all(f['status'] == 'pass' for f in audit_model(m)))
    def test_ambiguous_hyphen_preserved(self):
        r, m = self.run_case('hyphen')
        self.assertIn('transfor-mação', ' '.join(b['text'] for b in m['blocks']))
        self.assertTrue(any(f['code'] == 'hyphenation' for f in r['findings']))
        self.assertEqual(r['state'], 'Revisão recomendada')
    def test_evidenced_hyphen_removed(self):
        _, m = self.run_case('knownhyphen')
        self.assertIn('transformação', m['blocks'][1]['text'])
        self.assertTrue(any(t['kind'] == 'dehyphenate' for t in m['transformations']))
        self.assertTrue(all(f['status'] == 'pass' for f in audit_model(m)))
    def test_footnote_preserved_and_flagged(self):
        r, m = self.run_case('footnote')
        self.assertIn('Nota de rodapé', ' '.join(b['text'] for b in m['blocks']))
        self.assertEqual(r['state'], 'Revisão recomendada')
        self.assertTrue(any(f['code'] == 'small_text' for f in r['findings']))
    def test_columns_blocked(self):
        r, _ = self.run_case('columns')
        self.assertEqual(r['state'], 'Intervenção necessária')
        self.assertFalse((self.root/'v1/book.epub').exists())
    def test_scan_blocked(self):
        r, _ = self.run_case('scan')
        self.assertEqual(r['state'], 'Intervenção necessária')
    def test_essential_image_not_silently_lost(self):
        r, _ = self.run_case('image')
        self.assertIsNotNone(r['epub_sha256'])
        with zipfile.ZipFile(self.root/'v1/book.epub') as z:
            self.assertIn('EPUB/images/p1-img1.png',z.namelist())
        self.assertTrue(any(f['code']=='serialized_images_semantics' and f['status']=='pass' for f in r['findings']))
    def test_empty_blocked(self):
        r, _ = self.run_case('blank')
        self.assertEqual(r['state'], 'Intervenção necessária')
    def test_reproducible_epub_and_model(self):
        self.run_case(name='v1'); self.run_case(name='v2')
        for name in ['book.epub', 'model.json']:
            self.assertEqual((self.root/'v1'/name).read_bytes(), (self.root/'v2'/name).read_bytes())
    def test_css_revision_never_reextracts(self):
        self.run_case()
        with patch('book_epub.pipeline.extract', side_effect=AssertionError('reextraction')):
            r = refine(self.root/'v1', self.root/'v2', paragraph_gap=1.2, command=COMMAND)
        self.assertEqual(r['revision'], 2)
        self.assertEqual((self.root/'v1/model.json').read_bytes(), (self.root/'v2/model.json').read_bytes())
        with zipfile.ZipFile(self.root/'v1/book.epub') as a, zipfile.ZipFile(self.root/'v2/book.epub') as b:
            self.assertEqual([n for n in a.namelist() if a.read(n) != b.read(n)], ['EPUB/style.css'])
    def test_nav_revision_preserves_css_and_text(self):
        self.run_case()
        refine(self.root/'v1', self.root/'v2', labels={'b1': 'Início'}, command=COMMAND)
        with zipfile.ZipFile(self.root/'v1/book.epub') as a, zipfile.ZipFile(self.root/'v2/book.epub') as b:
            self.assertEqual([n for n in a.namelist() if a.read(n) != b.read(n)], ['EPUB/nav.xhtml'])
    def test_previous_tamper_refused(self):
        self.run_case(); (self.root/'v1/model.json').write_text('{}')
        with self.assertRaises(ValueError): refine(self.root/'v1', self.root/'v2', paragraph_gap=1)
    def test_never_overwrite_revision(self):
        self.run_case()
        with self.assertRaises(FileExistsError): self.run_case()
    def test_lost_duplicate_and_reordered_text_detected(self):
        _, m = self.run_case()
        for kind in ['lost', 'duplicate', 'reorder']:
            bad = copy.deepcopy(m)
            if kind == 'lost': bad['blocks'].pop()
            if kind == 'duplicate': bad['blocks'].append(bad['blocks'][1])
            if kind == 'reorder': bad['blocks'].reverse()
            self.assertTrue(any(f['status'] == 'fail' for f in audit_model(bad)))
    def test_serialized_corruption_detected(self):
        _, m = self.run_case()
        with zipfile.ZipFile(self.root/'v1/book.epub') as z: members = {n:z.read(n) for n in z.namelist()}
        for member, before, after in [('EPUB/nav.xhtml', b'#b1', b'#missing'), ('EPUB/chapter-0001.xhtml', b'Primeiro', b'Alterado')]:
            changed = dict(members); changed[member] = changed[member].replace(before, after)
            write_epub(self.root/'bad.epub', changed)
            checks = validate(self.root/'bad.epub', m, 'generic', css()[1], command=COMMAND)
            self.assertTrue(any(f['status'] == 'fail' for f in checks))
    def test_tolerable_unavailability_not_blocking(self):
        self.assertEqual(classify([finding('device', 'unavailable', 'tolerable', 'Not tested')]), 'Aprovado')
    def test_invalid_style_and_navigation_rejected(self):
        self.run_case()
        for n in [-1, 4, float('nan'), float('inf')]:
            with self.assertRaises(ValueError): refine(self.root/'v1', self.root/'v2', paragraph_gap=n)
        with self.assertRaises(ValueError): refine(self.root/'v1', self.root/'v2', labels={'unknown': 'Bad'})
    def test_invalid_pdf_report(self):
        src = self.root/'invalid.pdf'; src.write_bytes(b'not PDF')
        r = convert(src, self.root/'v1', title='Invalid', language='en')
        self.assertEqual(r['state'], 'Intervenção necessária')

if __name__ == '__main__': unittest.main()
