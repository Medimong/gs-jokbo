# -*- coding: utf-8 -*-
"""작업 대상 확정.
  python3 _pipeline/f_targets.py [최소출제횟수]   기본 3

출제 3회 이상은 선지 집합이 같은 exact_group으로 묶인다. 2회, 1회로 내려가면
그룹에 속하지 못한 단독 문항이 대상에 들어오는데 그중 대부분은 문항이 아니라
파싱 잔해(선지 0~3개)다. 그래서 선지 4개 이상, 발문 25자 이상만 남긴다.

단독 문항은 서로 대조할 다른 복원본이 없다. 대신 두 가지를 미리 확인해 준다.
  - 단독끼리 발문이 겹치면 한 군집으로 묶어 출제 횟수를 바로잡는다.
  - 이미 완료된 문항과 발문이 겹치면 dup_of에 그 문항을 적어 둔다.
    선지 표현만 달라 exact_group이 놓친 중복이 실제로 29건 있었다.
"""
import os, re, sys, json, collections

P = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(P)
MIN_EXAM = int(sys.argv[1]) if len(sys.argv) > 1 else 3
MIN_OPT, MIN_STEM = 4, 25
FUZZ_CLUSTER, FUZZ_DUP = 0.75, 0.60


def norm(s):
    s = re.sub(r'\([^)]*\)', ' ', s or '')
    return re.sub(r'[^0-9A-Za-z가-힣]+', '', s).lower()


def grams(s, n=4):
    return {s[i:i + n] for i in range(max(0, len(s) - n + 1))}


def done_ids():
    out = set()
    qdir = os.path.join(ROOT, 'questions')
    if not os.path.exists(qdir):
        return out
    for sec in os.listdir(qdir):
        d = os.path.join(qdir, sec)
        if not os.path.isdir(d):
            continue
        for f in os.listdir(d):
            if f.endswith('.json'):
                try:
                    j = json.load(open(os.path.join(d, f)))
                except Exception:
                    continue
                i = j.get('id') or (int(f[1:-5]) if f[1:-5].isdigit() else None)
                if i is not None:
                    out.add(i)
    return out


def pick(members):
    """가장 온전하게 복원된 버전을 대표로."""
    return max(members, key=lambda x: (len(x['options']), x['answer'] is not None, x['year']))


def section_of(members):
    secs = [m['section'] for m in members if m.get('section')]
    pref = [s for s in secs if s != '총론'] or secs
    return collections.Counter(pref).most_common(1)[0][0] if pref else None


def main():
    pool = json.load(open(os.path.join(P, 'c_pool.json')))
    cand = json.load(open(os.path.join(P, 'd_dupcand.json')))
    byid = {q['qid']: q for q in pool}
    done = done_ids()

    groups = [list(g) for g in cand['exact_groups']]
    gof = {}
    for gi, g in enumerate(groups):
        for i in g:
            gof[i] = gi

    # 완료된 그룹의 모든 멤버를 커버된 것으로 본다
    covered = set(done)
    for i in list(done):
        if i in gof:
            covered.update(groups[gof[i]])

    # 그룹 밖 단독 문항 중 문항의 꼴을 갖춘 것만
    ingroup = set(gof)
    singles = [q for q in pool if q['qid'] not in ingroup
               and len(q['options']) >= MIN_OPT
               and len(q['stem'].strip()) >= MIN_STEM]
    sids = {q['qid'] for q in singles}

    # 단독끼리 발문이 겹치면 한 군집으로 (출제 횟수를 바로잡는다)
    par = {i: i for i in sids}

    def find(x):
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x

    for p in cand['fuzzy_pairs']:
        a, b = p['a'], p['b']
        if p['jaccard'] >= FUZZ_CLUSTER and a in sids and b in sids:
            ra, rb = find(a), find(b)
            if ra != rb:
                par[ra] = rb
    clusters = collections.defaultdict(list)
    for i in sids:
        clusters[find(i)].append(i)
    for members in clusters.values():
        groups.append(members)

    # 완료 문항의 발문 지문 (중복 의심 판정용)
    covg = []
    for i in covered:
        q = byid.get(i)
        if not q:
            continue
        g = grams(norm(q['stem']))
        if len(g) >= 10:
            covg.append((i, g))

    def dup_of(stem):
        g = grams(norm(stem))
        if len(g) < 10:
            return None, 0.0
        best, bq = 0.0, None
        for qid, cg in covg:
            inter = len(g & cg)
            if inter * 2 < min(len(g), len(cg)):
                continue
            j = inter / len(g | cg)
            if j > best:
                best, bq = j, qid
        return (bq, round(best, 2)) if best >= FUZZ_DUP else (None, round(best, 2))

    targets, seen = [], set()
    for gi, g in enumerate(groups):
        key = min(g)
        if key in seen:
            continue
        seen.add(key)
        if len(g) < MIN_EXAM:
            continue
        members = [byid[i] for i in g]
        best = pick(members)
        if len(best['options']) < MIN_OPT:
            continue
        group_done = any(m['qid'] in done for m in members)
        dq, sim = (None, 0.0) if len(g) > 1 else dup_of(best['stem'])
        targets.append({
            'qid': best['qid'], 'section': section_of(members), 'examCount': len(members),
            'years': sorted({m['year'] for m in members}),
            'nopt': len(best['options']), 'hasAns': best['answer'] is not None,
            'nimg': len(best['images']),
            'stem': best['stem'][:70].replace('\n', ' '),
            'dup_of': dq, 'dup_sim': sim,
            'done': group_done,
        })

    targets.sort(key=lambda t: (-t['examCount'], str(t['section'])))
    json.dump(targets, open(os.path.join(P, 'f_targets.json'), 'w'), ensure_ascii=False, indent=1)

    todo = [t for t in targets if not t['done']]
    print(f"출제 {MIN_EXAM}회 이상 대상 {len(targets)}개 (완료 {len(targets)-len(todo)}, 남음 {len(todo)})")
    print("분과별:", dict(collections.Counter(str(t['section']) for t in todo).most_common()))
    print("정답 없는 문항:", sum(1 for t in todo if not t['hasAns']))
    print("선지 4개(5개 미만):", sum(1 for t in todo if t['nopt'] == 4))
    dups = [t for t in todo if t['dup_of']]
    if dups:
        print(f"완료 문항과 발문 유사(중복 의심): {len(dups)}개")
    print("\n상위 12개 미리보기")
    for t in todo[:12]:
        d = f" ~q{t['dup_of']}({t['dup_sim']})" if t['dup_of'] else ''
        print(f"  q{t['qid']:<5} {str(t['section']):<5} {t['examCount']:>2}회 선지{t['nopt']} "
              f"img{t['nimg']} {'답O' if t['hasAns'] else '답X'}{d} | {t['stem'][:46]}")


if __name__ == '__main__':
    main()
