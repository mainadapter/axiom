"""Validation fixtures frozen before first execution of the revised motor.

Separate from development generators: independent PDF extraction, cardinal,
ordinal and Roman labels, different typography and repeated quotations. This
small authored set is not a representative population or a general success rate.
"""
import unittest
import test_booksmith as helpers
from book_epub.validate import audit_editorial
from book_epub.package import chapters


class EditorialValidation(helpers.BooksmithTests):
    def test_unseen_portuguese_ordinal_novel(self):
        labels=['CAPÍTULO OITAVO','CAPÍTULO NONO','CAPÍTULO DÉCIMO']
        def draw(c):
            c.setFont('Helvetica-Bold',32);c.drawCentredString(300,740,'AS PORTAS DO VALE')
            c.setFont('Helvetica',22);c.drawCentredString(300,660,'Uma autora imaginaria')
            c.showPage();c.setFont('Helvetica',16);c.drawCentredString(300,740,'SUMÁRIO')
            c.setFont('Helvetica',12)
            for i,label in enumerate(labels):c.drawCentredString(300,650-i*40,label.title())
            c.showPage()
            for label in labels:
                c.setFont('Helvetica',18);c.drawCentredString(300,740,label)
                c.setFont('Helvetica-Oblique',9)
                for i in range(15):c.drawString(70,680-i*12,'Uma citacao pequena descreve uma cidade distante e um antigo caminho.')
                c.setFont('Helvetica',13)
                for i,text in enumerate(['A viajante atravessou a ponte e encontrou um pequeno mercado',
                                         'onde todas as pessoas aguardavam a chegada de um barco.',
                                         'O marinheiro trouxe noticias das ilhas distantes e das tempestades.',
                                         'A conversa prosseguiu enquanto o sol desaparecia no horizonte.']):
                    c.drawString(40,460-i*17,text)
                c.showPage();c.setFont('Helvetica',13)
                for i in range(26):c.drawString(40,740-i*19,'Uma narrativa comum continua com outras palavras ao longo da viagem.')
                c.showPage()
        self.convert(draw)
        self.assertEqual([(b['text'],b['level']) for b in self.model['blocks'] if b['kind']=='heading'],[(l,1) for l in labels])
        self.assertEqual(len(chapters(self.model)),4)
        self.assertTrue(all(f['status']=='pass' for f in audit_editorial(self.model)))
        self.assertIsNotNone(self.report['epub_sha256'])

    def test_unseen_no_contents_roman_and_cardinal_chapters(self):
        for labels in [('Chapter IV','Chapter V'),('Chapter four','Chapter five')]:
            with self.subTest(labels=labels):
                # Each conversion has its own output to exercise the real CLI pipeline.
                def draw(c):
                    for label in labels:
                        c.setFont('Courier-Bold',19);c.drawCentredString(300,740,label)
                        c.setFont('Courier-Oblique',8)
                        for i in range(10):c.drawString(60,680-i*12,'A quiet quotation recalls a lighthouse beyond the shore.')
                        c.setFont('Courier',11)
                        for i in range(12):c.drawString(40,500-i*19,'The ordinary narrative continues along another quiet harbour.')
                        c.showPage()
                self.convert(draw)
                self.assertEqual([(b['text'],b['level']) for b in self.model['blocks'] if b['kind']=='heading'],[(l,1) for l in labels])
                self.assertTrue(all(f['status']=='pass' for f in audit_editorial(self.model)))
                import shutil
                shutil.rmtree(self.root/'v1')

for name in list(vars(helpers.BooksmithTests)):
    if name.startswith('test_') and name not in vars(EditorialValidation):setattr(EditorialValidation,name,None)
