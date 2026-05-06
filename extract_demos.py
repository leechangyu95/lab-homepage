"""
Extract every <div class="demo">...</div> block (and any immediately-following
<script>...</script> blocks) from each lecture HTML file under lab-homepage/
and write a standalone HTML file per demo into lab-homepage/demos/.

The output filename is derived from the source path + the demo's <h4> text:
  e.g. lectures-mech/02-basics.html  ->  mech-02-basics--ohms-law-vi-curve.html
"""
from __future__ import annotations
import os, re, html, json, sys
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
DEMOS_DIR = ROOT / "demos"

# 강의 원본은 backup-lectures/ 안에 보관되어 있다 (홈페이지 데모 위주 개편 이후).
# 폴더가 없으면 ROOT 직하를 그대로 본다 (구조 복구 시 호환).
LECTURE_BASE = ROOT / "backup-lectures" if (ROOT / "backup-lectures").is_dir() else ROOT
LECTURE_BASE_REL = "backup-lectures/" if LECTURE_BASE != ROOT else ""

# Lecture roots to scan and the friendly name used for grouping.
LECTURE_DIRS = {
    "lectures":              "로봇공학특론",
    "lectures-dl":           "딥러닝 & 머신러닝",
    "lectures-mech":         "기전공학기초",
    "lectures-dynamics":     "동역학",
    "lectures-mechatronics": "메카트로닉스",
    "lectures-control":      "자동제어",
    "lectures-mpc":          "모델예측제어",
    "lectures-path-planning":"경로계획 & 추종",
    "lectures-calculus":     "미분적분학",
    "lectures-linear-algebra":"선형대수학",
    "lectures-physics":      "기초물리학",
}

# Short prefix for filenames per source folder.
DIR_PREFIX = {
    "lectures":              "robot",
    "lectures-dl":           "dl",
    "lectures-mech":         "mech",
    "lectures-dynamics":     "dyn",
    "lectures-mechatronics": "mecha",
    "lectures-control":      "ctrl",
    "lectures-mpc":          "mpc",
    "lectures-path-planning":"path",
    "lectures-calculus":     "calc",
    "lectures-linear-algebra":"linalg",
    "lectures-physics":      "phys",
}

# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------

DIV_OPEN_RE  = re.compile(r"<div\b[^>]*>", re.IGNORECASE)
DIV_CLOSE_RE = re.compile(r"</div\s*>",    re.IGNORECASE)
DEMO_OPEN_RE = re.compile(r'<div\b[^>]*\bclass\s*=\s*"[^"]*\bdemo\b[^"]*"[^>]*>',
                          re.IGNORECASE)
SCRIPT_RE    = re.compile(r"<script\b[^>]*>.*?</script\s*>", re.IGNORECASE | re.DOTALL)
LEADING_WS_RE= re.compile(r"\s*", re.DOTALL)
H4_RE        = re.compile(r"<h4\b[^>]*>(.*?)</h4\s*>", re.IGNORECASE | re.DOTALL)
TITLE_RE     = re.compile(r"<title\b[^>]*>(.*?)</title\s*>", re.IGNORECASE | re.DOTALL)
PAGE_TITLE_RE= re.compile(r'<h1[^>]*class="[^"]*page-title[^"]*"[^>]*>(.*?)</h1\s*>',
                          re.IGNORECASE | re.DOTALL)
TAG_RE       = re.compile(r"<[^>]+>")


def strip_tags(s: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(TAG_RE.sub("", s))).strip()


def slugify(s: str) -> str:
    """Slug: keep ASCII alnum + hyphen; collapse spaces; allow Hangul."""
    s = html.unescape(s)
    s = TAG_RE.sub("", s)
    # Drop common emoji prefix and decorative leaders.
    s = re.sub(r"[\U0001F300-\U0001FAFF☀-➿]", "", s)
    # Replace any kind of separator/punctuation with hyphens.
    s = re.sub(r"[\s/_]+", "-", s.strip())
    # Keep word chars (incl. Hangul via \w + UNICODE) and hyphens.
    s = re.sub(r"[^\w\-]+", "", s, flags=re.UNICODE)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return s.lower()


def find_demo_blocks(html_text: str):
    """Yield (demo_html, end_index_after_block, title_text) tuples.

    A demo block is the <div class="demo">...</div> region (with proper div
    balancing) plus any whitespace-only-separated <script>...</script> tags
    that immediately follow.
    """
    i = 0
    while True:
        m = DEMO_OPEN_RE.search(html_text, i)
        if not m: return
        start = m.start()
        # Walk through nested divs to find the matching </div>.
        depth = 1
        pos = m.end()
        while depth > 0:
            no = DIV_OPEN_RE.search(html_text,  pos)
            nc = DIV_CLOSE_RE.search(html_text, pos)
            if not nc:  # malformed; bail
                return
            if no and no.start() < nc.start():
                depth += 1
                pos = no.end()
            else:
                depth -= 1
                pos = nc.end()
        end_div = pos
        # Eat trailing scripts (whitespace-separated, possibly several).
        cursor = end_div
        while True:
            ws = LEADING_WS_RE.match(html_text, cursor)
            test_pos = ws.end() if ws else cursor
            if html_text[test_pos:test_pos+7].lower() == "<script":
                sc = SCRIPT_RE.match(html_text, test_pos)
                if not sc: break
                cursor = sc.end()
            else:
                break
        block = html_text[start:cursor]
        # Title from first <h4>; fallback to first non-empty <p>.
        h4 = H4_RE.search(block)
        title = strip_tags(h4.group(1)) if h4 else ""
        yield block, cursor, title
        i = cursor


# ----------------------------------------------------------------------------
# HTML template for a standalone demo
# ----------------------------------------------------------------------------

def page_html(*, demo_title, lecture_title, lecture_subject,
              source_href, demo_block) -> str:
    return f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(demo_title)} — Demo</title>
<link rel="stylesheet" href="../assets/style.css">
<script defer src="../assets/syntax.js"></script>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"
 onload="renderMathInElement(document.body,{{delimiters:[{{left:'$$',right:'$$',display:true}},{{left:'$',right:'$',display:false}}]}})"></script>
<style>
  body{{background:#fafbfc}}
  .demo-meta{{color:var(--muted);font-size:13px;margin:6px 0 18px}}
  .demo-meta a{{color:var(--accent-d)}}
  .back-link{{display:inline-block;margin-bottom:12px;color:var(--muted);
    text-decoration:none;font-size:13px}}
  .back-link:hover{{color:var(--accent)}}
</style>
</head>
<body>
<header class="site-header"><div class="wrap">
  <h1><a href="../index.html">🌊 Study Page</a></h1>
  <nav>
    <a href="../index.html">로봇공학특론</a>
    <a href="../dl.html">딥러닝 &amp; 머신러닝</a>
    <a href="../mech.html">기전공학기초</a>
    <a href="../dynamics.html">동역학</a>
    <a href="../mechatronics.html">메카트로닉스</a>
    <a href="../control.html">자동제어</a>
    <a href="../mpc.html">모델예측제어</a>
    <a href="../path-planning.html">경로계획 &amp; 추종</a>
    <a href="../calculus.html">미분적분학</a>
    <a href="../linear-algebra.html">선형대수학</a>
    <a href="../physics.html">기초물리학</a>
  </nav>
</div></header>

<main class="wrap">
  <a href="index.html" class="back-link">← Demos</a>
  <h1 class="page-title">{html.escape(demo_title)}</h1>
  <p class="demo-meta">
    {html.escape(lecture_subject)} · <a href="{html.escape(source_href)}">{html.escape(lecture_title)}</a>에서 추출된 인터랙티브 데모.
  </p>
  {demo_block}
</main>
</body>
</html>
"""


def index_html(records) -> str:
    # Group by subject in original ordering.
    subjects = {}
    for r in records:
        subjects.setdefault(r["subject"], []).append(r)
    sections = []
    for subject, items in subjects.items():
        cards = []
        # Sub-group within subject by source lecture file (preserve order).
        by_src = {}
        for it in items:
            by_src.setdefault(it["src_rel"], []).append(it)
        rows = []
        for src_rel, lst in by_src.items():
            lecture_title = lst[0]["lecture_title"]
            links = "\n".join(
                f'      <li><a href="{html.escape(x["filename"])}">{html.escape(x["title"])}</a></li>'
                for x in lst
            )
            rows.append(
                f'  <article class="lec-card">\n'
                f'    <h3><a href="../{html.escape(src_rel)}">{html.escape(lecture_title)}</a></h3>\n'
                f'    <ul>\n{links}\n    </ul>\n'
                f'  </article>'
            )
        sections.append(
            f'<section class="subj">\n'
            f'  <h2>{html.escape(subject)} <span class="cnt">{len(items)}</span></h2>\n'
            f'  <div class="lec-grid">\n' + "\n".join(rows) + "\n  </div>\n</section>"
        )
    body = "\n".join(sections)
    total = len(records)
    return f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>인터랙티브 데모 모음 — Study Page</title>
<link rel="stylesheet" href="../assets/style.css">
<script defer src="../assets/syntax.js"></script>
<style>
  .subj{{margin:34px 0}}
  .subj > h2 .cnt{{font-size:13px;color:var(--muted);background:var(--accent-l);
    color:var(--accent-d);padding:2px 10px;border-radius:12px;margin-left:8px;
    font-weight:500}}
  .lec-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));
    gap:16px;margin-top:14px}}
  .lec-card{{background:#fff;border:1px solid var(--border);border-radius:10px;
    padding:14px 18px;box-shadow:0 1px 4px rgba(0,0,0,.03)}}
  .lec-card h3{{font-size:14px;margin:0 0 8px;color:var(--accent-d)}}
  .lec-card h3 a{{color:inherit;text-decoration:none}}
  .lec-card h3 a:hover{{text-decoration:underline}}
  .lec-card ul{{margin:0;padding-left:18px}}
  .lec-card li{{font-size:13.5px;line-height:1.7}}
  .summary{{color:var(--muted);font-size:14px}}
</style>
</head>
<body>
<header class="site-header"><div class="wrap">
  <h1><a href="../index.html">🌊 Study Page</a></h1>
  <nav>
    <a href="../index.html">로봇공학특론</a>
    <a href="../dl.html">딥러닝 &amp; 머신러닝</a>
    <a href="../mech.html">기전공학기초</a>
    <a href="../dynamics.html">동역학</a>
    <a href="../mechatronics.html">메카트로닉스</a>
    <a href="../control.html">자동제어</a>
    <a href="../mpc.html">모델예측제어</a>
    <a href="../path-planning.html">경로계획 &amp; 추종</a>
    <a href="../calculus.html">미분적분학</a>
    <a href="../linear-algebra.html">선형대수학</a>
    <a href="../physics.html">기초물리학</a>
  </nav>
</div></header>

<main class="wrap">
  <h1 class="page-title">🎮 인터랙티브 데모 모음</h1>
  <p class="lead">전체 강의에서 추출한 데모를 한 곳에 모았습니다.</p>
  <p class="summary">총 {total}개 데모 · 강의별 분류</p>
  {body}
</main>
</body>
</html>
"""


# ----------------------------------------------------------------------------
# Main extraction
# ----------------------------------------------------------------------------

def main():
    DEMOS_DIR.mkdir(exist_ok=True)
    records = []
    used_names: dict[str,int] = {}
    for sub, subject in LECTURE_DIRS.items():
        folder = LECTURE_BASE / sub
        if not folder.is_dir(): continue
        prefix = DIR_PREFIX[sub]
        for path in sorted(folder.glob("*.html")):
            text = path.read_text(encoding="utf-8")
            tm = TITLE_RE.search(text)
            page_title = strip_tags(tm.group(1)) if tm else path.stem
            pm = PAGE_TITLE_RE.search(text)
            lecture_title = strip_tags(pm.group(1)) if pm else page_title
            stem = path.stem  # e.g. 02-basics
            for idx, (block, _end, title) in enumerate(find_demo_blocks(text), 1):
                title_clean = title or f"Demo {idx}"
                slug = slugify(title_clean)
                if not slug:
                    slug = f"demo-{idx}"
                base = f"{prefix}-{stem}--{slug}"
                # de-dup
                fname = f"{base}.html"
                if fname in used_names:
                    used_names[fname] += 1
                    fname = f"{base}-{used_names[fname]}.html"
                else:
                    used_names[fname] = 1
                src_rel = f"{LECTURE_BASE_REL}{sub}/{path.name}"
                out = page_html(
                    demo_title=title_clean,
                    lecture_title=lecture_title,
                    lecture_subject=subject,
                    source_href=f"../{src_rel}",
                    demo_block=block,
                )
                (DEMOS_DIR / fname).write_text(out, encoding="utf-8")
                records.append({
                    "filename": fname,
                    "title": title_clean,
                    "subject": subject,
                    "src_rel": src_rel,
                    "lecture_title": lecture_title,
                })
    (DEMOS_DIR / "index.html").write_text(index_html(records), encoding="utf-8")
    (DEMOS_DIR / "_manifest.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {len(records)} demos -> {DEMOS_DIR}")


if __name__ == "__main__":
    main()
