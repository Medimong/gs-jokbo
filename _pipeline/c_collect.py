# -*- coding: utf-8 -*-
"""모든 소스를 파싱해 raw 문항 풀 + 이미지 라이브러리를 만든다."""
import os, sys, json, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from b_parse_docx import parse as parse_docx
from b_parse_pdf import parse as parse_pdf

P = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(P)
IMGDIR = os.path.join(ROOT, 'images')

def main():
    inv = json.load(open(os.path.join(P, 'a0_files.json')))
    os.makedirs(IMGDIR, exist_ok=True)
    pool, saved, report = [], {}, []
    for f in inv['files']:
        path = os.path.join(inv['drive'], f['rel'])
        try:
            if f['ext'] == '.docx':
                qs, blobs = parse_docx(path, f['rel'])
                blobs = {hashlib.md5(b).hexdigest()[:10]: b for b in blobs.values()}
                annots = []
            else:
                qs, blobs, annots = parse_pdf(path, f['rel'])
        except Exception as e:
            report.append((f['rel'], 'ERR', str(e)[:60])); continue

        for md5, blob in blobs.items():
            fp = os.path.join(IMGDIR, f'e{md5}')
            if md5 not in saved:
                ext = ('.png' if blob[:8] == b'\x89PNG\r\n\x1a\n' else
                       '.jpg' if blob[:2] == b'\xff\xd8' else
                       '.gif' if blob[:3] == b'GIF' else
                       '.tif' if blob[:4] in (b'MM\x00*', b'II*\x00') else
                       '.emf' if blob[:4] == b'\x01\x00\x00\x00' else '.bin')
                open(fp + ext, 'wb').write(blob)
                # TIFF와 EMF는 브라우저가 못 읽는다. 저장 즉시 PNG로 정규화한다.
                if ext in ('.tif', '.emf'):
                    png = fp + '.png'
                    if ext == '.tif':
                        os.system(f'sips -s format png "{fp+ext}" --out "{png}" >/dev/null 2>&1')
                    else:
                        so = '/Applications/LibreOffice.app/Contents/MacOS/soffice'
                        if os.path.exists(so):
                            os.system(f'"{so}" --headless --convert-to png --outdir "{IMGDIR}" '
                                      f'"{fp+ext}" >/dev/null 2>&1')
                    if os.path.exists(png) and os.path.getsize(png) > 0:
                        os.remove(fp + ext); ext = '.png'
                saved[md5] = f'e{md5}{ext}'
        for q in qs:
            q['year'] = f['year']
            q['combined'] = f.get('combined', False)
            q['images'] = [saved.get(im['md5']) for im in q['images']
                           if saved.get(im['md5'])]
        pool += qs
        full = sum(1 for q in qs if len(q['options']) >= 4 and q['answer'])
        report.append((f['rel'], len(qs), full))

    json.dump(pool, open(os.path.join(P, 'c_pool.json'), 'w'), ensure_ascii=False)
    print(f"{'file':56s} {'Q':>5} {'완전':>5}")
    for r in report:
        print(f"{r[0][:56]:56s} {str(r[1]):>5} {str(r[2]):>5}")
    print(f"\n총 {len(pool)}문항, 이미지 {len(saved)}개 저장 -> images/")
    full = sum(1 for q in pool if len(q['options']) >= 4 and q['answer'])
    print(f"선지4개이상+정답있음: {full} ({full*100//max(len(pool),1)}%)")

if __name__ == '__main__':
    main()
