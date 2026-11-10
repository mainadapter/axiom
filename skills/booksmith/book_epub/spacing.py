"""Conservative boundary audit against literal PDF glyphs and a second parser.

No dictionary or book-specific rules. A literal separator AND pypdf agreement
prove a lost boundary only when all non-whitespace characters align exactly.
Differences without that evidence remain review items, never automatic edits.
"""
import re
from .common import compact, finding, digest


def boundaries(text):
    result, offset = set(), 0
    for part in re.split(r'(\s+)', text):
        if part.isspace():
            result.add(offset)
        else:
            offset += len(compact(part))
    return result - {0, offset}


def audit_spacing(model, source=None):
    """Use saved literal glyph text; optionally reread the original for old bundles.

    This checks the source line ledger independently of its reconstruction. The
    existing source/serialized audits then check blocks and actual EPUB text.
    """
    pages = model.get('pages', [])
    if source is not None:
        from pathlib import Path
        if model.get('source_sha256') and digest(Path(source).read_bytes()) != model['source_sha256']:
            raise ValueError('Original PDF hash differs from bundle source')
        import pdfplumber
        from pypdf import PdfReader
        reader = PdfReader(str(source))
        with pdfplumber.open(source) as pdf:
            pages = [dict(page=i, literal_text=''.join(c['text'] for c in p.chars),
                          independent_text=reader.pages[i-1].extract_text() or '')
                     for i,p in enumerate(pdf.pages, 1)]
    checks = []
    block_ids = {s:b['id'] for b in model.get('blocks',[]) for s in b['source']}
    for page in pages:
        pi = page['page']
        if 'literal_text' not in page:
            checks.append(finding('word_spacing','unavailable','review',
                'Bundle sem registro literal de espaços; reauditar com o PDF original.',page=pi))
            continue
        lines = [l for l in model['lines'] if l['page']==pi]
        text = ' '.join(l['text'] for l in lines)
        literal, independent = page['literal_text'], page.get('independent_text')
        if independent is None or not (compact(text)==compact(literal)==compact(independent)):
            checks.append(finding('word_spacing','inconclusive','review',
                'Sequências de caracteres não alinháveis; espaços não classificados automaticamente.',page=pi,reason='unaligned'))
            continue
        actual, other, explicit = boundaries(text), boundaries(independent), boundaries(literal)
        missing, extra = other-actual, actual-other
        confirmed = missing & explicit
        # Literal whitespace is authoritative even if the other parser misses it;
        # without corroboration this stays inconclusive rather than blocking.
        unresolved_literal = explicit-actual-other
        def emit(offset, category, status, impact):
            n=0
            line=None
            for candidate in lines:
                end=n+len(compact(candidate['text']))
                if n < offset < end:
                    line=candidate;break
                n=end
            stream=compact(text)
            evidence=dict(page=pi,offset=offset,reason=category,
                          produced=stream[max(0,offset-12):offset]+'|'+stream[offset:offset+12],
                          expected_boundary='space' if status=='fail' else 'undetermined')
            if line:
                local_offset=offset-n
                display_index=next((i for i in range(len(line['text'])+1)
                    if len(compact(line['text'][:i]))==local_offset),len(line['text']))
                evidence['produced']=line['text']
                if category in ('explicit_missing','literal_uncorroborated','geometric_or_extractor'):
                    evidence['expected' if status=='fail' else 'candidate']=line['text'][:display_index]+' '+line['text'][display_index:]
                evidence.update(source=line['id'],block=block_ids.get(line['id']),
                                line_offset=offset-n,line_text=line['text'],
                                bbox=[line['x0'],line['top'],line['x1'],line['bottom']])
            checks.append(finding('word_spacing',status,impact,
                'Espaço literal perdido, corroborado por pypdf.' if status=='fail' else
                'Diferença antes de pontuação, sem espaço literal: não caracteriza fusão de palavras; pontuação adjacente preservada.' if category=='punctuation_difference' else
                'Fronteira divergente sem prova suficiente para corrigir automaticamente.',**evidence))
        for offset in sorted(confirmed):emit(offset,'explicit_missing','fail','blocking')
        for offset in sorted(missing-explicit):
            # No letters are merged here: pypdf often inserts whitespace at
            # a font/text-operator transition immediately before punctuation.
            # Do not add that whitespace or claim a word-fidelity failure.
            if compact(text)[offset] in '.,;:!?)]}':
                emit(offset,'punctuation_difference','pass','tolerable')
            else:
                emit(offset,'geometric_or_extractor','inconclusive','review')
        for offset in sorted(extra):emit(offset,'engine_only_boundary','inconclusive','review')
        for offset in sorted(unresolved_literal):emit(offset,'literal_uncorroborated','inconclusive','review')
        if not (missing or extra or unresolved_literal):
            checks.append(finding('word_spacing','pass','review',
                'Fronteiras de palavras concordam com pypdf; sem perda de espaço literal detectada.',page=pi))
    return checks
