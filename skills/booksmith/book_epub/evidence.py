"""Source-only editorial facts; no block predictions or book-specific identifiers.

Facts are shared vocabulary, not a correctness oracle. Auditing compares these
facts and raw narrative continuity with the model, including legacy predictions.
"""
import re
import unicodedata
from collections import Counter, defaultdict


def key(text):
    text=unicodedata.normalize('NFKD',text.casefold())
    return ' '.join(''.join(c for c in text if not unicodedata.combining(c)).split())


WORDS = {
    'pt': ['primeiro','segundo','terceiro','quarto','quinto','sexto','setimo','oitavo','nono','decimo'],
    'en': ['first','second','third','fourth','fifth','sixth','seventh','eighth','ninth','tenth'],
    'cardinal_pt': ['um','dois','tres','quatro','cinco','seis','sete','oito','nove','dez'],
    'cardinal_en': ['one','two','three','four','five','six','seven','eight','nine','ten'],
}
NUMBERS={w:i for ws in WORDS.values() for i,w in enumerate(ws,1)}
# Feminine PT ordinal forms are explicit lexical evidence as well.
NUMBERS.update({w[:-1]+'a':i for w,i in list(NUMBERS.items()) if w.endswith('o')})
LABELS={'capitulo':'chapter','chapter':'chapter','parte':'part','part':'part',
        'secao':'section','section':'section'}
ROMAN=re.compile(r'(?=[ivxlcdm]+$)m{0,4}(cm|cd|d?c{0,3})(xc|xl|l?x{0,3})(ix|iv|v?i{0,3})$')


def explicit(text):
    """Full, short label only; narrative mentioning a chapter is not a label.

    Bounded vocabulary: arbitrary numbers use digits/Romans; written ordinals
    beyond ten and multi-line/embellished labels remain uncertain.
    """
    bits=key(text.replace('º','').replace('ª','')).split()
    if len(bits)!=2 or bits[0] not in LABELS:return None
    token=bits[1].rstrip('.:').rstrip('ºª')
    if token.isdecimal():value=int(token)
    elif token in NUMBERS:value=NUMBERS[token]
    elif ROMAN.fullmatch(token):
        values=dict(i=1,v=5,x=10,l=50,c=100,d=500,m=1000)
        value=sum(-values[c] if i+1<len(token) and values[c]<values[token[i+1]] else values[c] for i,c in enumerate(token))
    else:return None
    return (LABELS[bits[0]],value) if value>0 else None


def style(line):
    return round(line['size'],1),tuple(line['fonts'])


def isolated(lines,i):
    l=lines[i];size=l['size']
    before=i==0 or lines[i-1]['page']!=l['page'] or l['top']-lines[i-1]['bottom']>size*.65
    after=i+1==len(lines) or lines[i+1]['page']!=l['page'] or lines[i+1]['top']-l['bottom']>size*.65
    return before and after


def narrative_facts(lines):
    """Return negative evidence, never sufficient by itself to rewrite text."""
    long_pages=defaultdict(set)
    for l in lines:
        if len(l['text'])>=60 and explicit(l['text']) is None:
            long_pages[style(l)].add(l['page'])
    result={}
    for i,l in enumerate(lines):
        if explicit(l['text']) or (l['text'].isupper() and len(l['text'])<100):continue
        neighbours=[n for n in lines[max(0,i-1):i]+lines[i+1:i+2]
                    if n['page']==l['page'] and style(n)==style(l) and
                    abs(n['top']-l['top'])<l['size']*2 and len(n['text'])>=40]
        reasons=[]
        if re.match(r'^[—–](?![—–])',l['text']):reasons.append('dialogue_marker')
        if not isolated(lines,i) and neighbours:reasons.append('continuous_prose_style')
        if len(long_pages[style(l)])>=3:reasons.append('recurring_body_style')
        if reasons:result[l['id']]=reasons
    return result


def explicit_facts(lines):
    """Find isolated labels outside contents lists, plus ordered contents echoes.

    Contents detection requires a sparse earlier region AND a complete ordered
    echo. A partial/missing contents entry is recorded separately, not guessed.
    """
    parsed={l['id']:explicit(l['text']) for l in lines if explicit(l['text'])}
    by_page=defaultdict(list)
    for l in lines:by_page[l['page']].append(l)
    list_pages={p for p,ls in by_page.items() if sum(l['id'] in parsed for l in ls)>=2 and
                not any(len(l['text'])>=60 and l['id'] not in parsed for l in ls)}
    labels=[l for i,l in enumerate(lines) if l['id'] in parsed and l['page'] not in list_pages and isolated(lines,i)]
    groups=defaultdict(list)
    for l in labels:groups[parsed[l['id']][0]].append(l)
    # Only repeated families set hierarchy. Singleton labels remain local cues.
    families={f:ls for f,ls in groups.items() if len(ls)>=2}
    confirmed=[l for l in labels if parsed[l['id']][0] in families]
    front=[];toc=[];issues=[]
    if confirmed:
        first=confirmed[0];before=[l for l in lines if l['page']<first['page']]
        expected=[parsed[l['id']] for l in confirmed]
        echoes=[l for l in before if l['id'] in parsed]
        observed=[parsed[l['id']] for l in echoes]
        complete=any(observed[i:i+len(expected)]==expected for i in range(len(observed)-len(expected)+1))
        sparse=all(len(by_page[p])<=25 for p in {l['page'] for l in before})
        if complete and sparse:
            front=[l['id'] for l in before];toc=[l['id'] for l in echoes]
        # A source-labelled contents list can prove missing/extra chapters even
        # when a complete echo is unavailable. Do not infer an unseen chapter.
        for p in sorted(list_pages):
            ls=by_page[p]
            if p<first['page'] and any(key(l['text']) in ('indice','sumario','contents','table of contents') for l in ls):
                entries=[l for l in ls if l['id'] in parsed]
                if [parsed[l['id']] for l in entries]!=expected:
                    issues.append(dict(reason='contents_source_mismatch',source=[l['id'] for l in entries+confirmed]))
    order=['part','chapter','section']
    present=[f for f in order if f in families]
    levels={l['id']:min(2,1+present.index(parsed[l['id']][0])) for l in confirmed}
    if len(present)>2:
        issues.append(dict(reason='hierarchy_depth',source=[l['id'] for l in confirmed]))
    return dict(labels=[l['id'] for l in confirmed],levels=levels,frontmatter=front,toc=toc,
                issues=issues,values={l['id']:parsed[l['id']] for l in confirmed})


def typographic_facts(lines):
    """Corroborate repeated, isolated large title styles followed by body prose.

    This does not infer semantics from a lone font-size difference. Cover-only
    styles and recurring body lines cannot establish a family of titles.
    """
    weights=Counter()
    for l in lines:
        if len(l['text'])>=40:weights[round(l['size'],1)]+=len(l['text'])
    body=weights.most_common(1)[0][0] if weights else 12
    negative=narrative_facts(lines);groups=defaultdict(list)
    for i,l in enumerate(lines[:-1]):
        n=lines[i+1]
        if (l['size']>=body*1.25 and len(l['text'])<100 and isolated(lines,i) and
                l['id'] not in negative and n['page']==l['page'] and len(n['text'])>=40 and n['size']<l['size']*.85):
            groups[style(l)].append(l)
    families=[ls for ls in groups.values() if len({l['page'] for l in ls})>=2]
    largest=max((ls[0]['size'] for ls in families),default=0)
    return {l['id']:1 if l['size']>=largest*.9 else 2 for ls in families for l in ls}
