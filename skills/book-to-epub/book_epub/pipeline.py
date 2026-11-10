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

def report_markdown(report):
    text = [f'Estado: **{report["state"]}**', '',
            f'Versão: {report["revision"]}. Perfil: {report["profile"]}.',
            'Aprovação automatizada não garante fidelidade editorial absoluta.', '']
    for status, label in [('fail', 'Falhas detectadas'), ('inconclusive', 'Verificações inconclusivas / ambiguidades'),
                          ('unavailable', 'Verificações indisponíveis'), ('pass', 'Verificações realizadas')]:
        items = [f for f in report['findings'] if f['status'] == status]
        text += [f'### {label}', '']
        if not items:
            text += ['Nenhuma.', '']
            continue
        groups = Counter((f['code'], f['impact'], f['detail']) for f in items)
        text += [f'- `{code}` ({impact}, {count}): {detail}' for (code, impact, detail), count in groups.items()]
        text += ['']
    text += ['### Transformações', '']
    counts = Counter(t['kind'] for t in report['transformations'])
    text += [f'- `{kind}`: {n}.' for kind, n in sorted(counts.items())] or ['Nenhuma.']
    text += ['', 'Evidências por página/bloco, hashes e detalhes completos em report.json e model.json.', '']
    return '\n'.join(text)

def finish(out, model, profile, settings, revision, transformations, labels, command, parent=None, extra=None):
    findings = model['findings'] + (extra or [])
    epub = out / 'book.epub'
    if epub.exists():
        findings += validate(epub, model, profile, settings, labels, command)
    else:
        findings += [finding('package_validation', 'unavailable', 'tolerable', 'Não executada: extração bloqueou a geração do EPUB.'),
                     finding('epubcheck', 'unavailable', 'tolerable', 'Não executado: nenhum EPUB foi gerado.')]
    report = dict(schema=1, state=classify(findings), revision=revision, profile=profile,
                  settings=settings, navigation_labels=labels or {}, environment=environment(),
                  source_sha256=model['source_sha256'], findings=findings, transformations=transformations,
                  parent=parent, epub_sha256=digest(epub.read_bytes()) if epub.exists() else None)
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
    model.update(schema=1, engine=VERSION, source_sha256=digest(raw),
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
    if model.get('schema') != 1 or model.get('engine') != VERSION:
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
