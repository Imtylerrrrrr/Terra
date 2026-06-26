"""
Bedrock Knowledge Base 지식소스 생성 — 계수 RAG용.
KEITI EPD 3,002제품 + 식품 + 디지털 + 전력 → kb_factors.jsonl (S3 업로드 → Bedrock KB 적재).

각 줄 = 검색 단위 문서: content(임베딩 대상) + metadata(정확한 계수·출처).
RAG는 messy 입력("오모리김치찌개라면")을 의미검색으로 정식 품목에 연결.
숫자는 metadata에 보존 → LLM이 지어내지 않음(환각 차단).
"""
import csv, json, re, pathlib, unicodedata

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DL = pathlib.Path.home() / "Downloads"

def _find(dirp, needle):  # macOS 한글 파일명 NFD/NFC 무관 탐색
    needle = unicodedata.normalize("NFC", needle)
    for p in dirp.iterdir():
        if needle in unicodedata.normalize("NFC", p.name):
            return p
    return None
EPD = _find(DL, "환경성적표지 유효 인증현황")

def num(s):
    s = (s or "").strip()
    if not re.match(r"^\.?\d", s):
        return None
    return float("0" + s if s.startswith(".") else s)

docs = []

# ① KEITI EPD 3,002 제품 (영수증·소비재)
if EPD.exists():
    for r in csv.DictReader(open(EPD, encoding="cp949")):
        f = num(r["탄소발자국-총량"])       # 숫자값=총량, 단위=단위텍스트
        if f is None:
            continue
        name, cat, unit = r["인증제품명"].strip(), r["제품군"].strip(), r["탄소발자국-단위"].strip()
        if cat in ("생산재", "에너지사용"):   # 산업자재(콘크리트 등) 제외 — 영수증=소비재만 (KB 노이즈↓)
            continue
        docs.append({
            "content": f"{name} ({cat}) 탄소발자국 {f} {unit}",
            "metadata": {"kind": "product", "item": name, "category": cat,
                         "factor": f, "unit": unit,
                         "source": "KEITI 환경성적표지 유효 인증현황 2025"}})

# ② 식품 계수
for r in csv.DictReader(open(DATA / "food_factors.csv", encoding="utf-8")):
    f = float(r["factor_kgco2e_per_kg"])
    docs.append({
        "content": f"{r['item_ko']} ({r['category']}) 식품 탄소발자국 {f} kgCO2e/kg",
        "metadata": {"kind": "food", "item": r["item_ko"], "factor": f,
                     "unit": "kgCO2e/kg", "source": r["source"]}})

# ③ 디지털 계수
for r in csv.DictReader(open(DATA / "digital_factors.csv", encoding="utf-8")):
    docs.append({
        "content": f"{r['activity_ko']} 디지털 탄소 {r['factor_gco2e_per_unit']} gCO2e/{r['unit']}",
        "metadata": {"kind": "digital", "item": r["activity_ko"],
                     "factor": float(r["factor_gco2e_per_unit"]), "unit": f"gCO2e/{r['unit']}",
                     "source": r["source"]}})

# ④ 전력 계수
for r in csv.DictReader(open(DATA / "energy_transport_factors.csv", encoding="utf-8")):
    docs.append({
        "content": f"{r['item_ko']} 탄소배출계수 {r['factor_kgco2e_per_unit']} kgCO2e/{r['unit']}",
        "metadata": {"kind": "energy", "item": r["item_ko"],
                     "factor": float(r["factor_kgco2e_per_unit"]), "unit": r["unit"],
                     "source": r["source"]}})

out = DATA / "kb_factors.jsonl"
with open(out, "w", encoding="utf-8") as w:
    for d in docs:
        w.write(json.dumps(d, ensure_ascii=False) + "\n")

from collections import Counter
print(f"KB 문서 {len(docs)}건 → {out.name}")
for k, v in Counter(d["metadata"]["kind"] for d in docs).most_common():
    print(f"  {k:8s} {v}")
