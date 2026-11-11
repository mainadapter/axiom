"""Checks actual serialized EPUB, line accounting and external conformance evidence."""
import json
import base64
import io
from collections import Counter
from PIL import Image
import posixpath
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree as ET

from .common import compact, finding, digest
from .spacing import audit_spacing
from .evidence import explicit_facts, narrative_facts, isolated, explicit, typographic_facts
from .package import XHTML, EPUB, chapters, css, navigation_entries
from .structure import document_structure, profiles, roman_value

NS = {'h': XHTML, 'o': 'http://www.idpf.org/2007/opf'}

def require(condition, message):
    if not condition:
        raise ValueError(message)


def audit_editorial(model):
    """Source-context checks, independent of valid links and serialized model agreement.

    These bounded checks cannot certify every editorial choice. Legacy schema 1
    lacks the typography ledger; never manufacture retrospective evidence.
    """
    if model.get('schema',1)<2:
        return [finding('editorial_structure','unavailable','tolerable',
                        'Bundle histórico sem evidência tipográfica suficiente; modelo não migrado.')]
    lines=[l for l in model['lines'] if not l.get('excluded')]
    if not lines:
        return []
    source_headings, context=document_structure(lines, profiles(lines))
    by_source={s:b for b in model['blocks'] for s in b['source']}
    by_id={l['id']:l for l in lines}
    checks=[]
    def emit(status, impact, detail, ids, **extra):
        checks.append(finding('editorial_structure',status,impact,detail,
            source=ids, pages=sorted({by_id[i]['page'] for i in ids}),
            blocks=list(dict.fromkeys(by_source[i]['id'] for i in ids if i in by_source)), **extra))
    facts=explicit_facts(lines)
    negatives=narrative_facts(lines)
    repeated=typographic_facts(lines)
    for ident,level in facts['levels'].items():
        b=by_source.get(ident,{})
        if b.get('kind')!='heading' or b.get('level')!=level:
            emit('fail','blocking','Capítulo explícito contradiz a família de rótulos na fonte.',[ident],
                 reason='explicit_level',expected_level=level,source_label=facts['values'][ident])
    for issue in facts['issues']:
        emit('inconclusive','review','Índice original e rótulos explícitos da fonte divergem; conferir lacunas e escopo.' if issue['reason']=='contents_source_mismatch' else 'Mais de dois níveis estruturais na fonte; hierarquia não suportada exige revisão.',
             issue['source'],reason=issue['reason'])
    for ident,candidate in context.get('pending_titles',{}).items():
        promoted=by_source.get(ident,{}).get('kind')=='heading'
        emit('inconclusive','review',
             'Candidato sem corroboração promovido à navegação; reconverter para manter como texto.' if promoted else
             'Candidato tipográfico preservado como texto comum; confirmar intenção editorial antes de promover.',
             [ident],reason='ambiguous_title',decision='unsupported_promotion' if promoted else 'deferred',
             candidate_evidence=candidate['evidence'])
    for i,l in enumerate(lines):
        b=by_source.get(l['id'],{})
        if b.get('kind')!='heading' or l['id'] in facts['labels'] or l['id'] in repeated or l['id'] in context['parents'] or l['id'] in context['romans'] or l['id'] in context['frontmatter'] or l['id'] in context.get('pending_titles',{}) or any(e in source_headings.get(l['id'],{}).get('evidence',[]) for e in ('distinctive_title_body_transition','roman_subdivision_context','corroborated_title_family')):
            continue
        reasons=negatives.get(l['id'],[])
        # Repeated body typography AND adjacent prose/absent isolation prove a
        # contradiction. A dialogue-looking isolated title remains ambiguous.
        if reasons:
            proven=not isolated(lines,i) and {'continuous_prose_style','recurring_body_style'}<=set(reasons)
            emit('fail' if proven else 'inconclusive','blocking' if proven else 'review',
                 'Título contradiz continuidade narrativa.' if proven else 'Possível prosa/diálogo como título sem corroboração suficiente.',
                 [l['id']],reason='narrative_heading',source_evidence=reasons,
                 neighbours=[n['id'] for n in lines[max(0,i-1):i]+lines[i+1:i+2]])
        elif explicit(l['text']) and not isolated(lines,i):
            emit('inconclusive','review','Rótulo explícito sem isolamento ou família corroborada.',[l['id']],reason='unconfirmed_label')
        elif not explicit(l['text']):
            emit('inconclusive','review','Título tipográfico sem padrão estrutural corroborado; confirmar intenção editorial.',
                 [l['id']],reason='ambiguous_title')
    for page in sorted({l['page'] for l in lines}):
        ls=[l for l in lines if l['page']==page]
        suspects=[l['id'] for l in ls if by_source.get(l['id'],{}).get('kind')=='heading' and
                  l['id'] not in facts['labels'] and l['id'] not in context['romans'] and l['id'] not in context['parents']]
        if len(suspects)>=6 and len(suspects)>=len(ls)*.25:
            emit('inconclusive','review','Concentração anormal de títulos sem corroboração estrutural.',suspects,
                 reason='heading_density',headings=len(suspects),retained_lines=len(ls))
    for ident in context['parents']:
        b=by_source.get(ident,{})
        if b.get('kind')!='heading' or b.get('level')!=1:
            emit('fail','blocking','Título principal contradiz padrões narrativos recorrentes na fonte.',[ident],reason='parent_level')
    for ident in context['frontmatter']:
        b=by_source.get(ident,{})
        if b.get('kind')=='heading' or b.get('content_role')!='frontmatter':
            emit('fail','blocking','Pré-texto confirmado pelo índice foi tratado como estrutura narrativa.',[ident],reason='frontmatter_role')
    for ident in context.get('closing',[]):
        if by_source.get(ident,{}).get('kind')=='heading':
            emit('inconclusive','review','Fórmula terminal em tipografia de corpo promovida à navegação.',[ident],reason='closing_heading')
    for ident in context['backmatter']:
        b=by_source.get(ident,{})
        if b.get('kind')=='heading' or b.get('content_role')!='backmatter':
            emit('fail','blocking','Informações editoriais finais confirmadas pela fonte sem separação da narrativa.',[ident],reason='backmatter_role')
    if context['parents'] and not context['frontmatter'] and lines[0]['id']!=context['parents'][0]:
        emit('inconclusive','review','Material anterior aos ciclos narrativos sem confirmação suficiente de pré-texto.',
             [lines[0]['id'],context['parents'][0]],reason='uncertain_frontmatter')
    parent=None
    previous=0
    for l in lines:
        b=by_source.get(l['id'],{})
        if b.get('kind')=='heading' and b.get('level')==1 and roman_value(l['text']) is None:
            parent=l['id']; previous=0
        if l['id'] not in context['romans']:
            continue
        value=roman_value(l['text'])
        ids=([parent] if parent else [])+[l['id']]
        if b.get('kind')!='heading' or b.get('level')!=2:
            emit('fail' if parent else 'inconclusive','blocking' if parent else 'review',
                 'Subdivisão romana sem nível subordinado confirmado.',ids,reason='roman_level')
        if parent is None or value!=previous+1:
            emit('inconclusive','review','Sequência romana sem pai ou com salto/reinício não explicado.',ids,
                 reason='roman_sequence',previous=previous,observed=value)
        previous=value
    if not checks:
        emit('pass','review','Verificações contextuais limitadas: rótulos explícitos, índice, continuidade narrativa e ciclos romanos sem contradição detectada; não é certificação editorial universal.',
             context['parents'] or [lines[0]['id']],parents=len(context['parents']),romans=len(context['romans']))
    return checks

def audit_model(model):
    checks = []
    lines = model['lines']
    expected = [l['id'] for l in lines if not l.get('excluded')]
    actual = [s for b in model['blocks'] for s in b['source']]
    checks.append(finding('source_accounting', 'pass' if expected == actual else 'fail', 'blocking',
                          'Cada linha retida deve aparecer exatamente uma vez e na ordem original.'))
    by_id = {l['id']: l for l in lines}
    text_ok = True
    spacing_bad = []
    tight_pairs = {tuple(t['source']) for t in model['transformations']
                   if t['kind'] in ('dehyphenate','join_preserving_hyphen')}
    for b in model['blocks']:
        segments = [by_id[s]['text'] for s in b['source']]
        for t in model['transformations']:
            if t['kind'] == 'dehyphenate' and all(s in b['source'] for s in t['source']):
                a, z = t['source']
                index = b['source'].index(a)
                if index+1 >= len(segments) or b['source'][index+1] != z or not segments[index].endswith(('-', '\u00ad')):
                    text_ok = False
                else:
                    segments[index] = segments[index][:-1]
        if model.get('schema',1)>=2:
            reconstructed = ''
            for index, segment in enumerate(segments):
                pair=b['source'][index-1:index+1]
                tight = index and tuple(pair) in tight_pairs
                reconstructed += ('' if index==0 or tight else ' ') + segment
            if reconstructed != b['text']:
                spacing_bad.append(b['id'])
        raw = ''.join(segments)
        if compact(raw) != compact(b['text']):
            text_ok = False
    checks.append(finding('source_text', 'pass' if text_ok else 'fail', 'blocking', 'Texto reconstruído deve coincidir com linhas de origem e transformações registradas.'))
    if model.get('schema',1)>=2:
        checks.append(finding('source_word_boundaries','fail' if spacing_bad else 'pass','blocking',
            'Espaços dos blocos devem reproduzir as linhas e junções registradas, sem ignorar separadores.',blocks=spacing_bad))
        try:
            assets=model.get('assets',[])
            require(Counter(model.get('image_sources',[]))==Counter(a['id'] for a in assets), 'Imagem de origem ausente ou duplicada')
            refs=[b['asset'] for b in model['blocks'] if b['kind']=='image']
            require(Counter(refs)==Counter(a['id'] for a in assets), 'Ocorrência de imagem ausente ou duplicada no modelo')
            for a in assets:
                raw=base64.b64decode(a['data_base64'],validate=True)
                require(digest(raw)==a['sha256'], 'Hash de imagem divergente')
                with Image.open(io.BytesIO(raw)) as im:
                    require(im.format=='PNG' and im.size==(a['width'],a['height']), 'Formato/dimensões de imagem divergentes')
                    im.verify()
            for b in model['blocks']:
                if b['kind']=='image':
                    a=next(a for a in assets if a['id']==b['asset'])
                    require(b.get('display_width_percent')==a.get('display_width_percent'), 'Dimensionamento de imagem divergente')
                    page=next(p for p in model['pages'] if p['page']==a['page'])
                    width=round(min(80 if a['cover'] else 100,100*(a['bbox'][2]-a['bbox'][0])/page['width'],100*a['width']/a['height']),3)
                    require(width==a['display_width_percent'],'Dimensionamento fora do limite responsivo')
                    require(bool(b.get('cover'))==bool(a.get('cover')), 'Papel de capa diverge do asset')
                    preceding=[s for item in model['blocks'][:model['blocks'].index(b)] for s in item['source']]
                    before=[l['id'] for l in lines if not l.get('excluded') and (l['page'],l['top'])<(a['page'],a['bbox'][1])]
                    require(preceding==before, 'Imagem deslocada relativamente às linhas de origem')
                else:
                    require(''.join(s['text'] for s in b['spans'])==b['text'], 'Trechos tipográficos divergentes do texto')
                    expected=[]
                    for ident in b['source']:
                        ss=[dict(s) for s in by_id[ident]['spans']]
                        if any(t['kind']=='dehyphenate' and t['source'][0]==ident and all(x in b['source'] for x in t['source']) for t in model['transformations']):
                            ss[-1]['text']=ss[-1]['text'][:-1]
                        expected.extend(styled_characters(ss))
                    require(expected==styled_characters(b['spans']), 'Ênfase difere dos trechos da fonte')
            checks.append(finding('source_images_semantics','pass','blocking','Imagens, ordem relativa e trechos tipográficos conferidos contra a origem.'))
        except (ValueError,KeyError,StopIteration,OSError,TypeError) as error:
            checks.append(finding('source_images_semantics','fail','blocking',str(error)))
    return checks


def styled_characters(spans):
    return [(c,bool(s.get('bold')),bool(s.get('italic'))) for s in spans for c in s['text'] if not c.isspace()]


def observed_styles(element, bold=False, italic=False):
    bold=bold or element.tag==f'{{{XHTML}}}strong'
    italic=italic or element.tag==f'{{{XHTML}}}em'
    result=[(c,bold,italic) for c in element.text or '' if not c.isspace()]
    for child in element:
        result.extend(observed_styles(child,bold,italic))
        result.extend((c,bold,italic) for c in child.tail or '' if not c.isspace())
    return result


def epubcheck(path, command=None):
    command = command or ([shutil.which('epubcheck')] if shutil.which('epubcheck') else None)
    if command is None:
        return finding('epubcheck', 'unavailable', 'review', 'EPUBCheck não está disponível; conformidade completa não verificada.')
    with tempfile.TemporaryDirectory() as tmp:
        report = Path(tmp) / 'check.json'
        try:
            result = subprocess.run([*command, str(Path(path).resolve()), '--json', str(report)], capture_output=True, text=True, timeout=120)
        except (OSError, subprocess.TimeoutExpired) as error:
            return finding('epubcheck', 'unavailable', 'review', 'EPUBCheck não pôde concluir.', reason=str(error))
        if not report.exists():
            return finding('epubcheck', 'inconclusive', 'review', 'EPUBCheck não produziu relatório estruturado.', returncode=result.returncode, stderr=result.stderr[-2000:])
        try:
            data = json.loads(report.read_text())
        except (ValueError, OSError):
            return finding('epubcheck', 'inconclusive', 'review', 'Relatório EPUBCheck ilegível.')
        checker = data.get('checker', {}) if isinstance(data, dict) else {}
        if not isinstance(checker, dict) or not checker.get('checkerVersion') or not isinstance(data.get('messages'), list) or any(not isinstance(checker.get(k), int) for k in ('nFatal', 'nError', 'nWarning', 'nUsage')):
            return finding('epubcheck', 'inconclusive', 'review', 'Relatório EPUBCheck incompleto; não é prova de conformidade.')
        messages = data['messages']
        if any(not isinstance(m, dict) or m.get('severity', '').upper() not in ('INFO', 'WARNING', 'ERROR', 'FATAL', 'USAGE', 'SUPPRESSED') for m in messages):
            return finding('epubcheck', 'inconclusive', 'review', 'Mensagens EPUBCheck não reconhecidas.')
        errors = [m for m in messages if m.get('severity', '').upper() in ('ERROR', 'FATAL')]
        warnings = [m for m in messages if m.get('severity', '').upper() == 'WARNING']
        if errors or checker['nError'] or checker['nFatal']:
            status, impact = 'fail', 'blocking'
        elif result.returncode != 0 or checker['nUsage']:
            status, impact = 'inconclusive', 'review'
        elif warnings or checker['nWarning']:
            status, impact = 'inconclusive', 'review'
        else:
            status, impact = 'pass', 'review'
        return finding('epubcheck', status, impact, 'Validação de conformidade EPUB; não certifica fidelidade editorial.', report=data, returncode=result.returncode)

def validate(path, model, profile, settings, labels=None, command=None):
    checks = audit_model(model) + audit_editorial(model) + audit_spacing(model)
    try:
        with zipfile.ZipFile(path) as z:
            names = z.namelist()
            require(len(names) == len(set(names)), 'Duplicate ZIP member')
            require(names[0] == 'mimetype' and z.read('mimetype') == b'application/epub+zip', 'mimetype missing or wrong')
            require(z.getinfo('mimetype').compress_type == zipfile.ZIP_STORED, 'Compressed mimetype')
            require(z.testzip() is None, 'CRC mismatch')
            members = {n: z.read(n) for n in names}
        trees = {n: ET.fromstring(data) for n, data in members.items() if n.endswith(('.xml', '.opf', '.xhtml'))}
        container = trees['META-INF/container.xml']
        roots = container.findall('.//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile')
        require(len(roots) == 1 and roots[0].get('full-path') == 'EPUB/package.opf', 'Wrong container root')
        opf = trees['EPUB/package.opf']
        manifest = {e.get('id'): e for e in opf.findall('o:manifest/o:item', NS)}
        require(len(manifest) == len(opf.findall('o:manifest/o:item', NS)), 'Duplicate manifest ID')
        require(all('EPUB/' + e.get('href') in members for e in manifest.values()), 'Missing manifest resource')
        spine = [manifest[e.get('idref')].get('href') for e in opf.findall('o:spine/o:itemref', NS)]
        require(spine == [c['name'] for c in chapters(model)], 'Wrong spine sequence')
        observed = []
        observed_elements=[]
        for name in spine:
            body = trees['EPUB/' + name].find('h:body', NS)
            for el in body:
                observed.append((el.get('id'), ''.join(el.itertext())))
                observed_elements.append(el)
        expected = [(b['id'], b['text']) for b in model['blocks']]
        require(observed == expected, 'Text lost, duplicated, changed or displaced')
        if model.get('schema',1)>=2:
            all_images=[el.get('src') for name in spine for el in trees['EPUB/'+name].findall('.//h:img',NS)]
            require(all_images==[f'images/{b["asset"]}.png' for b in model['blocks'] if b['kind']=='image'],'Unexpected, repeated or missing serialized image')
            for b,el in zip(model['blocks'],observed_elements):
                if b['kind']=='image':
                    require(el.tag==f'{{{XHTML}}}figure','Imagem fora de figure')
                    require((el.get('class')=='cover')==bool(b.get('cover')),'Apresentação de capa divergente')
                    images=el.findall('h:img',NS)
                    require(len(images)==1 and images[0].get('src')==f'images/{b["asset"]}.png','Imagem alterada ou deslocada')
                    require(images[0].get('style')==f"width: {b['display_width_percent']:.3f}%;",'Dimensionamento serializado divergente')
                else:
                    tag='h'+str(b.get('level',1)) if b['kind']=='heading' else 'blockquote' if b['kind']=='quote' else 'p'
                    require(el.tag==f'{{{XHTML}}}'+tag,'Hierarquia ou semântica de bloco alterada')
                    require(observed_styles(el)==styled_characters(b['spans']),'Ênfase serializada divergente')
                    if b['kind']=='separator': require(el.get('class')=='separator','Separador sem apresentação preservada')
            for a in model.get('assets',[]):
                require(digest(members[f'EPUB/images/{a["id"]}.png'])==a['sha256'],'Imagem serializada alterada')
                entry=manifest.get(a['id'])
                require(entry is not None and entry.get('media-type')=='image/png' and entry.get('href')==f'images/{a["id"]}.png','Manifesto de imagem divergente')
                require((entry.get('properties')=='cover-image')==bool(a.get('cover')),'Metadados de capa divergentes')
            checks.append(finding('serialized_images_semantics','pass','blocking','Imagens, capa, hierarquia e ênfase verificadas no pacote real.'))
        checks.append(finding('serialized_text', 'pass', 'blocking', 'Texto e ordem dos blocos conferidos no EPUB serializado.'))
        for name, tree in trees.items():
            ids = [e.get('id') for e in tree.iter() if e.get('id')]
            require(len(ids) == len(set(ids)), f'Duplicate ID in {name}')
            for element in tree.iter():
                for attr in ['href', 'src']:
                    link = element.get(attr)
                    if link is None:
                        continue
                    parsed = urlsplit(link)
                    require(not parsed.scheme and not parsed.netloc, 'External resource unsupported')
                    target = posixpath.normpath(posixpath.join(posixpath.dirname(name), unquote(parsed.path))) if parsed.path else name
                    require(target in members, f'Broken reference {link}')
                    if parsed.fragment:
                        require(any(e.get('id') == unquote(parsed.fragment) for e in trees[target].iter()), f'Broken anchor {link}')
        nav = trees['EPUB/nav.xhtml'].find(f'.//h:nav[@{{{EPUB}}}type="toc"]', NS)
        require(nav is not None, 'No toc')
        links = nav.findall('.//h:a', NS)
        entries = navigation_entries(model)
        require([a.get('href') for a in links] == [e['href'] for e in entries], 'Incomplete or unordered TOC')
        require([''.join(a.itertext()) for a in links] == [(labels or {}).get(e['id'],e['label']) for e in entries], 'Wrong navigation labels')
        parents={child:parent for parent in nav.iter() for child in parent}
        for a,e in zip(links,entries):
            depth=0
            node=a
            while node in parents:
                node=parents[node]
                if node.tag==f'{{{XHTML}}}ol': depth+=1
            require(depth==e['level'],'Wrong TOC hierarchy')
        require(members['EPUB/style.css'] == css(profile, **settings)[0], 'CSS differs from validated bounded template')
        require(model['blocks'], 'Empty spine')
        checks.append(finding('package_navigation_css', 'pass', 'blocking', 'ZIP/XML, spine, links, âncoras, sumário e CSS restrito conferidos.'))
    except (AssertionError, KeyError, ValueError, AttributeError, TypeError, ET.ParseError, zipfile.BadZipFile) as error:
        checks.append(finding('package_navigation_css', 'fail', 'blocking', str(error)))
    checks.append(epubcheck(path, command))
    return checks
