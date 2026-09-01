# -*- coding: utf-8 -*-
"""다음 배치를 준비한다. 세션이 끊긴 뒤 재개할 때 이것만 실행하면 된다.
  python3 _pipeline/next_batch.py [배치크기]
스냅샷을 남기고, 대상 목록을 갱신하고, 추출까지 한 번에 한다."""
import os, sys, json, shutil, subprocess, datetime, collections

P = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(P)
N = int(sys.argv[1]) if len(sys.argv) > 1 else 12

def sh(*cmd):
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True).stdout

# 1) 스냅샷. 배치 도중 사고가 나도 되돌릴 수 있게.
ts = datetime.datetime.now().strftime('%Y%m%d_%H%M')
snap = os.path.join(ROOT, f'_backup_{ts}')
if not os.path.exists(snap):
    os.makedirs(snap)
    for d in ('questions', 'concepts'):
        if os.path.exists(os.path.join(ROOT, d)):
            shutil.copytree(os.path.join(ROOT, d), os.path.join(snap, d))
    print(f"스냅샷 _backup_{ts}")

# 2) 대상 목록 갱신 (questions/에 있는 것은 자동으로 done 처리된다)
print(sh('python3', '_pipeline/f_targets.py').strip().split('\n상위')[0])

# 3) 다음 배치 선정
targets = json.load(open(os.path.join(P, 'f_targets.json')))
todo = [t for t in targets if not t['done']]
batch = todo[:N]
if not batch:
    print("\n남은 대상이 없다. 작업 완료.")
    sys.exit(0)

ids = [str(t['qid']) for t in batch]
print(sh('python3', '_pipeline/e_extract.py', *ids).strip())

# 4) 각 문항의 작업 지시에 필요한 특징을 뽑아준다
print("\n=== 배치 특징 (에이전트 프롬프트용) ===")
for t in batch:
    d = json.load(open(os.path.join(P, 'extract', f"q{t['qid']}.json")))
    v = d['versions'][0]
    imgs = sorted({i for x in d['versions'] for i in x['images']})
    ans = sorted({x['answer'] for x in d['versions'] if x['answer']})
    flags = []
    if not ans: flags.append('정답없음')
    if len(v['options']) < 5: flags.append(f"선지{len(v['options'])}개")
    if len(imgs) >= 5: flags.append(f"이미지{len(imgs)}장")
    if '총론' in d['section_votes'] and len(d['section_votes']) > 1: flags.append('분과의심')
    if d['section_votes'].get('총론') and len(d['section_votes']) == 1: flags.append('분과미상')
    print(f"q{t['qid']:<5} {str(t['section']):<5} {t['examCount']:>2}회 "
          f"답{ans if ans else 'X'} 이미지{len(imgs)} {' '.join(flags)}")
    print(f"      {v['stem'][:96]}")

# 5) 기존 정리 카드 목록 (에이전트가 재사용하도록)
idx = os.path.join(ROOT, 'concepts')
cards = []
if os.path.exists(idx):
    for f in sorted(os.listdir(idx)):
        if f.endswith('.json'):
            c = json.load(open(os.path.join(idx, f)))
            cards.append((c['slug'], c.get('section', ''), c.get('title', '')))
print(f"\n=== 기존 정리 카드 {len(cards)}개 (새로 만들지 말고 먼저 재사용할 것) ===")
for s, sec, t in cards: print(f"  [{sec:<5}] {s:<38} {t}")
