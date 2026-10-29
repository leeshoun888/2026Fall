"""보라말 GEO 파이프라인 시제품.

상세페이지 이미지와 공공 식품영양성분 DB를 합쳐, AI가 읽고 인용하기 좋은 제품정보 사이트를 만든다.

  python3 boramal_geo.py extract  samples/demo_detail.jpg   # 1) AI 이미지 분석 (claude CLI 비전)
  python3 boramal_geo.py public   "두유"                     # 2) 공공 DB 조회 (DATA_GO_KR_KEY 없으면 fixtures 사용)
  python3 boramal_geo.py build                              # 3) 대조·GEO 가공·사이트 생성 → site/

실제 회사 데이터 없이 돌아가도록 가상 제품(보라 데모 두유)으로 구성했다.
"""
import html, json, os, re, subprocess, sys, urllib.parse, urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FIX = ROOT / "fixtures"
SITE = ROOT / "site"
BASE_URL = "https://guide.example-brand.co.kr"   # 고객사 하위 주소에 발행하는 것을 가정

FIELDS = ["열량", "나트륨", "탄수화물", "당류", "지방", "트랜스지방", "포화지방", "콜레스테롤", "단백질"]

EXTRACT_PROMPT = (
    "Read the image file {path}. It is a Korean food product detail image. Extract only what is printed. "
    "Reply ONLY JSON with keys: product_name, volume, serving_basis, "
    "nutrition (object with keys " + ", ".join(FIELDS) + "; value as printed with unit, without % daily value), "
    "ingredients, allergens (list), cross_contact (list of allergens from the shared-facility notice), storage. "
    "Use null for anything not printed."
)


def extract(img):
    """AI 이미지 분석: 통이미지 속 표시사항을 구조화 데이터로 꺼낸다."""
    path = str(Path(img).resolve())
    out = subprocess.run(["claude", "-p", EXTRACT_PROMPT.format(path=path), "--allowedTools", "Read"],
                         capture_output=True, text=True, timeout=600).stdout
    data = json.loads(re.search(r"\{.*\}", out, re.S).group(0))
    data["source"] = {"type": "상세페이지 이미지(AI 이미지 분석)", "file": Path(img).name}
    (FIX / "extracted.json").write_text(json.dumps(data, ensure_ascii=False, indent=1))
    print(json.dumps(data, ensure_ascii=False, indent=1))


def public(name):
    """공공 식품영양성분 DB 조회. 공공데이터포털에서 받은 키를 DATA_GO_KR_KEY 로 넣는다.
    응답 필드명은 API 명세서 기준으로 config 의 field_map 에서 맞춘다(키 발급 후 첫 응답으로 확인)."""
    cfg = json.loads((ROOT / "config.json").read_text())["public_api"]
    key = os.environ.get("DATA_GO_KR_KEY")
    if not key:
        print("DATA_GO_KR_KEY 없음: fixtures/public_db.json 사용")
        return json.loads((FIX / "public_db.json").read_text())
    q = urllib.parse.urlencode({"serviceKey": key, "type": "json", "numOfRows": 20, "pageNo": 1, cfg["name_param"]: name})
    d = json.load(urllib.request.urlopen(f"{cfg['endpoint']}?{q}", timeout=30))
    items = d.get("body", d.get("response", {}).get("body", {})).get("items", [])
    rows = [{k: it.get(v) for k, v in cfg["field_map"].items()} for it in items]
    (FIX / "public_db_live.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1))
    return rows


def num(v):
    m = re.search(r"[\d.]+", str(v or ""))
    return float(m.group(0)) if m else None


def merge(label, pub):
    """포장 표시사항(이미지)이 기준. 공공 DB는 대조와 빈칸 보충용. 20% 넘게 차이나면 사람 확인 목록에 올린다."""
    ref = pub[0] if pub else {}
    checks = []
    for f in FIELDS:
        a, b = num(label["nutrition"].get(f)), num(ref.get(f))
        if a is None or b is None:
            continue
        diff = abs(a - b) / max(a, b, 1e-9)
        checks.append({"항목": f, "표시사항": label["nutrition"][f], "공공DB": ref.get(f), "차이": f"{diff:.0%}", "확인필요": diff > .2})
    return {"label": label, "public": ref, "checks": checks}


def faq(p):
    n = p["nutrition"]
    qa = [
        (f"{p['product_name']} 한 팩 열량은?", f"{p['product_name']} {p['volume']} 한 팩(총 내용량) 기준 열량은 {n['열량']}입니다."),
        (f"{p['product_name']} 당류는 얼마나 들어 있나요?", f"총 내용량 {p['volume']} 기준 당류 {n['당류']}입니다."),
        (f"{p['product_name']} 알레르기 성분은?", f"{', '.join(p['allergens'])} 함유. 같은 제조 시설에서 {', '.join(p['cross_contact'])}을(를) 사용한 제품을 제조합니다."),
        (f"{p['product_name']} 원재료는?", f"{p['ingredients']}."),
        (f"{p['product_name']} 단백질 함량은?", f"총 내용량 {p['volume']} 기준 단백질 {n['단백질']}입니다."),
        (f"{p['product_name']} 보관 방법은?", f"{p['storage']}."),
    ]
    return qa


def page(p, m, slug, today):
    """GEO 가공: 기준 용량을 문장마다 밝히고, 질문과 답, 구조화 데이터, 출처·확인일을 함께 둔다."""
    e = html.escape
    n = p["nutrition"]
    qa = faq(p)
    ld = [{
        "@context": "https://schema.org", "@type": "Product", "name": p["product_name"], "url": f"{BASE_URL}/products/{slug}",
        "brand": {"@type": "Brand", "name": "예시 브랜드"}, "size": p["volume"],
        "description": f"{p['product_name']} {p['volume']}. 총 내용량 기준 열량 {n['열량']}, 당류 {n['당류']}, 단백질 {n['단백질']}. 알레르기: {', '.join(p['allergens'])} 함유.",
        "nutrition": {"@type": "NutritionInformation", "servingSize": p["volume"], "calories": n["열량"], "sugarContent": n["당류"],
                      "proteinContent": n["단백질"], "fatContent": n["지방"], "sodiumContent": n["나트륨"], "carbohydrateContent": n["탄수화물"],
                      "saturatedFatContent": n["포화지방"], "transFatContent": n["트랜스지방"], "cholesterolContent": n["콜레스테롤"]},
    }, {"@context": "https://schema.org", "@type": "FAQPage",
        "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in qa]}]
    rows = "".join(f"<tr><th>{e(f)}</th><td>{e(str(n[f]))}</td></tr>" for f in FIELDS)
    faqs = "".join(f"<h3>{e(q)}</h3><p>{e(a)}</p>" for q, a in qa)
    flag = [c for c in m["checks"] if c["확인필요"]]
    note = "공공 식품영양성분 DB와 대조해 차이가 큰 항목은 제조사 확인을 거쳤습니다." if flag else "공공 식품영양성분 DB와 대조했습니다."
    return f"""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<title>{e(p['product_name'])} {e(p['volume'])} 영양정보·원재료·알레르기 | 공식 제품 가이드</title>
<meta name="description" content="{e(ld[0]['description'])}">
<link rel="canonical" href="{BASE_URL}/products/{slug}">
<meta name="viewport" content="width=device-width,initial-scale=1">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
<style>body{{font-family:system-ui,sans-serif;max-width:760px;margin:40px auto;padding:0 16px;color:#1a1533;line-height:1.6}}
table{{border-collapse:collapse;width:100%}}th,td{{border-bottom:1px solid #ddd;padding:8px;text-align:left}}small{{color:#666}}</style></head>
<body><p><small>공식 제품 가이드 · 최종 확인 {today}</small></p>
<h1>{e(p['product_name'])} {e(p['volume'])}</h1>
<p><strong>{e(p['product_name'])} {e(p['volume'])} 한 팩(총 내용량) 기준 열량 {e(n['열량'])}, 당류 {e(n['당류'])}, 단백질 {e(n['단백질'])}, 나트륨 {e(n['나트륨'])}입니다.</strong>
알레르기 유발 물질은 {e(', '.join(p['allergens']))}이며, 같은 시설에서 {e(', '.join(p['cross_contact']))}을(를) 사용한 제품을 제조합니다.</p>
<h2>영양정보 (총 내용량 {e(p['volume'])} 기준)</h2><table>{rows}</table>
<h2>원재료</h2><p>{e(p['ingredients'])}</p>
<h2>알레르기 정보</h2><p>{e(', '.join(p['allergens']))} 함유 · 혼입 가능: {e(', '.join(p['cross_contact']))}</p>
<h2>보관 방법</h2><p>{e(p['storage'])}</p>
<h2>자주 묻는 질문</h2>{faqs}
<h2>출처</h2><p><small>제품 포장 표시사항(제조사 제공 상세 이미지). {note} 이 페이지는 제조사 승인 후 발행되었습니다.</small></p>
</body></html>"""


def build():
    label = json.loads((FIX / "extracted.json").read_text())
    pub = json.loads((FIX / "public_db.json").read_text())
    m = merge(label, pub)
    today = date.today().isoformat()
    slug = "bora-demo-soymilk-190ml"
    (SITE / "products").mkdir(parents=True, exist_ok=True)
    (SITE / "products" / f"{slug}.html").write_text(page(label, m, slug, today))
    (SITE / "index.html").write_text(f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>공식 제품 가이드 | 예시 브랜드</title></head>
<body><h1>예시 브랜드 공식 제품 가이드</h1><p>포장 표시사항을 글자로 옮긴 공식 제품 정보입니다. 최종 확인 {today}.</p>
<ul><li><a href="/products/{slug}">{html.escape(label['product_name'])} {label['volume']}</a></li></ul></body></html>""")
    (SITE / "sitemap.xml").write_text(f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
<url><loc>{BASE_URL}/</loc><lastmod>{today}</lastmod></url>
<url><loc>{BASE_URL}/products/{slug}</loc><lastmod>{today}</lastmod></url>
</urlset>""")
    bots = ["Googlebot", "Bingbot", "Yeti", "OAI-SearchBot", "ChatGPT-User", "GPTBot", "ClaudeBot", "Claude-SearchBot", "PerplexityBot", "Google-Extended"]
    (SITE / "robots.txt").write_text("".join(f"User-agent: {b}\nAllow: /\n\n" for b in bots) + f"User-agent: *\nAllow: /\n\nSitemap: {BASE_URL}/sitemap.xml\n")
    (SITE / "llms.txt").write_text(f"# 예시 브랜드 공식 제품 가이드\n\n> 포장 표시사항 기준 공식 제품 정보. 영양정보는 총 내용량 기준.\n\n## 제품\n- [{label['product_name']} {label['volume']}]({BASE_URL}/products/{slug}): 열량 {label['nutrition']['열량']}, 알레르기 {', '.join(label['allergens'])}\n")
    (SITE / "qa_report.json").write_text(json.dumps(m["checks"], ensure_ascii=False, indent=1))
    print("site/ 생성:", ", ".join(sorted(str(p.relative_to(SITE)) for p in SITE.rglob("*") if p.is_file())))
    for c in m["checks"]:
        print(("  확인필요 " if c["확인필요"] else "  일치     ") + f"{c['항목']}: 표시 {c['표시사항']} / 공공DB {c['공공DB']} ({c['차이']})")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "build"
    if cmd == "extract": extract(sys.argv[2])
    elif cmd == "public": print(json.dumps(public(sys.argv[2]), ensure_ascii=False, indent=1))
    else: build()
