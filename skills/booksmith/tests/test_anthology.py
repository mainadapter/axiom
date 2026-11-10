"""Editorial ground truth authored before reconstruction; no private book text."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest
from xml.etree import ElementTree as ET

import test_booksmith as helpers
from book_epub.package import chapters, navigation_entries, navigation
from book_epub.validate import audit_editorial
from book_epub.pipeline import diagnostic_summary, report_markdown

TITLES = ['THE RIVER', 'THE WINDOW', 'THE ROAD', 'THE BRIDGE', 'THE LETTER', 'THE RETURN']
SECTIONS = [8, 9, 4, 10, 8, 9]
ROMANS = ['I','II','III','IV','V','VI','VII','VIII','IX','X']

class AnthologyTests(helpers.BooksmithTests):
    # Reuse helpers only; the other test class is discovered in its own module.
    def anthology(self, c):
        c.setFont('Times-Bold',28);c.drawCentredString(300,730,TITLES[4])
        c.setFont('Times-Roman',24);c.drawCentredString(300,660,'An Author')
        c.setFont('Times-Roman',12);c.drawCentredString(300,500,'A city, 2026')
        c.showPage()
        c.setFont('Times-Roman',20);c.drawCentredString(300,760,'CONTENTS')
        c.setFont('Times-Roman',14)
        for i,title in enumerate(TITLES):c.drawCentredString(300,650-i*40,title.title())
        c.showPage()
        for title,count in zip(TITLES,SECTIONS):
            c.setFont('Times-Roman',20);c.drawCentredString(300,760,title)
            c.setFont('Times-Bold',14);c.drawCentredString(300,600,'I')
            c.setFont('Times-Roman',14);c.drawString(40,550,'A quiet beginning establishes ordinary narrative prose.')
            c.drawString(40,510,'Another ordinary paragraph follows in the original order.')
            c.showPage()
            for roman in ROMANS[1:count]:
                c.setFont('Times-Bold',14);c.drawCentredString(300,760,roman)
                c.setFont('Times-Roman',14);c.drawString(40,700,'The narrative continues under this section of the tale.')
                c.drawString(40,660,'A final sentence preserves the ordinary body typography.')
                c.showPage()

    def test_six_tales_ground_truth(self):
        self.convert(self.anthology)
        hs=[(b['text'],b['level']) for b in self.model['blocks'] if b['kind']=='heading']
        expected=[]
        for title,count in zip(TITLES,SECTIONS):expected.extend([(title,1)]+[(r,2) for r in ROMANS[:count]])
        self.assertEqual(hs,expected)
        cs=chapters(self.model)
        self.assertEqual(len(cs),7)
        self.assertEqual([c['label'] for c in cs],['Front matter']+TITLES)
        self.assertTrue(all(b.get('content_role')=='frontmatter' for b in cs[0]['blocks']))
        self.assertEqual([sum(b['kind']=='heading' and b['level']==2 for b in c['blocks']) for c in cs[1:]],SECTIONS)
        self.assertTrue(all(f['status']=='pass' for f in audit_editorial(self.model)))
        entries=navigation_entries(self.model)
        self.assertEqual(len(entries),55)
        nav=ET.fromstring(navigation(self.model));ns={'h':'http://www.w3.org/1999/xhtml'}
        roots=nav.findall('.//h:nav/h:ol/h:li',ns)
        self.assertEqual(len(roots),7)
        self.assertEqual([len(r.findall('h:ol/h:li',ns)) for r in roots],[0]+SECTIONS)
        self.assertIsNotNone(self.report['epub_sha256'])

    def test_valid_links_do_not_hide_wrong_editorial_model(self):
        self.convert(self.anthology)
        broken=copy.deepcopy(self.model)
        parent=next(b for b in broken['blocks'] if b['text']==TITLES[2])
        parent['level']=2
        checks=audit_editorial(broken)
        f=next(f for f in checks if f['status']=='fail')
        self.assertEqual(f['evidence']['blocks'],[parent['id']])
        self.assertTrue(f['evidence']['pages'])
        report=dict(self.report,summary=diagnostic_summary(checks,broken))
        self.assertIn('Estrutura editorial',report_markdown(report))
        self.assertIn(parent['id'],report_markdown(report))

    def test_terminal_publishing_information_is_separate(self):
        def draw(c):
            self.anthology(c)
            c.setFont('Times-Roman',10)
            c.drawString(40,740,'Copyright 2026, all rights reserved.')
            c.drawString(40,700,'ISBN 000-0-00-000000-0')
        self.convert(draw)
        cs=chapters(self.model)
        self.assertEqual(len(cs),8)
        self.assertEqual(cs[-1]['label'],'Publishing information')
        self.assertTrue(all(b.get('content_role')=='backmatter' for b in cs[-1]['blocks']))
        self.assertTrue(all(f['status']=='pass' for f in audit_editorial(self.model)))

    def test_frontmatter_promotion_is_a_proven_contradiction(self):
        self.convert(self.anthology)
        broken=copy.deepcopy(self.model)
        block=next(b for b in broken['blocks'] if b['text']=='An Author')
        block.update(kind='heading',level=2)
        block.pop('content_role')
        findings=audit_editorial(broken)
        self.assertTrue(any(f['status']=='fail' and f['evidence'].get('reason')=='frontmatter_role' for f in findings))

    def test_roman_gap_is_review_not_approval(self):
        def draw(c):
            c.setFont('Times-Roman',12);c.drawCentredString(300,740,'THE GARDEN')
            for y,text in [(680,'I'),(500,'III')]:
                c.drawCentredString(300,y,text)
                c.drawString(40,y-40,'Ordinary narrative prose establishes a body font and margin.')
        self.convert(draw)
        checks=audit_editorial(self.model)
        self.assertTrue(any(f['status']=='inconclusive' and f['evidence']['reason']=='roman_sequence' for f in checks))
        self.assertEqual(self.report['state'],'Revisão recomendada')

    def test_canonical_command_without_legacy_directory(self):
        canonical=Path(__file__).resolve().parents[1]
        self.assertFalse((canonical.parent/'book-to-epub').exists())
        result=subprocess.run([sys.executable,'-m','book_epub','--help'],cwd=canonical,capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)

# Inheritance supplies helpers, not duplicate executions of the original regressions.
for name in list(vars(helpers.BooksmithTests)):
    if name.startswith('test_') and name not in vars(AnthologyTests):setattr(AnthologyTests,name,None)
