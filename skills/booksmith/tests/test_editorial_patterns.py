"""Development fixtures: source patterns independent of private novels."""
import unittest
from book_epub.evidence import explicit, explicit_facts
from book_epub.structure import document_structure, profiles
from book_epub.validate import audit_editorial
from book_epub.common import classify


def line(text,page=1,n=1,size=12,font='Body',top=None,x=40):
    top=top if top is not None else 40+n*60
    return dict(id=f'p{page}-l{n}',page=page,text=text,size=size,fonts=[font],
                top=top,bottom=top+size,x0=x,x1=min(550,x+len(text)*size*.4),width=600,height=800,
                spans=[dict(text=text,bold='Bold' in font,italic='Italic' in font)])


def novel(labels=('CHAPTER ONE','CHAPTER TWO'),contents=True):
    ls=[]
    if contents:
        ls=[line('A DISTANT SHORE',1,1,30),line('An invented author',1,2,22),line('CONTENTS',2,1,18)]
        ls += [line(t,2,i+2,12) for i,t in enumerate(labels)]
    for p,t in enumerate(labels,3):
        ls.append(line(t,p,1,18,'Title',40))
        # Enough small quotation text to dominate a naive page character mode.
        ls += [line('A smaller quotation remembers distant shores and imaginary seasons.',p,i+2,8,'Italic',100+i*10) for i in range(12)]
        ls += [line(t,p,i+14,12,'Body',260+i*16) for i,t in enumerate([
            'The traveller opened the gate and continued along the unfamiliar road',
            'where the orchard ended and an ordinary conversation began.',
            '— Have you brought the map that we discussed yesterday?',
            '— It is here, said the other traveller, unfolding the faded paper.'
        ])]
    # Ordinary narrative pages anchor the document reference, independently of
    # the smaller local quotation majority on chapter-opening pages.
    for p in [5,6,7]:
        ls += [line('The ordinary narrative continues through the orchard with many familiar details.',p,i+1,12,top=40+i*16) for i in range(20)]
    return ls


def model_for(ls):
    hs,ctx=document_structure(ls,profiles(ls))
    return dict(schema=2,lines=ls,blocks=[dict(id='b'+str(i),source=[l['id']],text=l['text'],
        kind='heading' if l['id'] in hs else 'paragraph',
        **({'level':hs[l['id']]['level']} if l['id'] in hs else {}),
        **({'content_role':'frontmatter'} if l['id'] in ctx['frontmatter'] else {})) for i,l in enumerate(ls)])


class EditorialPatterns(unittest.TestCase):
    def test_numeric_ordinal_roman_labels_and_nonlabels(self):
        for t,n in [('CAPÍTULO QUINTO',5),('Capítulo sétimo',7),('Chapter third',3),('Chapter nine',9),('Chapter IX',9),('Parte segunda',2),('Seção 12',12),('Capítulo 5º',5)]:
            self.assertEqual(explicit(t)[1],n)
        for t in ['Chapter two was missing from the shelf.','Chapter impossible','I am here','Chapter IC','Chapter 0']:
            self.assertIsNone(explicit(t))

    def test_small_epigraph_cannot_promote_larger_prose(self):
        ls=novel();hs,ctx=document_structure(ls,profiles(ls))
        self.assertEqual([(l['text'],hs[l['id']]['level']) for l in ls if l['id'] in hs],[('CHAPTER ONE',1),('CHAPTER TWO',1)])
        self.assertEqual(len(ctx['frontmatter']),5)
        self.assertEqual([profiles(ls)[p]['size'] for p in [3,4]],[12,12])
        self.assertFalse(any(f['status']!='pass' for f in audit_editorial(model_for(ls))))

    def test_no_contents_still_recognizes_chapters(self):
        ls=novel(('Capítulo terceiro','Capítulo quarto'),False)
        hs,ctx=document_structure(ls,profiles(ls))
        self.assertEqual([h['level'] for h in hs.values()],[1,1]);self.assertFalse(ctx['frontmatter'])

    def test_legitimate_bold_typographic_subdivision(self):
        ls=[line('A Different Journey',n=1,size=24,font='Bold'),line('A brief interlude',n=2,size=18,font='Bold'),
            line('Ordinary narrative provides the local reference for body text.',n=3),line('Another ordinary sentence continues the narrative.',n=4)]
        hs,_=document_structure(ls,profiles(ls));self.assertEqual([h['level'] for h in hs.values()],[1,2])
        self.assertTrue(all(f['status']=='pass' for f in audit_editorial(model_for(ls))))

    def test_mutations_detect_levels_missing_chapter_frontmatter_and_prose(self):
        ls=novel();m=model_for(ls)
        target=next(b for b in m['blocks'] if b['source']==['p4-l1']);target['level']=2
        missing=next(b for b in m['blocks'] if b['source']==['p3-l1']);missing['kind']='paragraph'
        front=m['blocks'][0];front.update(kind='heading',level=1);front.pop('content_role')
        prose=next(b for b in m['blocks'] if b['source']==['p3-l14']);prose.update(kind='heading',level=2)
        fs=audit_editorial(m);reasons={f['evidence'].get('reason') for f in fs if f['status']=='fail'}
        self.assertTrue({'explicit_level','frontmatter_role','narrative_heading'}<=reasons)
        self.assertEqual(classify(fs),'Intervenção necessária')
        self.assertTrue(all('pages' in f['evidence'] and 'blocks' in f['evidence'] and 'source' in f['evidence'] for f in fs))

    def test_source_contents_divergence_requires_review(self):
        ls=novel();ls.insert(5,line('CHAPTER THREE',2,4))
        fs=audit_editorial(model_for(ls))
        self.assertTrue(any(f['status']=='inconclusive' and f['evidence'].get('reason')=='contents_source_mismatch' for f in fs))

    def test_isolated_dialogue_title_is_ambiguous_not_proven_defect(self):
        ls=[line('— A promise?',n=1,size=20,font='Bold'),line('A narrative sentence establishes an ordinary body text style.',n=2)]
        m=model_for(ls);m['blocks'][0].update(kind='heading',level=1)
        fs=audit_editorial(m)
        self.assertEqual(classify(fs),'Revisão recomendada')
        self.assertFalse(any(f['status']=='fail' for f in fs))

    def test_dense_headings_detected_without_trusting_recorded_evidence(self):
        ls=[line('An ordinary narrative sentence continues across this densely printed region.',page=p,n=i+1,top=40+i*14) for p in [1,2,3] for i in range(12)]
        m=model_for(ls)
        for b in m['blocks']:b.update(kind='heading',level=1,heading_evidence=['explicit_label'])
        fs=audit_editorial(m)
        self.assertTrue(any(f['evidence'].get('reason')=='heading_density' for f in fs))
        self.assertEqual(classify(fs),'Intervenção necessária')

    def test_part_and_chapter_families_use_consistent_levels(self):
        ls=[]
        for p,t in enumerate(['Part I','Chapter 1','Chapter 2','Part II','Chapter 3','Chapter 4'],1):
            ls += [line(t,p,1,size=20),line('A full narrative paragraph accompanies this structural label.',p,2)]
        hs,_=document_structure(ls,profiles(ls))
        self.assertEqual([hs[l['id']]['level'] for l in ls if l['id'] in hs],[1,2,2,1,2,2])

    def test_local_reference_preserves_legitimate_entire_page_font_change(self):
        ls=novel()
        ls += [line('Smaller narrative text continues throughout this ordinary page.',8,i+1,10,top=40+i*15) for i in range(20)]
        self.assertEqual(profiles(ls)[8]['size'],10)

    def test_terminal_formula_and_unlabelled_duplicate_remain_nonstructural(self):
        ls=novel(contents=False)
        ls.append(line('THE END',8,1,12,'Bold'))
        hs,ctx=document_structure(ls,profiles(ls))
        self.assertNotIn('p8-l1',hs);self.assertEqual(ctx['closing'],['p8-l1'])
        ls.insert(0,line('THE END',1,1,12,'Bold'))
        hs,ctx=document_structure(ls,profiles(ls))
        self.assertNotIn('p8-l1',hs);self.assertFalse(ctx['closing'])
        self.assertIn('p8-l1',ctx['pending_titles'])

    def test_deeper_hierarchy_is_reviewed_instead_of_certified(self):
        ls=[]
        for p,t in enumerate(['Part I','Chapter 1','Section 1','Section 2','Part II','Chapter 2'],1):
            ls += [line(t,p,1,size=20),line('A full narrative paragraph accompanies this structural label.',p,2)]
        self.assertTrue(any(f['status']=='inconclusive' and f['evidence'].get('reason')=='hierarchy_depth' for f in audit_editorial(model_for(ls))))
