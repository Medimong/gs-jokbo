# -*- coding: utf-8 -*-
"""중복으로 판정된 문항의 출제 이력을 정본에 합친다.
에이전트가 `appearances_to_merge`에 적어둔 값에는 합본 파일명이 섞이므로 걸러낸다."""
import json, glob, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TURN = re.compile(r'((?:19|20)\d{2})\s*[·\-]\s*(\d[A-Da-d]{1,2})')
YEAR = re.compile(r'^((?:19|20)\d{2})(\s*이전)?$')

def clean(a):
    """'2022·4CD~2023·2AB 합본' 같은 파일명에서 실제 턴 표기만 뽑는다.
    에이전트가 배열 대신 {label, source_files, note} 객체를 넣는 일이 있어 label을 꺼낸다."""
    if isinstance(a, dict):
        a = a.get('label') or a.get('turn') or a.get('appearance') or ''
    a = str(a).strip()
    m = YEAR.match(a)
    if m: return a
    m = TURN.search(a)
    if m: return f"{m.group(1)}·{m.group(2).upper()}"
    # '2024·통합턴'처럼 회차 이름이 숫자+영문이 아닌 경우도 있다.
    # 다만 합본 파일명은 출제 이력이 아니므로 걸러낸다.
    # 합본 파일명은 출제 이력이 아니다. 다만 '복원'처럼 정당한 메모에도 쓰이는 말은
    # 그것만으로 버리지 않고, 파일명임이 분명한 신호만 본다.
    if any(b in a for b in ('합본', '통합본', '~', '.docx', '.pdf')):
        return None
    m = re.match(r'^((?:19|20)\d{2})\s*[·\-]\s*([^\s,()]+)', a)
    if m: return f"{m.group(1)}·{m.group(2)}"
    # 회차는 몰라도 연도가 확인된 경우
    m = re.match(r'^((?:19|20)\d{2})\b', a)
    return m.group(1) if m else None

def main():
    merged = 0
    for fp in glob.glob(os.path.join(ROOT, 'questions', '*', 'q*.json')):
        d = json.load(open(fp))
        if not d.get('excluded'): continue
        tgt, raw = d.get('duplicate_of'), d.get('appearances_to_merge') or []
        if not tgt: continue
        # 제외 문항이 또 다른 제외 문항을 가리키면 정본까지 따라간다.
        # (A가 B로 흡수된 뒤 B가 다시 C로 흡수되는 사슬이 실제로 생겼다)
        seen = {d.get('id')}
        while True:
            hop = glob.glob(os.path.join(ROOT, 'questions', '*', f'q{tgt}.json'))
            if not hop: break
            h = json.load(open(hop[0]))
            if not h.get('excluded') or not h.get('duplicate_of'): break
            if h['duplicate_of'] in seen: break
            seen.add(tgt); tgt = h['duplicate_of']
        add = [x for x in (clean(a) for a in raw) if x]
        hits = glob.glob(os.path.join(ROOT, 'questions', '*', f'q{tgt}.json'))
        if not hits:
            print(f"  q{d.get('id')}: 정본 q{tgt}를 못 찾음"); continue
        t = json.load(open(hits[0]))
        before = set(t.get('appearances') or [])
        ap = sorted(before | set(add))
        if ap != sorted(before):
            t['appearances'] = ap
            t['examCount'] = max(int(t.get('examCount') or 0), len(ap))
            note = f"q{d['id']}로 따로 추출된 버전이 같은 문항으로 확인되어 출제 이력을 합쳤다. "
            if note not in str(t.get('source_notes') or ''):
                t['source_notes'] = note + str(t.get('source_notes') or '')
            json.dump(t, open(hits[0], 'w'), ensure_ascii=False, indent=1)
            print(f"  q{d['id']} -> q{tgt}: {ap} (출제 {len(ap)}회)")
            merged += 1
        d['appearances_to_merge_applied'] = True
        json.dump(d, open(fp, 'w'), ensure_ascii=False, indent=1)
    print(f"병합 {merged}건")

if __name__ == '__main__':
    main()
