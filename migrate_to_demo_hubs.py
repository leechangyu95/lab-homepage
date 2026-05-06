"""
강의 페이지를 데모 허브로 개편하는 일회성 마이그레이션 스크립트.

동작:
1. 기존 hub HTML(dl.html 등)에서 주차별 카드 정보 (Week N, 제목, 설명, 원본 lecture href) 추출
2. demos/_manifest.json 로드 → (subject, src_rel) 별로 데모 그룹핑
3. 각 과목별 새 hub HTML 생성 (메모리)
4. lectures/, lectures-* 폴더 + 기존 hub HTML들을 backup-lectures/ 로 이동
5. 새 hub HTML 파일들을 최상위에 기록
6. demos/*.html 안의 `../lectures...` 경로 → `../backup-lectures/lectures...` 로 보정
"""
from __future__ import annotations
import json, re, shutil, sys, io
from pathlib import Path

# -- utf-8 stdout
if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).parent.resolve()
DEMOS = ROOT / "demos"
BACKUP = ROOT / "backup-lectures"

# subject 키 → 새 hub HTML 파일명, nav 표기, 정렬 순서
SUBJECTS = [
    # (slug,  filename,         display,                   active_attr_slot,   subject_in_manifest)
    ("robot",   "index.html",       "로봇공학특론",            "robot",   "로봇공학특론"),
    ("dl",      "dl.html",          "딥러닝 & 머신러닝",       "dl",      "딥러닝 & 머신러닝"),
    ("mech",    "mech.html",        "기전공학기초",            "mech",    "기전공학기초"),
    ("dynamics","dynamics.html",    "동역학",                  "dynamics","동역학"),
    ("mecha",   "mechatronics.html","메카트로닉스",            "mecha",   "메카트로닉스"),
    ("control", "control.html",     "자동제어",                "control", "자동제어"),
    ("mpc",     "mpc.html",         "모델예측제어",            "mpc",     "모델예측제어"),
    ("path",    "path-planning.html","경로계획 & 추종",        "path",    "경로계획 & 추종"),
    ("calc",    "calculus.html",    "미분적분학",              "calc",    "미분적분학"),
    ("linalg",  "linear-algebra.html","선형대수학",            "linalg",  "선형대수학"),
    ("phys",    "physics.html",     "기초물리학",              "phys",    "기초물리학"),
]

# 최상위 nav 에 노출되는 슬러그 (메모리에 의하면 기초물리학은 최상위 nav 미포함)
TOP_NAV_SLUGS = ["robot","dl","mech","dynamics","mecha","control","mpc","path","calc","linalg"]

# ── 헬퍼 ────────────────────────────────────────────────────────────────────

CARD_RE = re.compile(
    r'<a class="card" href="([^"]+)">\s*'
    r'<span class="num">([^<]+)</span>\s*'
    r'<h3>(.*?)</h3>\s*'
    r'<p>(.*?)</p>\s*'
    r'</a>',
    re.DOTALL,
)

def parse_hub(file: Path):
    """기존 hub HTML 에서 카드 리스트 추출."""
    text = file.read_text(encoding="utf-8")
    cards = []
    for m in CARD_RE.finditer(text):
        href, num, title, desc = m.groups()
        cards.append({
            "href": href.strip(),
            "num": num.strip(),
            "title": re.sub(r"\s+"," ",title).strip(),
            "desc": re.sub(r"\s+"," ",desc).strip(),
        })
    return cards

def load_manifest():
    with open(DEMOS / "_manifest.json", encoding="utf-8") as f:
        return json.load(f)

# ── nav HTML 빌더 ──────────────────────────────────────────────────────────

NAV_LABELS = {
    "robot":   "로봇공학특론",
    "dl":      "딥러닝 &amp; 머신러닝",
    "mech":    "기전공학기초",
    "dynamics":"동역학",
    "mecha":   "메카트로닉스",
    "control": "자동제어",
    "mpc":     "모델예측제어",
    "path":    "경로계획 &amp; 추종",
    "calc":    "미분적분학",
    "linalg":  "선형대수학",
    "phys":    "기초물리학",
}
NAV_HREFS = {
    "robot":   "index.html",
    "dl":      "dl.html",
    "mech":    "mech.html",
    "dynamics":"dynamics.html",
    "mecha":   "mechatronics.html",
    "control": "control.html",
    "mpc":     "mpc.html",
    "path":    "path-planning.html",
    "calc":    "calculus.html",
    "linalg":  "linear-algebra.html",
    "phys":    "physics.html",
}

def build_nav(active_slug: str) -> str:
    parts = []
    for slug in TOP_NAV_SLUGS:
        cls = ' class="active"' if slug == active_slug else ""
        parts.append(f'    <a href="{NAV_HREFS[slug]}"{cls}>{NAV_LABELS[slug]}</a>')
    # 기초물리학은 최상위에는 없으나 서브페이지 활성 시 노출
    if active_slug == "phys":
        parts.append(f'    <a href="{NAV_HREFS["phys"]}" class="active">{NAV_LABELS["phys"]}</a>')
    return "\n".join(parts)

# ── 페이지 빌더 ────────────────────────────────────────────────────────────

PAGE_TPL = """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{display} — 인터랙티브 데모</title>
<link rel="stylesheet" href="assets/style.css">
<script defer src="assets/syntax.js"></script>
<style>
  .week-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));
    gap:16px;margin:24px 0}}
  .week-box{{padding:18px 20px;background:var(--card);border:1px solid var(--border);
    border-radius:12px;display:flex;flex-direction:column}}
  .week-box .num{{display:inline-block;font-size:12px;font-weight:700;color:var(--accent);
    background:var(--accent-l);padding:3px 9px;border-radius:20px;align-self:flex-start}}
  .week-box h3{{margin:10px 0 4px;color:var(--fg);font-size:16px;line-height:1.35}}
  .week-box .week-desc{{margin:0 0 10px;color:var(--muted);font-size:13px;line-height:1.5}}
  .demo-list{{list-style:none;margin:8px 0 0;padding:0}}
  .demo-list li{{margin:0}}
  .demo-list a{{display:block;padding:7px 10px;border-radius:6px;color:var(--accent-d);
    text-decoration:none;font-size:13.5px;line-height:1.45;transition:.12s}}
  .demo-list a:hover{{background:var(--accent-l)}}
  .week-box.empty{{background:#f5f5f5;border-style:dashed}}
  .week-box.empty .num{{background:#e0e0e0;color:#888}}
  .week-box.empty h3{{color:#888}}
  .week-box.empty .week-desc{{color:#aaa}}
  .week-box.empty .empty-note{{color:#999;font-style:italic;font-size:13px;margin:auto 0 0}}
  .summary{{color:var(--muted);font-size:14px;margin:6px 0 0}}
</style>
</head>
<body>
<header class="site-header"><div class="wrap">
  <h1><a href="index.html">Study Page</a></h1>
  <nav>
{nav}
  </nav>
</div></header>

<main class="wrap">
  <section class="hero">
    <h2>{display} — 인터랙티브 데모</h2>
    <p class="lead">{lead}</p>
    <p class="summary">총 <strong>{n_demos}</strong>개 데모 · {n_have}/{n_total}주차 제공 · 카드 클릭 시 데모 페이지로 이동합니다.</p>
  </section>

  <div class="week-grid">
{cards}
  </div>

  <div class="tip">💡 데모는 슬라이더·캔버스 기반의 단독 인터랙티브 페이지입니다. 직관 → 수식 순서로 익히면 이해가 쉬워요.</div>
</main>

<footer class="site-footer"><div class="wrap"><p>© SAIL, Kongju National University</p></div></footer>
</body>
</html>
"""

LEAD_BY_SLUG = {
    "robot":   "로봇공학특론 강의에서 추출된 인터랙티브 데모를 주차별로 모았습니다.",
    "dl":      "딥러닝·머신러닝 13주차 강의에서 추출된 인터랙티브 데모입니다. 슬라이더로 손실·결정경계·역전파를 손으로 만져보세요.",
    "mech":    "기전공학기초 강의의 회로·소자 인터랙티브 데모를 주차별로 모았습니다.",
    "dynamics":"동역학 강의의 입자·강체 운동 인터랙티브 데모입니다.",
    "mecha":   "메카트로닉스 강의의 센서·필터·제어 인터랙티브 데모입니다.",
    "control": "자동제어 강의의 라플라스·근궤적·Bode 인터랙티브 데모입니다.",
    "mpc":     "모델예측제어 강의의 LQR·MPC·QP 인터랙티브 데모입니다.",
    "path":    "경로계획 및 추종 강의의 RRT·A*·Pure-Pursuit·CBF 인터랙티브 데모입니다.",
    "calc":    "미분적분학 강의의 극한·미분·적분 인터랙티브 데모입니다.",
    "linalg":  "선형대수학 강의의 벡터·행렬·고유값 인터랙티브 데모입니다.",
    "phys":    "기초물리학 강의의 운동·에너지·전자기 인터랙티브 데모입니다.",
}

def render_card(week, demos):
    num = week["num"]
    title = week["title"]
    desc = week["desc"]
    if demos:
        items = "\n".join(
            f'      <li><a href="demos/{d["filename"]}">{d["title"]}</a></li>'
            for d in demos
        )
        return (
            '    <article class="week-box">\n'
            f'      <span class="num">{num}</span>\n'
            f'      <h3>{title}</h3>\n'
            f'      <p class="week-desc">{desc}</p>\n'
            '      <ul class="demo-list">\n'
            f'{items}\n'
            '      </ul>\n'
            '    </article>'
        )
    else:
        return (
            '    <article class="week-box empty">\n'
            f'      <span class="num">{num}</span>\n'
            f'      <h3>{title}</h3>\n'
            f'      <p class="week-desc">{desc}</p>\n'
            '      <p class="empty-note">데모 준비 중</p>\n'
            '    </article>'
        )

def build_page(slug, filename, display, active_slug, subject_key, weeks, demos_by_src):
    nav = build_nav(active_slug)
    cards = []
    n_demos = 0
    n_have = 0
    for w in weeks:
        ds = demos_by_src.get(w["href"], [])
        if ds:
            n_have += 1
            n_demos += len(ds)
        cards.append(render_card(w, ds))
    return PAGE_TPL.format(
        display=display,
        nav=nav,
        lead=LEAD_BY_SLUG[slug],
        n_demos=n_demos,
        n_have=n_have,
        n_total=len(weeks),
        cards="\n".join(cards),
    )

# ── 메인 ──────────────────────────────────────────────────────────────────

def main():
    manifest = load_manifest()

    # 데모를 (subject, src_rel) 로 그룹핑
    demos_by_subj_src: dict[tuple[str,str], list[dict]] = {}
    for d in manifest:
        demos_by_subj_src.setdefault((d["subject"], d["src_rel"]), []).append(d)

    # 1) 각 과목 hub 파싱
    subject_pages = {}
    for slug, filename, display, active_slug, subject_key in SUBJECTS:
        hub = ROOT / filename
        if not hub.exists():
            print(f"⚠ skip (no hub): {filename}")
            continue
        weeks = parse_hub(hub)
        if not weeks:
            print(f"⚠ no cards parsed in {filename}")
            continue

        # subject key 로 데모 dict 생성
        demos_by_src = {
            src_rel: lst for (subj, src_rel), lst in demos_by_subj_src.items()
            if subj == subject_key
        }

        # weeks 의 href 와 manifest 의 src_rel 가 동일 형식인지 확인
        # (둘 다 lab-homepage 루트 기준 상대경로)
        page = build_page(slug, filename, display, active_slug, subject_key, weeks, demos_by_src)
        subject_pages[filename] = page
        n = sum(len(v) for v in demos_by_src.values())
        print(f"  built {filename}: {len(weeks)} weeks, {n} demos")

    # 2) 백업 폴더 생성
    BACKUP.mkdir(exist_ok=True)
    print(f"\n→ backup dir: {BACKUP}")

    # 3) lectures/ 와 lectures-* 폴더 이동
    for d in sorted(ROOT.iterdir()):
        if d.is_dir() and (d.name == "lectures" or d.name.startswith("lectures-")):
            dest = BACKUP / d.name
            if dest.exists():
                print(f"  ! exists, skip move: {d.name}")
                continue
            shutil.move(str(d), str(dest))
            print(f"  moved {d.name}/ → backup-lectures/{d.name}/")

    # 4) hub HTML 파일들을 백업으로 이동
    for slug, filename, *_ in SUBJECTS:
        src = ROOT / filename
        if src.exists():
            dest = BACKUP / filename
            if dest.exists():
                print(f"  ! exists, skip move: {filename}")
                continue
            shutil.move(str(src), str(dest))
            print(f"  moved {filename} → backup-lectures/{filename}")

    # 5) 새 hub HTML 작성
    for filename, html in subject_pages.items():
        (ROOT / filename).write_text(html, encoding="utf-8")
        print(f"  wrote new {filename}")

    # 6) demos/*.html 안의 `../lectures` 경로 보정
    fixed = 0
    for f in DEMOS.glob("*.html"):
        s = f.read_text(encoding="utf-8")
        new = s.replace('href="../lectures', 'href="../backup-lectures/lectures')
        if new != s:
            f.write_text(new, encoding="utf-8")
            fixed += 1
    print(f"\n  fixed {fixed} demo files (../lectures → ../backup-lectures/lectures)")

    print("\n✓ done.")

if __name__ == "__main__":
    main()
