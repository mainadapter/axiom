import importlib.metadata
import json
import platform
import re
import zipfile
from collections import Counter
from pathlib import Path

from .common import VERSION, classify, digest, finding, serialized
from .extract import extract
from .package import build, css, navigation, write_epub
from .validate import validate


def environment():
    return {'python': platform.python_version(), 'engine': VERSION,
            'implementation_sha256': digest(b''.join(p.read_bytes() for p in sorted(Path(__file__).parent.glob('*.py')))),
            **{n: importlib.metadata.version(n) for n in ('pdfplumber', 'pypdf', 'pdfminer.six', 'Pillow', 'pypdfium2')}}

ACTIONS = {
    'image_capture':'Inspecione a imagem e seu recorte na página indicada.',
    'image_position':'Confira a relação entre a imagem e o texto na saída refluída.',
    'paragraph_boundary':'Compare os limites dos parágrafos nas amostras indicadas.',
    'paragraph_layout':'Revise limites de parágrafos nas páginas sem pistas de diagramação.',
    'page_boundary':'Confira a continuação do parágrafo na mudança de página.',
    'independent_extraction':'Compare a página original com a extração; divergência não prova perda.',
    'word_spacing':'Confira espaços entre palavras nas páginas indicadas.',
    'hyphenation':'Verifique o hífen preservado na origem.',
    'indented_run':'Confirme se o recuo representa uma citação.',
    'heading_hierarchy':'Confira a relação entre título e subtítulo.',
    'epubcheck':'Consulte as mensagens do validador antes de aprovar.',
}


def diagnostic_summary(findings, model):
    groups={}
    line_by_id={l['id']:l for l in model['lines']}
    for f in findings:
        key=(f['code'],f['status'],f['impact'],f['detail'])
        g=groups.setdefault(key,dict(code=f['code'],status=f['status'],impact=f['impact'],detail=f['detail'],
                                     count=0,examples=[],action=ACTIONS.get(f['code'],'Consulte as evidências completas para investigar este achado.')))
        g['count']+=1
        if len(g['examples'])<3 and f.get('evidence'):
            e=dict(f['evidence'])
            # External checker output remains only in the full findings ledger.
            e.pop('report',None)
            ids=e.get('source',[])
            if isinstance(ids,str): ids=[ids]
            ls=[line_by_id[i] for i in ids if i in line_by_id]
            if ls: e['pages']=sorted({l['page'] for l in ls})
            if e: g['examples'].append(e)
    return sorted(groups.values(),key=lambda g:(g['status']=='pass',{'blocking':0,'review':1,'tolerable':2}[g['impact']],g['code']))


def report_markdown(report):
    text=[f'Estado: **{report["state"]}**','',f'Versão: {report["revision"]}. Perfil: {report["profile"]}.',
          'Aprovação automatizada não garante fidelidade editorial absoluta.','']
    for status,label in [('fail','Falhas detectadas'),('inconclusive','Ambiguidades'),('unavailable','Verificações indisponíveis'),('pass','Verificações realizadas')]:
        groups=[g for g in report['summary'] if g['status']==status]
        text += [f'### {label}','']
        if not groups: text += ['Nenhuma.','']; continue
        for g in groups:
            text.append(f'- **{g["code"]}** ({g["impact"]}; {g["count"]} ocorrências): {g["detail"]}')
            if status!='pass':
                text.append('  Ação: '+g['action'])
                for e in g['examples']:
                    # Compact source/page references, without hundreds of repeated messages.
                    ref={k:v for k,v in e.items() if k in ('page','pages','source','block','bbox','reason','error')}
                    if ref: text.append('  Exemplo: '+json.dumps(ref,ensure_ascii=False))
        text += ['']
    text += ['### Transformações','']
    text += [f'- {kind}: {n}.' for kind,n in sorted(Counter(t['kind'] for t in report['transformations']).items())]
    text += ['','Registro completo de ocorrências, origem e transformações em report.json e model.json.','']
    return '\n'.join(text)


def finish(out, model, profile, settings, revision, transformations, labels, command, parent=None, extra=None):
    findings = model['findings'] + (extra or [])
    epub = out / 'book.epub'
    if epub.exists():
        findings += validate(epub, model, profile, settings, labels, command)
    else:
        findings += [finding('package_validation', 'unavailable', 'tolerable', 'Não executada: extração bloqueou a geração do EPUB.'),
                     finding('epubcheck', 'unavailable', 'tolerable', 'Não executado: nenhum EPUB foi gerado.')]
    rejected_epub_sha256=None
    if epub.exists() and classify(findings)=='Intervenção necessária':
        rejected_epub_sha256=digest(epub.read_bytes())
        epub.unlink()
    report = dict(rejected_epub_sha256=rejected_epub_sha256, schema=2, state=classify(findings), revision=revision, profile=profile,
                  settings=settings, navigation_labels=labels or {}, environment=environment(),
                  source_sha256=model['source_sha256'], findings=findings, transformations=transformations,
                  parent=parent, epub_sha256=digest(epub.read_bytes()) if epub.exists() else None)
    report['summary'] = diagnostic_summary(findings, model)
    (out / 'report.json').write_bytes(serialized(report))
    (out / 'report.md').write_text(report_markdown(report))
    (out / 'model.json').write_bytes(serialized(model))
    manifest = {p.name: digest(p.read_bytes()) for p in sorted(out.iterdir()) if p.is_file()}
    (out / 'manifest.json').write_bytes(serialized({'schema': 1, 'files': manifest}))
    return report

def convert(source, output, *, title, language, author='', profile='generic', command=None):
    if not title.strip() or not re.fullmatch(r'[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})*', language):
        raise ValueError('Provide nonempty title and a BCP-47-style language tag, e.g. pt-BR')
    source, out = Path(source), Path(output)
    raw = source.read_bytes()
    out.mkdir(parents=True, exist_ok=False)
    try:
        model = extract(source)
    except Exception as error:
        model = dict(lines=[], blocks=[], pages=[], transformations=[], findings=[finding('extraction', 'fail', 'blocking', 'Não foi possível extrair o documento.', error=type(error).__name__, message=str(error))])
    model.update(schema=2, engine=VERSION, source_sha256=digest(raw),
                 metadata=dict(title=title, language=language, author=author))
    _, settings = css(profile)
    # Blocked layouts are not published as misleading partial books.
    if model['blocks'] and classify(model['findings']) != 'Intervenção necessária':
        members, settings = build(model, profile)
        write_epub(out / 'book.epub', members)
    return finish(out, model, profile, settings, 1, model['transformations'], {}, command)

def load_bundle(previous):
    previous = Path(previous)
    manifest = json.loads((previous / 'manifest.json').read_text())
    for name, sha in manifest['files'].items():
        if Path(name).name != name or digest((previous / name).read_bytes()) != sha:
            raise ValueError(f'Previous bundle integrity failed: {name}')
    required = {'model.json', 'report.json', 'report.md', 'book.epub'}
    if not required <= set(manifest['files']):
        raise ValueError('Previous bundle lacks required files')
    model = json.loads((previous / 'model.json').read_text())
    report = json.loads((previous / 'report.json').read_text())
    if (model.get('schema'),model.get('engine')) not in ((1,'0.1.0'),(2,VERSION)):
        raise ValueError('Unsupported model version; explicit migration needed')
    return model, report

def refine(previous, output, *, profile=None, paragraph_gap=None, indent=None, labels=None, command=None):
    previous, out = Path(previous), Path(output)
    model, prior = load_bundle(previous)
    profile = profile or prior['profile']
    settings = dict(prior['settings'])
    if paragraph_gap is not None:
        settings['paragraph_gap'] = paragraph_gap
    if indent is not None:
        settings['indent'] = indent
    style, settings = css(profile, **settings)
    merged_labels = dict(prior.get('navigation_labels', {}))
    if labels is not None:
        merged_labels.update(labels)
    nav = navigation(model, merged_labels)
    with zipfile.ZipFile(previous / 'book.epub') as z:
        members = {n: z.read(n) for n in z.namelist()}
    before = dict(members)
    members['EPUB/style.css'] = style
    members['EPUB/nav.xhtml'] = nav
    unchanged = all(members[k] == v for k, v in before.items() if k not in ('EPUB/style.css', 'EPUB/nav.xhtml'))
    if not unchanged:
        raise ValueError('Unexpected content mutation')
    out.mkdir(parents=True, exist_ok=False)
    write_epub(out / 'book.epub', members)
    transformations = prior['transformations'] + [dict(kind='presentation_revision', settings=settings, navigation_labels=merged_labels)]
    checks = [finding('incremental_content', 'pass', 'blocking', 'Todos os membros, exceto CSS e sumário, permanecem idênticos byte a byte.')]
    result = finish(out, model, profile, settings, prior['revision']+1, transformations, merged_labels, command,
                    parent=digest((previous / 'manifest.json').read_bytes()), extra=checks)
    return result
