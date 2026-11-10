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
from .package import XHTML, EPUB, chapters, css, navigation_entries

NS = {'h': XHTML, 'o': 'http://www.idpf.org/2007/opf'}

def require(condition, message):
    if not condition:
        raise ValueError(message)

def audit_model(model):
    checks = []
    lines = model['lines']
    expected = [l['id'] for l in lines if not l.get('excluded')]
    actual = [s for b in model['blocks'] for s in b['source']]
    checks.append(finding('source_accounting', 'pass' if expected == actual else 'fail', 'blocking',
                          'Cada linha retida deve aparecer exatamente uma vez e na ordem original.'))
    by_id = {l['id']: l for l in lines}
    text_ok = True
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
        raw = ''.join(segments)
        if compact(raw) != compact(b['text']):
            text_ok = False
    checks.append(finding('source_text', 'pass' if text_ok else 'fail', 'blocking', 'Texto reconstruído deve coincidir com linhas de origem e transformações registradas.'))
    if model.get('schema',1)>=2:
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
    checks = audit_model(model)
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
