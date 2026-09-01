# -*- coding: utf-8 -*-
"""중복 후보 탐지. 병합은 하지 않는다 — 후보쌍만 산출해 에이전트가 1쌍씩 판정한다."""
import os, re, json, collections, itertools, difflib

P = os.path.dirname(os.path.abspath(__file__))

def norm(s):
    s = re.sub(r'\([^)]*\)', ' ', s or '')
    s = re.sub(r'[^0-9A-Za-z가-힣]+', '', s)
    return s.lower()

def opt_sig(q):
    o = sorted(norm(x)[:10] for x in q['options'] if norm(x))
    return '|'.join(o) if len(o) >= 3 else None

def grams(s, n=4):
    return {s[i:i+n] for i in range(max(0, len(s) - n + 1))}

def main():
    pool = json.load(open(os.path.join(P, 'c_pool.json')))
    for i, q in enumerate(pool): q['qid'] = i

    # 1단계: 선지 집합이 동일 → 확실한 중복 후보
    by_opt = collections.defaultdict(list)
    for q in pool:
        s = opt_sig(q)
        if s: by_opt[s].append(q['qid'])
    exact = [v for v in by_opt.values() if len(v) > 1]

    # 2단계: 선지가 다르거나 없는 것 → 발문 n-gram 자카드로 후보 추출
    grouped = {i for g in exact for i in g}
    rest = [q for q in pool if q['qid'] not in grouped and len(norm(q['stem'])) >= 25]
    buckets = collections.defaultdict(list)
    for q in rest:
        st = norm(q['stem'])
        q['_g'] = grams(st)
        for tok in sorted(q['_g'])[:6]:      # 희소 시그니처로 블로킹
            buckets[tok].append(q)
    pairs, seen = [], set()
    for lst in buckets.values():
        if len(lst) > 120: continue
        for a, b in itertools.combinations(lst, 2):
            key = (min(a['qid'], b['qid']), max(a['qid'], b['qid']))
            if key in seen: continue
            seen.add(key)
            inter = len(a['_g'] & b['_g'])
            if not inter: continue
            j = inter / len(a['_g'] | b['_g'])
            if j >= 0.45:
                pairs.append({'a': key[0], 'b': key[1], 'jaccard': round(j, 3)})
    for q in rest: q.pop('_g', None)

    out = {'exact_groups': exact, 'fuzzy_pairs': sorted(
        pairs, key=lambda p: -p['jaccard'])}
    json.dump(out, open(os.path.join(P, 'd_dupcand.json'), 'w'), ensure_ascii=False)
    json.dump(pool, open(os.path.join(P, 'c_pool.json'), 'w'), ensure_ascii=False)

    print(f"총 {len(pool)}문항")
    print(f"선지동일 그룹 {len(exact)}개 (문항 {sum(len(g) for g in exact)}개 관여)")
    print(f"발문유사 후보쌍 {len(pairs)}개")
    sizes = collections.Counter(len(g) for g in exact)
    print("그룹 크기 분포:", dict(sorted(sizes.items())))
    uniq_est = len(pool) - sum(len(g) - 1 for g in exact)
    print(f"선지동일만 병합해도 → 약 {uniq_est}문항")

if __name__ == '__main__':
    main()
