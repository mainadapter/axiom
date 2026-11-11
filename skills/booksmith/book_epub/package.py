"""Small EPUB 3 writer using standard XML/ZIP libraries, with stable member bytes."""
from html import escape
import base64
import math
from pathlib import PurePosixPath
import zipfile

from .common import digest, serialized

XHTML = 'http://www.w3.org/1999/xhtml'
EPUB = 'http://www.idpf.org/2007/ops'
PROFILES = {'generic': {'paragraph_gap': .6, 'indent': 0}, 'kindle': {'paragraph_gap': .6, 'indent': 0}}

def css(profile='generic', paragraph_gap=None, indent=None):
    settings = dict(PROFILES[profile])
    for key, value in [('paragraph_gap', paragraph_gap), ('indent', indent)]:
        if value is not None:
            if not math.isfinite(value) or not 0 <= value <= 3:
                raise ValueError(f'{key} must be finite and between 0 and 3 em')
            settings[key] = value
    return ('body { }\np { margin: 0 0 %.3fem 0; text-indent: %.3fem; }\n'
            'h1 { break-before: page; margin: 1em 0; }\n'
            'img { max-width: 100%%; height: auto; }\n'
            'figure { margin: 1em 0; text-align: center; }\n'
            'blockquote { margin: 1em 2em; }\n'
            '.separator { text-align: center; text-indent: 0; }\n'
            'nav ol { list-style-type: none; padding-left: 0; }\n' %
            (settings['paragraph_gap'], settings['indent'])).encode(), settings

def xhtml(title, lang, body):
    return ('<?xml version="1.0" encoding="utf-8"?>\n<!DOCTYPE html>\n'
            f'<html xmlns="{XHTML}" xmlns:epub="{EPUB}" xml:lang="{escape(lang, quote=True)}" lang="{escape(lang, quote=True)}">'
            f'<head><title>{escape(title)}</title><link rel="stylesheet" type="text/css" href="style.css"/></head>'
            f'<body>{body}</body></html>').encode()

def chapters(model):
    result = []
    for block in model['blocks']:
        back_start = block.get('content_role')=='backmatter' and result and result[-1]['blocks'][-1].get('content_role')!='backmatter'
        if not result or back_start or (block['kind'] == 'heading' and block.get('level',1) == 1):
            label = block['text'] if block['kind']=='heading' else model['metadata']['title']
            if block.get('content_role')=='frontmatter':
                label = 'Material pré-textual' if model['metadata']['language'].lower().startswith('pt') else 'Front matter'
            if block.get('content_role')=='backmatter':
                label = 'Créditos e informações editoriais' if model['metadata']['language'].lower().startswith('pt') else 'Publishing information'
            result.append({'name': f'chapter-{len(result)+1:04}.xhtml', 'label': label, 'blocks': []})
        result[-1]['blocks'].append(block)
    return result

def navigation_entries(model):
    entries=[]
    for chapter in chapters(model):
        for index,b in enumerate(chapter['blocks']):
            if index==0 or b['kind']=='heading':
                entries.append(dict(id=b['id'],href=chapter['name']+'#'+b['id'],
                                    label=b['text'] if b['kind']=='heading' else chapter['label'],
                                    level=b.get('level',1) if b['kind']=='heading' else 1))
    return entries


def navigation(model, labels=None):
    entries=navigation_entries(model)
    labels=labels or {}
    if set(labels)-{e['id'] for e in entries} or any(not isinstance(v,str) or not v.strip() for v in labels.values()):
        raise ValueError('Navigation labels must map existing navigation block IDs to nonempty strings')
    # Only two heading levels are currently inferred; nested entries attach to the preceding parent.
    roots=[]
    for entry in entries:
        if entry['level']>1 and roots:
            roots[-1][1].append(entry)
        else:
            roots.append((entry,[]))
    def link(e):
        return f'<a href="{e["href"]}">{escape(labels.get(e["id"],e["label"]))}</a>'
    body=''.join('<li>'+link(e)+('<ol>'+''.join('<li>'+link(child)+'</li>' for child in children)+'</ol>' if children else '')+'</li>' for e,children in roots)
    title='Sumário' if model['metadata']['language'].lower().startswith('pt') else 'Contents'
    return xhtml(title,model['metadata']['language'],f'<nav epub:type="toc" id="toc"><h1>{title}</h1><ol>{body}</ol></nav>')


def inline(block):
    if 'spans' not in block:
        return escape(block['text'])
    result=''
    for s in block['spans']:
        text=escape(s['text'])
        if s.get('italic'): text='<em>'+text+'</em>'
        if s.get('bold'): text='<strong>'+text+'</strong>'
        result+=text
    return result


def render_block(b):
    if b['kind']=='image':
        cls=' class="cover"' if b.get('cover') else ''
        return f'<figure id="{b["id"]}"{cls}><img src="images/{b["asset"]}.png" alt="" style="width: {b['display_width_percent']:.3f}%;"/></figure>'
    tag='h'+str(b.get('level',1)) if b['kind']=='heading' else 'blockquote' if b['kind']=='quote' else 'p'
    cls=' class="separator"' if b['kind']=='separator' else ''
    return f'<{tag} id="{b["id"]}"{cls}>{inline(b)}</{tag}>'


def build(model, profile, paragraph_gap=None, indent=None, labels=None):
    metadata = model['metadata']
    style, settings = css(profile, paragraph_gap, indent)
    cs = chapters(model)
    members = {
        'mimetype': b'application/epub+zip',
        'META-INF/container.xml': b'<?xml version="1.0"?><container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="EPUB/package.opf" media-type="application/oebps-package+xml"/></rootfiles></container>',
        'EPUB/style.css': style,
        'EPUB/nav.xhtml': navigation(model, labels),
    }
    manifest = '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/><item id="style" href="style.css" media-type="text/css"/>'
    spine = ''
    for i, chapter in enumerate(cs):
        body = ''.join(render_block(b) for b in chapter['blocks'])
        members['EPUB/' + chapter['name']] = xhtml(chapter['label'], metadata['language'], body)
        manifest += f'<item id="c{i}" href="{chapter["name"]}" media-type="application/xhtml+xml"/>'
        spine += f'<itemref idref="c{i}"/>'
    for a in model.get('assets',[]):
        members[f'EPUB/images/{a["id"]}.png']=base64.b64decode(a['data_base64'],validate=True)
        cover=' properties="cover-image"' if a.get('cover') else ''
        manifest+=f'<item id="{a["id"]}" href="images/{a["id"]}.png" media-type="image/png"{cover}/>'
    creator = f'<dc:creator>{escape(metadata["author"])}</dc:creator>' if metadata.get('author') else ''
    uid = digest(serialized({'source': model['source_sha256'], 'metadata': metadata}))
    members['EPUB/package.opf'] = (f'<?xml version="1.0" encoding="utf-8"?><package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="uid">'
        f'<metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:identifier id="uid">urn:sha256:{uid}</dc:identifier>'
        f'<dc:title>{escape(metadata["title"])}</dc:title><dc:language>{escape(metadata["language"])}</dc:language>{creator}'
        '<meta property="dcterms:modified">2000-01-01T00:00:00Z</meta></metadata>'
        f'<manifest>{manifest}</manifest><spine>{spine}</spine></package>').encode()
    return members, settings

def write_epub(path, members):
    with zipfile.ZipFile(path, 'w') as archive:
        for name in ['mimetype'] + sorted(set(members) - {'mimetype'}):
            if PurePosixPath(name).is_absolute() or '..' in PurePosixPath(name).parts:
                raise ValueError('Unsafe archive member')
            info = zipfile.ZipInfo(name, (2000, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_STORED if name == 'mimetype' else zipfile.ZIP_DEFLATED
            info.external_attr = 0o600 << 16
            archive.writestr(info, members[name])
