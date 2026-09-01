# -*- coding: utf-8 -*-
"""산출물의 금지 문장부호를 안전한 범위에서 수리한다.
문맥 판단이 필요한 것은 고치지 않고 남은 위반으로 보고한다."""
import os, re, sys, json, glob

P = os.path.dirname(os.path.abspath(__file__))
BAN = re.compile(r'[→←⇒—–]|--|✓|❌|⭐')

def fix_optnote(note, option):
    """'0.8 — 오답. ...' 처럼 선지 본문을 되풀이한 접두어를 걷어낸다."""
    n = note.strip()
    opt = (option or '').strip()
    m = re.match(r'^(.{1,60}?)\s*[—–]\s*(.+)$', n, re.S)
    if m and (m.group(1) in opt or opt.startswith(m.group(1))):
        return m.group(2).strip()
    return n

def fix_text(s):
    s = re.sub(r"'([^']{1,30})→([^']{1,30})'", r"'\1'을 '\2'로", s)
    s = re.sub(r"'([^']{1,30})'\s*→\s*([^\s,)。]{1,30})", r"'\1'을 \2로", s)
    s = re.sub(r'\s+[—–]\s+', ', ', s)
    return s

def main(paths):
    total, left, changed = 0, [], 0
    for fp in paths:
        orig = open(fp).read()
        d = json.loads(orig)
        opts = d.get('options') or []
        on = d.get('optnotes') or {}
        for k in list(on):
            i = int(k) - 1
            on[k] = fix_optnote(on[k], opts[i] if 0 <= i < len(opts) else '')
        def walk(o):
            if isinstance(o, dict): return {k: walk(v) for k, v in o.items()}
            if isinstance(o, list): return [walk(v) for v in o]
            if isinstance(o, str): return fix_text(o)
            return o
        d = walk(d)
        new = json.dumps(d, ensure_ascii=False, indent=1)
        if new != orig:
            open(fp, 'w').write(new)
            changed += 1
        hits = [m.group(0) for m in BAN.finditer(json.dumps(d, ensure_ascii=False))]
        total += 1
        if hits: left.append((os.path.basename(fp), set(hits)))
    print(f"{total}개 검사, {changed}개 수정")
    if left:
        print("문맥 판단이 필요해 남긴 위반:")
        for f, h in left: print(f"  {f}: {' '.join(h)}")
    else:
        print("금지 부호 없음")

if __name__ == '__main__':
    main(sys.argv[1:] or sorted(glob.glob(os.path.join(P, 'out', 'q*.json'))))
