# -*- coding: utf-8 -*-
"""외과 족보 PDF 파서.

flatten된 필기 주석을 본문에서 분리한 뒤(폰트 크기 기준), docx와 동일한
문항 분할 로직(b_parse_docx.parse_items)에 스트림을 넘긴다.
"""
import os, re, sys, json, hashlib, unicodedata, collections
import fitz
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from b_parse_docx import parse_items, SEC_RE, norm_section

def nfc(s): return unicodedata.normalize('NFC', s or '')

MIN_W, MIN_H = 120, 90        # 이보다 작은 그림은 장식/구분자
SHARED_LIMIT = 4              # 이만큼 많은 문항에 붙는 그림은 배경 장식

def body_size(doc):
    cnt = collections.Counter()
    for page in doc:
        for b in page.get_text('dict')['blocks']:
            if b['type'] != 0: continue
            for l in b['lines']:
                for s in l['spans']:
                    if s['text'].strip():
                        cnt[round(s['size'], 1)] += len(s['text'])
    return cnt.most_common(1)[0][0] if cnt else 11.0

def page_stream(page, bsize, xrefs):
    """페이지를 y좌표 순서의 (본문줄 | 주석줄 | 이미지) 스트림으로."""
    out = []
    for b in page.get_text('dict')['blocks']:
        if b['type'] == 0:
            for l in b['lines']:
                txt = nfc(''.join(s['text'] for s in l['spans']).strip())
                if not txt: continue
                sz = round(max(s['size'] for s in l['spans']), 1)
                is_annot = abs(sz - bsize) > 0.6
                # 분과 헤딩은 본문보다 크게 조판되는 일이 많다. 주석으로 버리면 안 된다.
                if is_annot and len(txt) <= 24:
                    m = SEC_RE.match(txt)
                    if m and norm_section(m.group(1)):
                        is_annot = False
                out.append((l['bbox'][1], {'t': 'annot' if is_annot else 'p',
                                           'text': txt, 'marks': []}))
        else:
            w, h = b['bbox'][2] - b['bbox'][0], b['bbox'][3] - b['bbox'][1]
            if w < MIN_W or h < MIN_H: continue
            xref = b.get('number')
            out.append((b['bbox'][1], {'t': 'img', 'rid': None, '_bbox': b['bbox'],
                                       '_page': page.number}))
    out.sort(key=lambda x: x[0])
    return [o[1] for o in out]

def parse(path, rel):
    doc = fitz.open(path)
    bsize = body_size(doc)
    items, imgblobs = [], {}
    for page in doc:
        # 이 페이지의 이미지 xref를 bbox 순서로 매칭
        rects = []
        for info in page.get_images(full=True):
            xref = info[0]
            for r in page.get_image_rects(xref):
                rects.append((r, xref))
        for it in page_stream(page, bsize, None):
            if it['t'] == 'img':
                bb = it.pop('_bbox'); it.pop('_page', None)
                best, bestov = None, 0
                for r, xref in rects:
                    ov = max(0, min(bb[2], r.x1) - max(bb[0], r.x0)) * \
                         max(0, min(bb[3], r.y1) - max(bb[1], r.y0))
                    if ov > bestov: best, bestov = xref, ov
                if best is None: continue
                try:
                    blob = doc.extract_image(best)['image']
                except Exception:
                    continue
                md5 = hashlib.md5(blob).hexdigest()[:10]
                imgblobs[md5] = blob
                it['rid'] = md5
            items.append(it)

    # 주석은 문항 분할에서 빼고 따로 모은다
    annots = [it for it in items if it['t'] == 'annot']
    stream = [it for it in items if it['t'] != 'annot']
    qs = parse_items(stream, rel, {})

    # 여러 문항에 공유되는 그림 = 페이지 배경/장식 → 제거
    share = collections.Counter()
    for q in qs:
        for im in q['images']: share[im['md5']] += 1
    for q in qs:
        q['images'] = [im for im in q['images'] if share[im['md5']] < SHARED_LIMIT]
    return qs, imgblobs, annots

if __name__ == '__main__':
    inv = json.load(open(os.path.join(os.path.dirname(__file__), 'a0_files.json')))
    rel = sys.argv[1]
    qs, blobs, annots = parse(os.path.join(inv['drive'], rel), rel)
    print(f"{rel}: {len(qs)}문항, 이미지 {len(blobs)}, 주석줄 {len(annots)}")
    for q in qs[:int(sys.argv[2]) if len(sys.argv) > 2 else 2]:
        print(json.dumps(q, ensure_ascii=False, indent=1)[:1100])
