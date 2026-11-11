"""Literal expected strings and independently positioned PDF text operators."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from reportlab.pdfgen import canvas
from reportlab.pdfbase.pdfmetrics import stringWidth
from book_epub.extract import extract
from book_epub.spacing import audit_spacing, boundaries
from book_epub.common import classify


class SpacingTests(unittest.TestCase):
    def fixture(self,draw):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        src=Path(tmp.name)/'spacing.pdf'
        c=canvas.Canvas(str(src),pagesize=(600,800),invariant=1);draw(c);c.save()
        return src,extract(src)

    def test_explicit_compressed_spaces_fonts_sizes(self):
        for font in ['Times-Roman','Helvetica','Courier']:
            for size in [8,12,24]:
                with self.subTest(font=font,size=size):
                    def draw(c):
                        t=c.beginText(40,700);t.setFont(font,size)
                        # Leave a positive literal separator below old .18em rule.
                        t.setWordSpace(size*.08-stringWidth(' ',font,size))
                        t.textOut('Silver birds, blue skies; sun-lit paths.');c.drawText(t)
                    _,m=self.fixture(draw)
                    self.assertEqual(m['lines'][0]['text'],'Silver birds, blue skies; sun-lit paths.')
                    self.assertTrue(any(t['kind']=='preserve_explicit_space' for t in m['transformations']))
                    self.assertFalse(any(f['status']=='fail' for f in audit_spacing(m)))

    def test_geometry_and_adjacent_letters_punctuation(self):
        def draw(c):
            c.setFont('Times-Roman',14)
            x=40
            for fragment,gap in [('Clear',4),('water',0),(',',4),('bright',0),('ness',0),('.',0)]:
                c.drawString(x,700,fragment);x+=stringWidth(fragment,'Times-Roman',14)+gap
        _,m=self.fixture(draw)
        self.assertEqual(m['lines'][0]['text'],'Clear water, brightness.')

    def test_ambiguous_geometry_is_not_rewritten(self):
        def draw(c):
            c.setFont('Helvetica',12);c.drawString(40,700,'rain')
            c.drawString(40+stringWidth('rain','Helvetica',12)+1,700,'bow')
        _,m=self.fixture(draw)
        self.assertEqual(m['lines'][0]['text'],'rainbow')
        # An alternative parser boundary alone is insufficient proof.
        m['pages'][0]['independent_text']='rain bow'
        checks=audit_spacing(m)
        self.assertEqual([f['evidence'].get('reason') for f in checks],['geometric_or_extractor'])
        self.assertEqual(classify(checks),'Revisão recomendada')
        self.assertEqual(m['lines'][0]['text'],'rainbow')

    def test_line_paragraph_hyphenation(self):
        def draw(c):
            c.setFont('Times-Roman',12)
            for y,t in [(700,'A well-lit path continues'),(684,'beyond a quiet hillside.'),(640,'Another paragraph begins here.')]:c.drawString(40,y,t)
        _,m=self.fixture(draw)
        self.assertIn('A well-lit path continues beyond a quiet hillside.',[b['text'] for b in m['blocks']])
        self.assertIn('Another paragraph begins here.',[b['text'] for b in m['blocks']])

    def test_independent_audit_catches_self_consistent_bad_ledger(self):
        def draw(c):
            c.setFont('Helvetica',12);c.drawString(40,700,'Quiet waters.')
        src,m=self.fixture(draw)
        m['lines'][0]['text']='Quietwaters.'
        m['lines'][0]['spans'][0]['text']='Quietwaters.'
        m['blocks'][0]['text']='Quietwaters.'
        checks=audit_spacing(m)
        self.assertEqual(classify(checks),'Intervenção necessária')
        defect=next(f for f in checks if f['status']=='fail')
        self.assertEqual(defect['evidence']['source'],'p1-l1')
        self.assertEqual(defect['evidence']['block'],'b1')
        # Cannot bypass the original by changing the saved evidence.
        m['pages'][0]['literal_text']='Quietwaters.'
        m['pages'][0]['independent_text']='Quietwaters.'
        self.assertEqual(classify(audit_spacing(m,src)),'Intervenção necessária')
        m['source_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'hash differs'):
            audit_spacing(m,src)

    def test_unaligned_and_legacy_are_not_proven_failures(self):
        def draw(c):
            c.setFont('Helvetica',12);c.drawString(40,700,'Clear weather.')
        _,m=self.fixture(draw)
        m['pages'][0]['independent_text']='Different letters.'
        self.assertEqual(audit_spacing(m)[0]['evidence']['reason'],'unaligned')
        del m['pages'][0]['literal_text']
        self.assertEqual(audit_spacing(m)[0]['status'],'unavailable')

    def test_extra_boundary_is_review_not_blocking(self):
        def draw(c):
            c.setFont('Helvetica',12);c.drawString(40,700,'Clouds.')
        _,m=self.fixture(draw);m['lines'][0]['text']='Cl ouds.'
        checks=audit_spacing(m)
        self.assertEqual(checks[0]['evidence']['reason'],'engine_only_boundary')
        self.assertEqual(classify(checks),'Revisão recomendada')

    def test_ligatures_and_whitespace_normalization(self):
        self.assertEqual(boundaries('ﬁne\u00a0weather.'),boundaries('fine weather.'))

    def test_font_transition_punctuation_difference_is_not_word_fusion(self):
        def draw(c):
            c.setFont('Helvetica',12);c.drawString(40,700,'Calm, quiet.')
        _,m=self.fixture(draw)
        m['pages'][0]['independent_text']='Calm , quiet.'
        fs=audit_spacing(m)
        self.assertEqual(fs[0]['evidence']['reason'],'punctuation_difference')
        self.assertEqual(fs[0]['status'],'pass')
        self.assertEqual(m['lines'][0]['text'],'Calm, quiet.')

    def test_block_only_space_loss_is_blocking(self):
        from book_epub.validate import audit_model
        def draw(c):
            c.setFont('Helvetica',12);c.drawString(40,700,'Clear water.')
        _,m=self.fixture(draw);m['schema']=2
        m['blocks'][0]['text']='Clearwater.'
        m['blocks'][0]['spans'][0]['text']='Clearwater.'
        check=next(f for f in audit_model(m) if f['code']=='source_word_boundaries')
        self.assertEqual(check['status'],'fail')
        self.assertEqual(check['evidence']['blocks'],['b1'])
