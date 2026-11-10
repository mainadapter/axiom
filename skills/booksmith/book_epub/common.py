import hashlib
import json
import re

VERSION = '0.2.0'

def digest(data):
    return hashlib.sha256(data).hexdigest()

def serialized(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()

def compact(text):
    # Whitespace and typographic ligatures only: never strip punctuation or case.
    for a, b in {'ﬁ': 'fi', 'ﬂ': 'fl', 'ﬀ': 'ff', 'ﬃ': 'ffi', 'ﬄ': 'ffl'}.items():
        text = text.replace(a, b)
    return re.sub(r'\s+', '', text)

def finding(code, status, impact, detail, **evidence):
    return dict(code=code, status=status, impact=impact, detail=detail, evidence=evidence)

def classify(findings):
    if any(f['impact'] == 'blocking' and f['status'] != 'pass' for f in findings):
        return 'Intervenção necessária'
    if any(f['impact'] == 'review' and f['status'] != 'pass' for f in findings):
        return 'Revisão recomendada'
    return 'Aprovado'
