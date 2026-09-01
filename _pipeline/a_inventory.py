# -*- coding: utf-8 -*-
"""2022~2026 외과 실습족보 소스 인벤토리 확정.
중복 사본(Conflict/(1)/하위폴더 사본)과 답제거본, docx가 있는 pdf 쌍을 제외한다."""
import os, json, unicodedata, glob

DRIVE = os.path.expanduser(
    "~/Library/CloudStorage/SynologyDrive-의학과3학년/외과학/4-1. 실습족보")
OUT = os.path.join(os.path.dirname(__file__), "a0_files.json")

# 제외 규칙: 동일 내용의 사본/열화본
EXCLUDE_SUBSTR = [
    "_Conflict",              # Synology 충돌 사본
    "복원 (1)",               # 4AB 사본 3개
    "(답제거)",               # 정답이 지워진 열화본
    "1) 3AB/", "2) 3CD/",     # 2022 하위폴더 사본 (루트에 동일 파일 존재)
    "2024년 통합턴 외과 턴말 복원.docx",  # v2가 있음
]
# docx/pdf 쌍이 있으면 docx 우선 (2025년 전 파일)
PREFER_DOCX_PAIRS = True

COMBINED = {   # 합본 = 여러 연도·턴을 담은 파일
    "[GS] 외과 실습족보_2016이전-2022 1CD.docx": ("~2016", "2022-1CD"),
    "[GS] 턴말 정리 19-22 4AB_고두혜, 박가을, 우한결, 윤한나.docx": ("2019", "2022-4AB"),
    "2022년 4CD~2AB 외과 턴말 합본.pdf": ("2022-4CD", "2023-2AB"),
    "2022 4CD~2023 2AB 외과 턴말 합본.pdf": ("2022-4CD", "2023-2AB"),
    "2023년 3AB~2AB 외과 턴말 합본.pdf": ("2023-3AB", "2024-2AB"),
    "2024~2022년 턴말 통합본.pdf": ("2022", "2024"),
}

def nfc(s): return unicodedata.normalize("NFC", s)

def main():
    files = []
    for path in glob.glob(DRIVE + "/**/*", recursive=True):
        if os.path.isdir(path): continue
        rel = nfc(os.path.relpath(path, DRIVE))
        ext = os.path.splitext(rel)[1].lower()
        if ext not in (".docx", ".pdf"): continue
        year = rel.split("/")[0]
        if not year.isdigit() or not (2022 <= int(year) <= 2026): continue
        if any(x in rel for x in EXCLUDE_SUBSTR): continue
        files.append({"rel": rel, "year": int(year), "ext": ext,
                      "base": nfc(os.path.basename(rel)),
                      "size_mb": round(os.path.getsize(path) / 1048576, 1)})

    if PREFER_DOCX_PAIRS:
        stems = {os.path.splitext(f["rel"])[0] for f in files if f["ext"] == ".docx"}
        files = [f for f in files
                 if not (f["ext"] == ".pdf" and os.path.splitext(f["rel"])[0] in stems)]

    for f in files:
        f["combined"] = f["base"] in COMBINED
        if f["combined"]:
            f["covers"] = COMBINED[f["base"]]

    files.sort(key=lambda f: (f["year"], f["rel"]))
    json.dump({"drive": DRIVE, "files": files}, open(OUT, "w"),
              ensure_ascii=False, indent=1)
    print(f"{len(files)} files -> {OUT}")
    for f in files:
        tag = "합본" if f["combined"] else "  "
        print(f"  {f['year']} {tag} {f['size_mb']:>5}MB  {f['rel']}")

if __name__ == "__main__":
    main()
