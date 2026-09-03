# -*- coding: utf-8 -*-
"""출제 이력 표기를 '2022·4CD' 꼴로 통일한다. 복원자마다 적는 방식이 달라 뒤섞여 있다."""
import json, re, glob, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 합본 파일 이름은 출제 이력이 아니다. 여러 턴을 묶어 놓은 문서일 뿐이다.
BAD = ('합본', '통합본', '정리', '복원본', '~')

def norm_one(a):
    a = str(a).strip().strip('()')
    if not a: return None
    if any(b in a for b in BAD): return None
    if '이전' in a:
        m = re.match(r'^((?:19|20)\d{2})\s*이전$', a)      # 이미 정규화된 형태
        if m: return a
        m = re.search(r'(\d{2})\s*이전', a)
        return f"20{m.group(1)} 이전" if m else "과거"
    # 22-4CD / 22-4 / 2022-4CD / 2022·4CD
    m = re.match(r'^(\d{2}|\d{4})\s*[-–·]\s*(\d[A-Da-d]{0,2})\s*$', a)
    if m:
        y = m.group(1)
        y = y if len(y) == 4 else ('20' + y)
        return f"{y}·{m.group(2).upper()}"
    m = re.match(r'^(19|20)\d{2}$', a)
    if m: return a
    m = re.match(r'^(\d{2})$', a)
    if m: return '20' + a
    # '2024·통합턴'처럼 회차 이름이 숫자+영문이 아닌 표기도 있다.
    m = re.match(r'^((?:19|20)\d{2})\s*[·\-]\s*([^\s,()]+)', a)
    if m: return f"{m.group(1)}·{m.group(2)}"
    # 연도로 시작하지 않는 표기는 회차를 특정할 수 없다는 뜻이다.
    # 에이전트가 산문 메모를 여기에 적어 넣는 일이 있어 한 칸으로 접는다.
    return '회차 미상'

def main():
    n = 0
    for fp in glob.glob(os.path.join(ROOT, 'questions', '*', 'q*.json')):
        d = json.load(open(fp))
        ap = d.get('appearances') or []
        out = []
        for a in ap:
            # "22-1AB, 2AB" 처럼 한 칸에 여러 턴이 묶인 경우를 편다
            parts = re.split(r',\s*', str(a))
            year = None
            for p in parts:
                v = norm_one(p)
                if not v: continue
                m = re.match(r'^((?:19|20)\d{2})·', v)
                if m: year = m.group(1)
                elif year and re.match(r'^\d[A-D]{1,2}$', p.strip().upper()):
                    v = f"{year}·{p.strip().upper()}"
                out.append(v)
        seen, uniq = set(), []
        for v in out:
            if v not in seen: seen.add(v); uniq.append(v)
        uniq.sort()
        if uniq != ap:
            d['appearances'] = uniq
            if uniq: d['examCount'] = len(uniq)
            json.dump(d, open(fp, 'w'), ensure_ascii=False, indent=1); n += 1
    print(f"출제 이력 표기 통일: {n}문항")

if __name__ == '__main__':
    main()
