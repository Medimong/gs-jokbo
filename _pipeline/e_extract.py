# -*- coding: utf-8 -*-
"""지정 qid의 '모든 복원 버전'을 한 묶음으로 뽑는다.
에이전트는 이 묶음과 원본 파일을 직접 대조해 완전한 한 문항으로 복원한다."""
import os, sys, json, collections

P = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(P)

def load():
    pool = json.load(open(os.path.join(P, 'c_pool.json')))
    cand = json.load(open(os.path.join(P, 'd_dupcand.json')))
    inv = json.load(open(os.path.join(P, 'a0_files.json')))
    return pool, cand, inv

def group_of(qid, cand):
    for g in cand['exact_groups']:
        if qid in g: return g
    return [qid]

def build(qid, pool, cand, inv):
    byid = {q['qid']: q for q in pool}
    g = group_of(qid, cand)
    # 발문 유사 후보도 같은 묶음으로 제시(판정은 에이전트 몫)
    fuzzy = [p for p in cand['fuzzy_pairs'] if p['a'] in g or p['b'] in g]
    near = sorted({(p['a'] if p['b'] in g else p['b'], p['jaccard']) for p in fuzzy},
                  key=lambda x: -x[1])[:4]
    secs = [byid[i]['section'] for i in g if byid[i].get('section')]
    versions = []
    for i in g:
        q = byid[i]
        versions.append({
            'qid': i, 'year': q['year'], 'source': q['src'],
            'abs_path': os.path.join(inv['drive'], q['src']),
            'section': q['section'], 'topic': q['topic'], 'num': q['num'],
            'src_tags': q['src_tags'], 'stem': q['stem'], 'options': q['options'],
            'answer': q['answer'], 'answer_raw': q['answer_raw'],
            'answer_text': q.get('answer_text'),
            # 답 번호가 아니라 '어느 선지를 가리키는지'를 함께 준다.
            # 복원본마다 선지 순서가 달라 번호만 보면 복수정답처럼 보이는 일이 잦다.
            'answer_option': (q['options'][q['answer'] - 1]
                              if q['answer'] and 0 < q['answer'] <= len(q['options']) else None),
            'tables': q['tables'], 'images': q['images'],
        })
    versions.sort(key=lambda v: (-len(v['options']), v['answer'] is None, -v['year']))
    return {
        'qid': qid,
        'section_votes': dict(collections.Counter(secs)),
        'exam_count': len(g),
        'appearances': sorted({f"{v['year']}" + (f"·{os.path.basename(v['source'])[:20]}"
                                                 if False else '') for v in versions}),
        'versions': versions,
        'near_duplicates': [{'qid': i, 'jaccard': j, 'stem': byid[i]['stem'][:200],
                             'options': byid[i]['options'], 'answer': byid[i]['answer']}
                            for i, j in near],
        'images_dir': os.path.join(ROOT, 'images'),
    }

if __name__ == '__main__':
    pool, cand, inv = load()
    ids = [int(x) for x in sys.argv[1:]]
    outdir = os.path.join(P, 'extract'); os.makedirs(outdir, exist_ok=True)
    for qid in ids:
        d = build(qid, pool, cand, inv)
        fp = os.path.join(outdir, f'q{qid}.json')
        json.dump(d, open(fp, 'w'), ensure_ascii=False, indent=1)
        imgs = sorted({i for v in d['versions'] for i in v['images']})
        print(f"q{qid}: {d['exam_count']}개 버전, 이미지 {len(imgs)}, 근접후보 "
              f"{len(d['near_duplicates'])} -> {os.path.relpath(fp, ROOT)}")
