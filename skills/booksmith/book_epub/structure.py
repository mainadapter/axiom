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


def local_headings(lines, layout):
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


def roman_value(text):
    if not text or not ROMAN.fullmatch(text):
        return None
    values = dict(I=1, V=5, X=10, L=50, C=100, D=500, M=1000)
    return sum(-values[c] if i+1<len(text) and values[c]<values[text[i+1]] else values[c]
               for i,c in enumerate(text))


def document_structure(lines, layout):
    """Corroborate local candidates using repeated title/roman cycles and source contents.

    No book-specific labels: titles must immediately precede I, share typography,
    and recur across narrative runs. Front matter needs an ordered contents echo
    on earlier sparse pages; preceding prose is never silently demoted.
    """
    hs = local_headings(lines, layout)
    romans = [i for i,l in enumerate(lines) if 'roman_layout' in hs.get(l['id'],{}).get('evidence',[])]
    starts = []
    for i in romans:
        if lines[i]['text'] != 'I' or not i:
            continue
        title = lines[i-1]
        if title['id'] in hs and roman_value(title['text']) is None and (
                title['page']==lines[i]['page'] or lines[i]['page']==title['page']+1):
            starts.append(i-1)
    groups = {}
    for i in starts:
        l = lines[i]
        groups.setdefault((round(l['size'],1), tuple(l['fonts'])), []).append(i)
    parents = max(groups.values(), key=len, default=[])
    if len(parents)<2:
        parents=[]
    # Require a second roman and real intervening narrative in at least two runs.
    corroborated = 0
    for j,i in enumerate(parents):
        end = parents[j+1] if j+1<len(parents) else len(lines)
        run = [k for k in romans if i<k<end]
        if len(run)>=2 and lines[run[1]]['text']=='II' and run[1]-run[0]>2:
            corroborated+=1
    if corroborated<2:
        parents=[]
    frontmatter=[]
    if parents:
        for i in parents:
            hs[lines[i]['id']] = dict(level=1, evidence=hs[lines[i]['id']]['evidence']+['repeated_roman_parent'])
        # Normalize only comparison keys. Text itself is never rewritten.
        keys=[re.sub(r'\s+',' ',lines[i]['text']).strip().casefold() for i in parents]
        first=parents[0]
        before=lines[:first]
        # Contents is a contiguous ordered echo. A title may also occur on the
        # cover (or as the collection name); that earlier duplicate is not a TOC entry.
        echoes=[l for l in before if l['text'].strip().casefold() in keys]
        echo_keys=[l['text'].strip().casefold() for l in echoes]
        ordered_echo=any(echo_keys[i:i+len(keys)]==keys for i in range(len(echo_keys)-len(keys)+1))
        sparse=all(sum(l['page']==p for l in before)<=25 for p in {l['page'] for l in before})
        if ordered_echo and sparse and all(l['page']<lines[first]['page'] for l in before):
            frontmatter=[l['id'] for l in before]
            for ident in frontmatter:
                hs.pop(ident,None)
    backmatter=[]
    if parents:
        # Only a terminal, uniformly smaller-font publishing section with both
        # rights and catalogue identifiers qualifies. Never split on prose alone.
        body_size=Counter(round(l['size'],1) for l in lines for _ in range(len(l['text']))).most_common(1)[0][0]
        tail=[]
        for page in sorted({l['page'] for l in lines},reverse=True):
            ls=[l for l in lines if l['page']==page]
            if page<=lines[parents[-1]]['page'] or len(ls)>35 or any(l['size']>=body_size*.85 for l in ls):
                break
            tail=ls+tail
        text=' '.join(l['text'] for l in tail).casefold()
        if re.search(r'copyright|direitos.*reservados|all rights reserved',text) and re.search(r'\bisbn\b|\bcip\b',text):
            backmatter=[l['id'] for l in tail]
            for ident in backmatter:hs.pop(ident,None)
    return hs, dict(parents=[lines[i]['id'] for i in parents],
                    romans=[lines[i]['id'] for i in romans], frontmatter=frontmatter,backmatter=backmatter)


def headings(lines, layout):
    return document_structure(lines, layout)[0]


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
