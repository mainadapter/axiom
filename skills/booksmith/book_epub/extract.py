"""Geometry-aware extraction with a retained line ledger; no generative rewriting."""
import math
import re
import statistics
from collections import Counter

import pdfplumber
from pypdf import PdfReader

from .common import compact, finding
from .images import capture
from .structure import profiles, document_structure, font_style, append_spans, quote_runs

HEADING = re.compile(r'^(?:cap[ií]tulo|chapter|parte|part|se[cç][aã]o|section)\s+(?:\d+|[IVXLCDM]+)\b', re.I)

def extract(path):
    lines, findings, transforms, pages, assets, image_sources = [], [], [], [], [], []
    try:
        reader = PdfReader(str(path))
    except Exception:
        reader = None
    with pdfplumber.open(path) as pdf:
        for pi, page in enumerate(pdf.pages, 1):
            chars = [c for c in page.chars if c.get('text', '').strip()]
            if not chars:
                status = 'fail' if (page.curves or page.rects) and not page.images else 'pass'
                findings.append(finding('textless_page', status, 'blocking' if status == 'fail' else 'tolerable',
                                        'Página sem texto extraível; OCR não implementado.' if status == 'fail' else 'Página vazia preservada no registro.', page=pi))
            image_sources.extend(f'p{pi}-img{i}' for i in range(1,len(page.images)+1))
            assets.extend(capture(page, pi, findings, transforms, len(pdf.pages)))
            if page.curves or len(page.lines) > 2 or len(page.rects) > 2:
                findings.append(finding('graphics', 'inconclusive', 'review', 'Elementos vetoriais ou estrutura tabular exigem inspeção.', page=pi))
            if any(not c.get('upright', True) for c in chars):
                findings.append(finding('rotated_text', 'fail', 'blocking', 'Texto rotacionado fora do MVP.', page=pi))
            spaces = [c for c in page.chars if c.get('text', '').isspace()]
            rows = []
            for char in sorted(chars, key=lambda c: (c['top'], c['x0'])):
                row = next((r for r in reversed(rows[-3:]) if abs(r[0]['top'] - char['top']) < 3), None)
                if row is None:
                    rows.append([char])
                else:
                    row.append(char)
            page_lines = []
            big_gaps = 0
            for row in rows:
                row.sort(key=lambda c: c['x0'])
                size = statistics.median(c['size'] for c in row)
                text = ''
                spans = []
                gaps = []
                for j, char in enumerate(row):
                    fragment = ''
                    if j:
                        gap = char['x0'] - row[j-1]['x1']
                        gaps.append(gap)
                        # Preserve an explicit PDF separator even when kerning or
                        # glyph metrics make its visible advance smaller than the
                        # geometric fallback. Never lower the global gap threshold.
                        explicit_spaces = [s for s in spaces
                            if abs(s['top'] - char['top']) < 3
                            and row[j-1]['x0'] < s['x0'] < char['x0']]
                        geometric = gap > max(1.5, size * .18)
                        if explicit_spaces or geometric:
                            fragment += ' '
                        if explicit_spaces and not geometric:
                            transforms.append(dict(kind='preserve_explicit_space',
                                source=[f'p{pi}-l{len(page_lines)+1}'], offset=len(text),
                                gap=round(gap,6), threshold=max(1.5,size*.18),
                                space_bbox=[[s['x0'],s['top'],s['x1'],s['bottom']] for s in explicit_spaces],
                                reason='literal_pdf_whitespace'))
                    fragment += char['text']
                    text += fragment
                    append_spans(spans, [dict(text=fragment, **font_style(char.get('fontname','')))])
                if max(gaps, default=0) > max(36, size * 3):
                    big_gaps += 1
                fonts = sorted({c.get('fontname', '') for c in row})
                line = dict(spans=spans, fonts=fonts, id=f'p{pi}-l{len(page_lines)+1}', page=pi, text=text,
                            x0=round(row[0]['x0'], 3), x1=round(max(c['x1'] for c in row), 3),
                            top=round(min(c['top'] for c in row), 3), bottom=round(max(c['bottom'] for c in row), 3),
                            size=round(size, 3), width=page.width, height=page.height)
                page_lines.append(line)
            if big_gaps >= 2:
                findings.append(finding('columns', 'fail', 'blocking', 'Múltiplas linhas com separação horizontal incompatível com prosa simples.', page=pi, lines=big_gaps))
            try:
                independent = reader.pages[pi-1].extract_text() or '' if reader is not None else None
            except Exception:
                independent = None
            if independent is None:
                findings.append(finding('independent_extraction', 'unavailable', 'review',
                                        'Extração independente indisponível nesta página.', page=pi))
            else:
                same = compact(' '.join(l['text'] for l in page_lines)) == compact(independent)
                findings.append(finding('independent_extraction', 'pass' if same else 'inconclusive', 'review',
                                        'Comparação por página com pypdf, ignorando apenas espaços e ligaturas.', page=pi))
            pages.append(dict(page=pi, literal_text=''.join(c['text'] for c in page.chars), independent_text=independent, width=page.width, height=page.height))
            lines.extend(page_lines)
    if not lines:
        findings.append(finding('empty_document', 'fail', 'blocking', 'Nenhum conteúdo textual extraível.'))
        return dict(lines=[], blocks=[], pages=pages, findings=findings, transformations=transforms, assets=assets, image_sources=image_sources)
    body_size = Counter(round(l['size'], 1) for l in lines).most_common(1)[0][0]
    def margin(l):
        if l['top'] < l['height'] * .08:
            return 'top'
        if l['bottom'] > l['height'] * .92:
            return 'bottom'
        return None
    threshold = max(3, math.ceil(len(pages) * .6))
    margin_pages = {}
    for l in lines:
        margin_pages.setdefault((margin(l), l['text']), set()).add(l['page'])
    kept = []
    for l in lines:
        zone = margin(l)
        page_number = bool(zone and re.fullmatch(r'\d+', l['text']) and int(l['text']) == l['page'])
        repeated_margin = zone and len(margin_pages[(zone, l['text'])]) >= threshold and not HEADING.match(l['text']) and not (l['text'].isupper() and len(l['text']) < 100)
        if page_number or repeated_margin:
            l['excluded'] = 'page_number' if page_number else 'repeated_margin'
            transforms.append(dict(kind='exclude_running_matter', source=[l['id']], original=l['text'], reason=l['excluded']))
        else:
            if zone and re.fullmatch(r'(?:[0-9]+|[ivxlcdmIVXLCDM]+)', l['text']):
                findings.append(finding('unresolved_pagination', 'inconclusive', 'review', 'Possível paginação com offset ou numeral romano; texto mantido.', source=l['id']))
            kept.append(l)
    if not kept:
        findings.append(finding('no_body', 'fail', 'blocking', 'Todo o texto foi classificado como margem; inspeção necessária.'))
    vocabulary = set(re.findall(r'\b[\wÀ-ÿ]+(?:-[\wÀ-ÿ]+)?\b', ' '.join(l['text'] for l in kept)))
    layout = profiles(kept)
    hs, editorial = document_structure(kept, layout)
    frontmatter = set(editorial['frontmatter'])
    backmatter = set(editorial['backmatter'])
    findings = [f for f in findings if not (f['code']=='unresolved_pagination' and 'roman_layout' in hs.get(f['evidence'].get('source'),{}).get('evidence',[]))]
    quotes, possible_quotes = quote_runs(kept, layout, hs)
    blocks = []
    body_lines = [l for l in kept if l['id'] not in hs]
    for pi in sorted({l['page'] for l in body_lines}):
        prose = [l for l in body_lines if l['page'] == pi]
        size = layout[pi]['size']
        cues = any(b['top']-a['bottom'] > size*.75 or abs(b['x0']-a['x0']) > size*.75
                   or re.match(r'^[—–](?![—–])', b['text']) for a,b in zip(prose,prose[1:]))
        if len(prose)>=2 and not cues:
            findings.append(finding('paragraph_layout','inconclusive','review',
                'Prosa sem evidências positivas de limites de parágrafos; revisão necessária.',page=pi))
    # Image events share the reading stream and force paragraph boundaries.
    events = [(l['page'], l['top'], 1, l) for l in kept]
    events += [(a['page'], a['bbox'][1], 0, a) for a in assets]
    events.sort(key=lambda e:e[:3])
    previous = None
    for _, _, event_kind, l in events:
        if event_kind == 0:
            blocks.append(dict(id=f'b{len(blocks)+1}', kind='image', text='', source=[], asset=l['id'], cover=l['cover'], display_width_percent=l['display_width_percent']))
            if frontmatter and l['page'] < next(x['page'] for x in kept if x['id']==editorial['parents'][0]):
                blocks[-1]['content_role']='frontmatter'
            if backmatter and l['page'] >= next(x['page'] for x in kept if x['id']==editorial['backmatter'][0]):
                blocks[-1]['content_role']='backmatter'
            previous = None
            continue
        p = layout[l['page']]
        body_size, left, right = p['size'], p['left'], p['right']
        heading = l['id'] in hs
        if re.match(r'^[“"«]', l['text']):
            findings.append(finding('quotation', 'inconclusive', 'review', 'Possível citação ou diálogo: sinais textuais preservados, sem marcação semântica específica.', source=l['id']))
        if any(c in l['text'] for c in '∑∫√≈≠≤≥∂∞'):
            findings.append(finding('formula', 'inconclusive', 'review', 'Possível expressão matemática; sem reconstrução semântica no MVP.', source=l['id']))
        if l['size'] < body_size * .8:
            findings.append(finding('small_text', 'inconclusive', 'review', 'Possível nota ou elemento especial; texto mantido, vínculo não inferido.', source=l['id']))
        if any(ord(c) < 32 and not c.isspace() or c == '\ufffd' for c in l['text']):
            findings.append(finding('invalid_glyph', 'fail', 'blocking', 'Caractere inválido na extração.', source=l['id']))
        new = previous is None or heading or l['id'] in frontmatter or (l['id'] in backmatter and previous['id'] not in backmatter) or blocks[-1]['kind'] in ('heading','separator')
        separator = bool(re.fullmatch(r'(?:\*\s*){3,}|[•·]{3,}|[—–]{3,}',l['text']))
        dialogue = bool(re.match(r'^[—–](?![—–])', l['text']))
        if separator or dialogue:
            new = True
        quote = l['id'] in quotes
        if previous and quote != (previous['id'] in quotes):
            new = True
        if previous and not new:
            if l['page'] == previous['page']:
                gap = l['top'] - previous['bottom']
                indented_run = quote and previous['id'] in quotes
                new = gap > body_size * .75 or (l['x0'] > left + body_size*.75 and not indented_run)
                if l['id'] in possible_quotes and previous['id'] in possible_quotes and gap <= body_size * .75:
                    findings.append(finding('indented_run', 'inconclusive', 'review', 'Possível citação em bloco ou estrutura recuada; semântica requer revisão.', source=[previous['id'], l['id']]))
                if not new and previous['x1'] < right - body_size * 4 and re.search(r'[.!?][”’"\)]?$', previous['text']):
                    new = True
                    findings.append(finding('paragraph_boundary', 'inconclusive', 'review', 'Linha curta com fim de frase sem espaçamento ou recuo: possível limite de parágrafo.', source=[previous['id'], l['id']]))
            else:
                # Strong continuation: unclosed sentence, full preceding line and no new indent.
                continuation = not re.search(r'[.!?:;][”’"\)]?$', previous['text']) and previous['x1'] >= right - body_size * 2 and l['x0'] <= left + body_size
                new = not continuation
                if not continuation and l['x0'] <= left + body_size*.75:
                    findings.append(finding('page_boundary', 'inconclusive', 'review', 'Continuação de parágrafo entre páginas incerta; separação mantida.', source=[previous['id'], l['id']]))
        if new:
            kind = 'heading' if heading else 'separator' if separator else 'quote' if quote else 'paragraph'
            block = dict(id=f'b{len(blocks)+1}', kind=kind, text=l['text'], source=[l['id']], spans=[dict(s) for s in l['spans']])
            if l['id'] in frontmatter:
                block['content_role']='frontmatter'
            if l['id'] in backmatter:
                block['content_role']='backmatter'
            if heading:
                block.update(level=hs[l['id']]['level'], heading_evidence=hs[l['id']]['evidence'])
                if block['level']>1 and not any(b['kind']=='heading' and b.get('level',1)==1 for b in blocks):
                    block['level']=1
                    findings.append(finding('heading_hierarchy','inconclusive','review','Título subordinado sem título pai; conteúdo preservado em nível superior.',source=l['id']))
            if dialogue: block['dialogue']=True
            blocks.append(block)
            transforms.append(dict(kind='start_block', source=[l['id']], block=block['id'],
                                    reason='heading' if heading else 'separator' if separator else 'dialogue' if dialogue else 'layout'))
        else:
            block = blocks[-1]
            old = block['text']
            match = re.search(r'([\wÀ-ÿ]+)([-\u00ad])$', old)
            first = re.match(r'([\wÀ-ÿ]+)', l['text'])
            if match and first:
                joined = match[1] + first[1]
                hyphenated = match[1] + '-' + first[1]
                if match[2] == '\u00ad' or (joined in vocabulary and hyphenated not in vocabulary):
                    block['text'] = old[:-1] + l['text']
                    transforms.append(dict(kind='dehyphenate', source=[previous['id'], l['id']], original=match[0]+' '+first[0], replacement=joined))
                else:
                    block['text'] = old + l['text']
                    transforms.append(dict(kind='join_preserving_hyphen', source=[previous['id'], l['id']]))
                    findings.append(finding('hyphenation', 'inconclusive', 'review', 'Hífen preservado; não há evidência suficiente para removê-lo.', source=[previous['id'], l['id']]))
            else:
                block['text'] += ' ' + l['text']
                transforms.append(dict(kind='join_lines', source=[previous['id'], l['id']]))
            suffix = block['text'][len(old):]
            if not block['text'].startswith(old):
                # Only the explicitly logged terminal hyphen may be removed.
                block['spans'][-1]['text'] = block['spans'][-1]['text'][:-1]
            elif suffix.startswith(' '):
                append_spans(block['spans'], [dict(text=' ', bold=False, italic=False)])
            append_spans(block['spans'], l['spans'])
            block['source'].append(l['id'])
        previous = l
    for block in blocks:
        if len(block['text']) > 8000:
            findings.append(finding('long_paragraph', 'inconclusive', 'review', 'Parágrafo acima de 8000 caracteres.', block=block['id']))
    if not any(b['kind'] == 'heading' for b in blocks):
        findings.append(finding('no_headings', 'inconclusive', 'review', 'Nenhum título reconhecido; sumário terá entrada única.'))
    findings.append(finding('device_test', 'unavailable', 'tolerable', 'Leitor físico e serviço Send to Kindle não testados.'))
    return dict(lines=lines, blocks=blocks, pages=pages, findings=findings, transformations=transforms, assets=assets, image_sources=image_sources,
                editorial_structure=editorial)
