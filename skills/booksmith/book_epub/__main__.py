import argparse
import json
from pathlib import Path

from .pipeline import convert, refine

parser = argparse.ArgumentParser(description='Offline conservative PDF to EPUB conversion and presentation refinement.')
sub = parser.add_subparsers(dest='operation', required=True)
convert_parser = sub.add_parser('convert')
convert_parser.add_argument('source')
convert_parser.add_argument('output', help='New output directory; never overwrites a revision')
convert_parser.add_argument('--title', required=True)
convert_parser.add_argument('--language', required=True)
convert_parser.add_argument('--author', default='')
convert_parser.add_argument('--profile', choices=['generic', 'kindle'], default='generic')
refine_parser = sub.add_parser('refine')
refine_parser.add_argument('previous')
refine_parser.add_argument('output', help='New output directory')
refine_parser.add_argument('--profile', choices=['generic', 'kindle'])
refine_parser.add_argument('--paragraph-gap', type=float)
refine_parser.add_argument('--indent', type=float)
refine_parser.add_argument('--labels', type=Path, help='JSON mapping chapter starting block IDs to navigation labels')
for p in (convert_parser, refine_parser):
    p.add_argument('--epubcheck-jar', type=Path, help='Trusted local EPUBCheck JAR; never downloaded automatically')
audit_parser = sub.add_parser('audit-spacing', help='Read-only re-audit of a bundle against its original PDF')
audit_parser.add_argument('source', type=Path)
audit_parser.add_argument('bundle', type=Path)
args = vars(parser.parse_args())
operation = args.pop('operation')
if operation == 'audit-spacing':
    from .pipeline import load_bundle
    from .spacing import audit_spacing
    from .common import classify
    try:
        model, _ = load_bundle(args['bundle'])
        findings = audit_spacing(model, args['source'])
    except (OSError,ValueError,KeyError) as error:
        parser.exit(2, f'{error}\n')
    state = classify(findings)
    print(json.dumps(dict(state=state, findings=findings), ensure_ascii=False, indent=2))
    raise SystemExit({'Aprovado':0,'Revisão recomendada':1,'Intervenção necessária':2}[state])
jar = args.pop('epubcheck_jar')
args['command'] = ['java', '-jar', str(jar.resolve())] if jar else None
if operation == 'refine' and args['labels']:
    args['labels'] = json.loads(args['labels'].read_text())
try:
    report = (convert if operation == 'convert' else refine)(**args)
except (OSError, ValueError, KeyError) as error:
    parser.exit(2, f'{error}\n')
print(json.dumps({'state': report['state'], 'revision': report['revision'], 'epub_sha256': report['epub_sha256']}, ensure_ascii=False))
raise SystemExit({'Aprovado': 0, 'Revisão recomendada': 1, 'Intervenção necessária': 2}[report['state']])
