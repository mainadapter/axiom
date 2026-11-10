"""Preserve raster occurrences by rendering their visible PDF region, not guessing semantics."""
import base64
import io
import math

from PIL import Image
from .common import digest, finding


def capture(page, page_number, findings, transformations, page_count):
    assets = []
    boxes = []
    for index, image in enumerate(page.images, 1):
        ident = f'p{page_number}-img{index}'
        box = tuple(float(image[k]) for k in ('x0', 'top', 'x1', 'bottom'))
        original_box=box
        if not all(math.isfinite(v) for v in box):
            findings.append(finding('image_capture','fail','blocking','Geometria de imagem inválida.',source=ident,page=page_number))
            continue
        # PDF objects can extend beyond the media box; preserve the visible intersection.
        box=(max(0,box[0]),max(0,box[1]),min(page.width,box[2]),min(page.height,box[3]))
        x0, top, x1, bottom = box
        evidence = dict(source=ident, page=page_number, bbox=list(box))
        if not all(math.isfinite(v) for v in box) or not (0 <= x0 < x1 <= page.width and 0 <= top < bottom <= page.height):
            findings.append(finding('image_capture', 'fail', 'blocking', 'Imagem fora da página ou geometria inválida; preservação não demonstrada.', **evidence))
            continue
        # Separate crops of overlapping objects would duplicate their composition.
        overlap = any(min(x1,b[2]) > max(x0,b[0]) and min(bottom,b[3]) > max(top,b[1]) for b in boxes)
        text_overlap = any(c.get('text','').strip() and min(x1,c['x1']) > max(x0,c['x0']) and min(bottom,c['bottom']) > max(top,c['top']) for c in page.chars)
        if overlap or text_overlap:
            findings.append(finding('image_composition', 'fail', 'blocking', 'Imagem sobreposta a texto ou outra imagem; composição exige intervenção para evitar duplicação.', **evidence))
            continue
        boxes.append(box)
        try:
            rendered = page.to_image(resolution=144, antialias=True).original
            sx, sy = rendered.width / page.width, rendered.height / page.height
            pixels = (math.floor(x0*sx), math.floor(top*sy), math.ceil(x1*sx), math.ceil(bottom*sy))
            crop = rendered.crop(pixels).convert('RGB')
            data = io.BytesIO()
            crop.save(data, format='PNG', optimize=False)
            raw = data.getvalue()
            with Image.open(io.BytesIO(raw)) as check:
                check.verify()
            asset = dict(id=ident, page=page_number, bbox=list(box), width=crop.width, height=crop.height,
                         media_type='image/png', sha256=digest(raw), data_base64=base64.b64encode(raw).decode(),
                         source_bbox=list(original_box), source_object=dict(name=str(image.get('name','')), srcsize=list(image.get('srcsize',[])),
                                            imagemask=bool(image.get('imagemask',False))),
                         transformation=dict(kind='render_crop', dpi=144, pixel_bbox=list(pixels)),
                         cover=bool(page_number == 1 and len(page.images)==1 and not page.chars
                                    and (x1-x0)*(bottom-top) >= page.width*page.height*.6))
            # Bound the long side to one content width; this avoids portrait-reader
            # page-fit artifacts for tall covers while retaining source-relative scale.
            asset['display_width_percent']=round(min(80 if asset['cover'] else 100,
                100*(x1-x0)/page.width,100*crop.width/crop.height),3)
            assets.append(asset)
            transformations.append(dict(kind='preserve_image', source=[ident], page=page_number,
                                        bbox=list(box), sha256=asset['sha256'], method='render_crop', dpi=144, display_width_percent=asset['display_width_percent']))
            findings.append(finding('image_capture','pass','blocking','Ocorrência preservada em PNG com origem, recorte e hash.', **evidence))
            if not page.chars and not asset['cover'] and (x1-x0)*(bottom-top) > page.width*page.height*.6:
                findings.append(finding('possible_scan','inconclusive','blocking','Página interna dominada por imagem sem texto: não é possível distinguir ilustração de scan sem inspeção.', **evidence))
            elif page.chars:
                # Reflow has no exact PDF horizontal placement; overlap above is unsafe.
                neighbors = [c for c in page.chars if c.get('text','').strip() and c['top'] < bottom and c['bottom'] > top]
                if neighbors:
                    findings.append(finding('image_position','inconclusive','review','Imagem ao lado do texto: ordem vertical mantida, relação lateral requer revisão.', **evidence))
        except Exception as error:
            findings.append(finding('image_capture','fail','blocking','Falha ao preservar imagem.', error=type(error).__name__, **evidence))
    return assets
