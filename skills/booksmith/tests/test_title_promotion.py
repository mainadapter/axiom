"""Authored editorial expectations, independent of classifier/model agreement.

Synthetic PDFs use arbitrary typography, identifiers and reading orders. Expected
headings, navigation and ordinary text are literal oracles, not detector output.
"""
import copy
import unittest
from xml.etree import ElementTree as ET
import test_booksmith as helpers
from book_epub.package import chapters, navigation
from book_epub.validate import audit_editorial

BODY='The traveller crossed the orchard and followed the river toward the village.'

class TitlePromotion(helpers.BooksmithTests):
    def assert_headings(self, expected):
        self.assertEqual([(b['text'],b['level']) for b in self.model['blocks'] if b['kind']=='heading'], expected)
        ns={'h':'http://www.w3.org/1999/xhtml'}
        # Inspect serialized navigation as well as model semantics.
        links=ET.fromstring(self.members()['EPUB/nav.xhtml']).findall('.//h:a',ns)
        self.assertEqual([a.text for a in links if a.text!='Booksmith fixture'],[t for t,_ in expected])

    def chapter(self,c,label):
        c.setFont('Times-Bold',20);c.drawString(40,740,label)
        c.setFont('Times-Roman',12);c.drawString(40,680,BODY)
        c.showPage()

    def test_catalogue_like_codes_preserved_without_navigation(self):
        codes=['27-04682 ABX-734.2','908-12-3456-789-0','R7-8024 ZQ-91']
        def draw(c):
            self.chapter(c,'Chapter 1');self.chapter(c,'Chapter 2')
            c.setFont('Times-Roman',12);c.drawString(40,740,'Production and publication information')
            for y,code in zip([680,620,560],codes):
                c.setFont('Times-Bold',12);c.drawCentredString(300,y,code)
            c.setFont('Times-Roman',12);c.drawString(40,500,'The record remains in its original reading order.')
        self.convert(draw);self.assert_headings([('Chapter 1',1),('Chapter 2',1)])
        self.assertEqual(len(chapters(self.model)),2)
        paragraphs=[b['text'] for b in self.model['blocks'] if b['kind']=='paragraph']
        for code in codes:self.assertIn(code,paragraphs)
        pending=[f for f in self.report['findings'] if f['evidence'].get('decision')=='deferred']
        self.assertTrue(pending)
        self.assertEqual(self.report['state'],'Revisão recomendada')

    def test_large_repeated_identifiers_are_not_typographic_title_family(self):
        codes=['82-771 RQ-93.4','93-882 JK-24.7']
        def draw(c):
            for code in codes:
                c.setFont('Helvetica-Bold',24);c.drawCentredString(300,740,code)
                c.setFont('Helvetica',12);c.drawString(40,680,'A descriptive publishing record supplies ordinary lexical text.')
                c.showPage()
        self.convert(draw);self.assert_headings([])
        self.assertEqual(len(self.model['editorial_structure']['pending_titles']),2)

    def test_single_unusual_unnumbered_isolated_title_with_body_support(self):
        def draw(c):
            c.setFont('Helvetica',22);c.drawString(40,740,'Perhaps, tomorrow?')
            c.setFont('Helvetica',12);c.drawString(40,670,BODY)
        self.convert(draw);self.assert_headings([('Perhaps, tomorrow?',1)])

    def test_uncorroborated_uppercase_is_reviewed_as_ordinary_text(self):
        def draw(c):
            self.chapter(c,'Chapter 1')
            c.setFont('Times-Bold',12);c.drawCentredString(300,740,'A POSSIBLE TITLE')
            c.setFont('Times-Roman',12);c.drawString(40,680,BODY)
        self.convert(draw);self.assert_headings([('Chapter 1',1)])
        self.assertTrue(any(b['text']=='A POSSIBLE TITLE' and b['kind']=='paragraph' for b in self.model['blocks']))
        self.assertTrue(any(f['evidence'].get('decision')=='deferred' for f in self.report['findings']))
        # Removing stored predictions must not silence retrospective audit.
        changed=copy.deepcopy(self.model);changed['editorial_structure']={}
        b=next(b for b in changed['blocks'] if b['text']=='A POSSIBLE TITLE')
        b.update(kind='heading',level=1,heading_evidence=['explicit_label'])
        self.assertTrue(any(f['evidence'].get('decision')=='unsupported_promotion' for f in audit_editorial(changed)))

    def test_complementary_unnumbered_title_survives_at_end(self):
        def draw(c):
            self.chapter(c,'Chapter 1');self.chapter(c,'Chapter 2')
            c.setFont('Times-Bold',21);c.drawString(40,740,'Afterword')
            c.setFont('Times-Roman',12);c.drawString(40,680,BODY)
        self.convert(draw);self.assert_headings([('Chapter 1',1),('Chapter 2',1),('Afterword',1)])

    def test_anchored_unnumbered_family_without_large_font_ratio(self):
        def draw(c):
            c.setFont('Times-Roman',16);c.drawCentredString(300,740,'THE ORCHARD')
            c.setFont('Times-Bold',14);c.drawCentredString(300,680,'I')
            c.setFont('Times-Roman',14);c.drawString(40,620,BODY)
            c.setFont('Times-Bold',14);c.drawCentredString(300,560,'II')
            c.setFont('Times-Roman',14);c.drawString(40,500,BODY)
            c.showPage()
            c.setFont('Times-Roman',16);c.drawCentredString(300,740,'THE SHORE')
            c.setFont('Times-Roman',14);c.drawString(40,650,'— Shall we go?')
            c.drawString(40,633,BODY)
        self.convert(draw);self.assert_headings([('THE ORCHARD',1),('I',2),('II',2),('THE SHORE',1)])

    def test_numeric_chapters_with_and_without_source_contents(self):
        for contents in [False,True]:
            with self.subTest(contents=contents):
                def draw(c):
                    if contents:
                        c.setFont('Times-Roman',12)
                        for y,t in [(740,'CONTENTS'),(680,'Chapter 8'),(620,'Chapter 9')]:c.drawString(40,y,t)
                        c.showPage()
                    self.chapter(c,'Chapter 8');self.chapter(c,'Chapter 9')
                self.convert(draw)
                self.assertEqual([(b['text'],b['level']) for b in self.model['blocks'] if b['kind']=='heading'],[('Chapter 8',1),('Chapter 9',1)])
                import shutil
                shutil.rmtree(self.root/'v1')

    def test_two_levels_and_title_only_book_without_contents(self):
        def draw(c):
            for title in ['The orchard','The shore']:
                c.setFont('Helvetica-Bold',24);c.drawString(40,740,title)
                c.setFont('Helvetica-Bold',18);c.drawString(40,680,'An interlude')
                c.setFont('Helvetica',12);c.drawString(40,620,BODY)
                c.showPage()
        self.convert(draw);self.assert_headings([('The orchard',1),('An interlude',2),('The shore',1),('An interlude',2)])

for name in list(vars(helpers.BooksmithTests)):
    if name.startswith('test_') and name not in vars(TitlePromotion):setattr(TitlePromotion,name,None)
