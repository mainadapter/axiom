"""Bounded layout evidence, separate from extraction and presentation."""
import re
from collections import Counter
import statistics

EXPLICIT = re.compile(r'^(?:cap[ií]tulo|chapter|parte|part|se[cç][aã]o|section)\s+(?:\d+|[IVXLCDM]+)\b', re.I)
ROMAN = re.compile(r'^(?=[IVXLCDM]+$)M{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$')


def font_style(font):
    return dict(bold=bool(re.search(r'bold|black|heavy|demi',font,re.I)),
                italic=bool(re.search(r'italic|oblique',font,re.I)))


def profiles(lines):
    result = {}
    overall = Counter(round(l['size'],1) for l in lines for _ in range(max(1,len(l['text'])))).most_common(1)[0][0] if lines else 12
    for page in {l['page'] for l in lines}:
        ls = [l for l in lines if l['page']==page]
        prose = [l for l in ls if len(l['text']) >= 40]
        size = Counter(round(l['size'],1) for l in prose for _ in range(len(l['text']))).most_common(1)[0][0] if prose else overall
        body = [l for l in ls if .85*size <= l['size'] <= 1.15*size and len(l['text'])>30] or ls
        left, right = min(l['x0'] for l in body), max(l['x1'] for l in body)
        normal_indents=Counter(round(a['x0']-left,1) for a,b in zip(body,body[1:]) if a['x0']>left+size*.75 and b['x0']<=left+size*.5)
        conventional=[offset for offset,count in normal_indents.items() if count>=2]
        result[page] = dict(size=size, left=left, right=right, conventional_indents=conventional)
    return result


def headings(lines, layout):
    found = {}
    sizes = []
    for i,l in enumerate(lines):
        profile=layout[l['page']]
        size=profile['size']; text=l['text']
        prev=lines[i-1] if i and lines[i-1]['page']==l['page'] else None
        nex=lines[i+1] if i+1<len(lines) and lines[i+1]['page']==l['page'] else None
        centered = abs((l['x0']+l['x1'])/2-l['width']/2) <= max(size*2,l['width']*.04)
        before = prev is None or l['top']-prev['bottom'] > size*.65
        after = nex is None or nex['top']-l['bottom'] > size*.65
        isolated = before and after
        upper = text.isupper() and len(text) > 2 and any(c.isalpha() for c in text)
        roman = bool(text and ROMAN.fullmatch(text))
        bold = any(font_style(f)['bold'] for f in l['fonts'])
        evidence = []
        if EXPLICIT.match(text) and (EXPLICIT.fullmatch(text) or (isolated and (bold or l['size']>=size*1.25))): evidence.append('explicit_label')
        if len(text)<140 and l['size']>=size*1.25: evidence.append('font_size')
        if len(text)<100 and upper and isolated and (centered or bold): evidence.append('uppercase_layout')
        if len(text)<100 and centered and isolated and bold and l['size']>size*1.05: evidence.append('centered_style')
        if roman and centered and isolated: evidence.append('roman_layout')
        if evidence:
            found[l['id']] = dict(level=2 if roman else 1, evidence=evidence)
            if not roman: sizes.append(l['size'])
    largest=max(sizes,default=12)
    for l in lines:
        h=found.get(l['id'])
        if h and not EXPLICIT.match(l['text']) and 'roman_layout' not in h['evidence']:
            if l['size'] < largest*.9 and 'font_size' in h['evidence']:
                h['level']=2
    return found


def append_spans(target, incoming):
    for span in incoming:
        s=dict(span)
        if not s['text']: continue
        if target and all(target[-1].get(k,False)==s.get(k,False) for k in ('bold','italic')):
            target[-1]['text']+=s['text']
        else:
            target.append(s)


def quote_runs(lines, layout, heading_ids):
    """Both edges inset and at least two consecutive lines; ordinary first indents do not qualify."""
    result=set(); ambiguous=set(); run=[]
    def finish():
        if len(run)>=2:
            ambiguous.update(l['id'] for l in run)
            if all(l['x1']<layout[l['page']]['right']-layout[l['page']]['size']*2 for l in run):
                result.update(l['id'] for l in run)
        run.clear()
    for l in lines:
        p=layout[l['page']]; size=p['size']
        inset=l['x0']>p['left']+size and l['id'] not in heading_ids and not re.match(r'^[—–](?![—–])',l['text']) and not any(abs(l['x0']-p['left']-v)<size*.3 for v in p['conventional_indents'])
        if not inset or (run and (run[-1]['page']!=l['page'] or l['top']-run[-1]['bottom']>size*.75)):
            finish()
        if inset: run.append(l)
    finish()
    return result, ambiguous
