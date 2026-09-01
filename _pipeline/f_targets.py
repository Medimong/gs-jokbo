# -*- coding: utf-8 -*-
"""작업 대상 확정: 출제 3회 이상 + 선지 4개 이상 복원된 고유 문항."""
import os, json, collections

P = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(P)
MIN_EXAM = 3

def main():
    pool = json.load(open(os.path.join(P, 'c_pool.json')))
    cand = json.load(open(os.path.join(P, 'd_dupcand.json')))
    byid = {q['qid']: q for q in pool}
    gof = {}
    for gi, g in enumerate(cand['exact_groups']):
        for i in g: gof[i] = gi

    # 이미 사이트에 올라간 문항
    done = set()
    qdir = os.path.join(ROOT, 'questions')
    if os.path.exists(qdir):
        for sec in os.listdir(qdir):
            d = os.path.join(qdir, sec)
            if os.path.isdir(d):
                for f in os.listdir(d):
                    if f.endswith('.json'):
                        done.add(json.load(open(os.path.join(d, f)))['id'])

    targets, seen = [], set()
    for q in pool:
        gi = gof.get(q['qid'])
        if gi is None: continue
        if gi in seen: continue
        members = [byid[i] for i in cand['exact_groups'][gi]]
        if len(members) < MIN_EXAM: continue
        seen.add(gi)
        # 그룹 안의 어떤 버전이라도 이미 사이트에 있으면 그 그룹은 끝난 것이다.
        # (대표 qid는 뽑는 방식에 따라 달라지므로 qid 하나로 판정하면 중복 작업이 생긴다)
        group_done = any(m['qid'] in done for m in members)
        # 대표는 가장 온전하게 복원된 버전
        best = max(members, key=lambda x: (len(x['options']), x['answer'] is not None, x['year']))
        if len(best['options']) < 4: continue
        # 분과는 그룹 다수결. '총론'은 신뢰도가 낮아 뒤로 민다.
        secs = [m['section'] for m in members if m.get('section')]
        pref = [s for s in secs if s != '총론'] or secs
        sec = collections.Counter(pref).most_common(1)[0][0] if pref else None
        targets.append({'qid': best['qid'], 'section': sec, 'examCount': len(members),
                        'years': sorted({m['year'] for m in members}),
                        'nopt': len(best['options']), 'hasAns': best['answer'] is not None,
                        'nimg': len(best['images']),
                        'stem': best['stem'][:70].replace('\n', ' '),
                        'done': group_done})
    targets.sort(key=lambda t: (-t['examCount'], str(t['section'])))
    json.dump(targets, open(os.path.join(P, 'f_targets.json'), 'w'), ensure_ascii=False, indent=1)

    todo = [t for t in targets if not t['done']]
    print(f"출제 {MIN_EXAM}회 이상 대상 {len(targets)}개 (완료 {len(targets)-len(todo)}, 남음 {len(todo)})")
    print("분과별:", dict(collections.Counter(str(t['section']) for t in todo).most_common()))
    print("정답 없는 문항:", sum(1 for t in todo if not t['hasAns']))
    print("선지 4개(5개 미만):", sum(1 for t in todo if t['nopt'] == 4))
    print("\n상위 12개 미리보기")
    for t in todo[:12]:
        print(f"  q{t['qid']:<5} {str(t['section']):<5} {t['examCount']:>2}회 선지{t['nopt']} "
              f"img{t['nimg']} {'답O' if t['hasAns'] else '답X'} | {t['stem'][:52]}")

if __name__ == '__main__':
    main()
