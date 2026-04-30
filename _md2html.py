"""
Convert Marp markdown lecture files to standalone HTML pages
matching the lab-homepage style (KaTeX + standard nav).
"""
import os
import re
from pathlib import Path

SRC_DIR = Path('../선형대수학').resolve() if False else Path(r'g:\\내 드라이브\\sail_homepage_claude\\선형대수학')
OUT_DIR = Path(r'g:\\내 드라이브\\sail_homepage_claude\\lab-homepage\\lectures-linear-algebra')

# (md filename, output html filename, page title, lead, prev, next)
LECTURES = [
    ('02강_벡터1_화살표와연산 (작업중).md', '02-vector-arrows.html',
        'Week 2. 벡터 (1) — 화살표·연산',
        '벡터를 화살표와 숫자 묶음 두 가지 방식으로 표현하는 법, 덧셈·스칼라곱이라는 두 가지 기본 연산, 그리고 일차결합으로 평면을 채우는 직관까지.',
        ('01-intro-ot.html', 'Week 1. 강의소개 (OT)'),
        ('03-vector-dot-angle.html', 'Week 3. 벡터 (2) — 내적·길이·각도')),
    ('03강_벡터2_내적과길이각도 (작업중).md', '03-vector-dot-angle.html',
        'Week 3. 벡터 (2) — 내적·길이·각도',
        '벡터의 길이(노름), 내적의 두 가지 정의(좌표·기하), 각도와 직교 판정. 내적 한 줄로 거의 모든 도형 문제가 풀린다.',
        ('02-vector-arrows.html', 'Week 2. 벡터 (1) — 화살표·연산'),
        ('04-vector-cross-line-plane.html', 'Week 4. 벡터 (3) — 외적·직선·평면')),
    ('04강_벡터3_외적과직선평면 (작업중).md', '04-vector-cross-line-plane.html',
        'Week 4. 벡터 (3) — 외적·직선·평면',
        '3차원 전용 외적, 오른손 법칙, 평행사변형 면적, 그리고 직선·평면의 방정식. 점-평면 거리 한 줄 공식까지.',
        ('03-vector-dot-angle.html', 'Week 3. 벡터 (2) — 내적·길이·각도'),
        ('05-matrix-basics.html', 'Week 5. 행렬 (1) — 정의·연산')),
    ('05강_행렬1_정의와연산 (작업중).md', '05-matrix-basics.html',
        'Week 5. 행렬 (1) — 정의·연산',
        '여러 벡터를 한꺼번에 다루는 도구 = 행렬. 정의·특수행렬·덧셈·스칼라곱·곱셈("행 × 열")·전치까지 한 학기 행렬 계산의 토대.',
        ('04-vector-cross-line-plane.html', 'Week 4. 벡터 (3) — 외적·직선·평면'),
        ('06-gauss-elimination.html', 'Week 6. 행렬 (2) — 가우스 소거법')),
    ('06강_행렬2_가우스소거법 (작업중).md', '06-gauss-elimination.html',
        'Week 6. 행렬 (2) — 가우스 소거법',
        '연립방정식을 첨가행렬로 정리하고, 세 가지 행 연산만으로 체계적으로 풀어내는 알고리즘. 해의 종류(유일·무수히 많은·없음)까지 한 번에.',
        ('05-matrix-basics.html', 'Week 5. 행렬 (1) — 정의·연산'),
        ('07-inverse-determinant.html', 'Week 7. 행렬 (3) — 역행렬·행렬식')),
    ('07강_행렬3_역행렬과행렬식 (작업중).md', '07-inverse-determinant.html',
        'Week 7. 행렬 (3) — 역행렬·행렬식',
        '"변환 되돌리기" = 역행렬, "가역 가능 한 줄 신호" = 행렬식. 두 도구로 $A\\mathbf{x}=\\mathbf{b}$ 의 해 분석을 완성한다.',
        ('06-gauss-elimination.html', 'Week 6. 행렬 (2) — 가우스 소거법'),
        ('08-midterm-review.html', 'Week 8. 중간고사 정리')),
    ('09강_부분공간과일차독립 (작업중).md', '09-subspace-independence.html',
        'Week 9. 부분공간·일차독립',
        '"공간을 본다" 의 첫 걸음. 부분공간(원점 통과 + 닫힘), 생성(span), 일차독립/종속 판정. 행렬과 도형이 만나는 지점.',
        ('08-midterm-review.html', 'Week 8. 중간고사 정리'),
        ('10-basis-dimension.html', 'Week 10. 기저·차원')),
    ('10강_기저와차원 (작업중).md', '10-basis-dimension.html',
        'Week 10. 기저·차원',
        '부분공간을 표현하는 최소한의 화살표 = 기저. 그 개수 = 차원. 같은 공간이라도 좌표계는 여럿 — "관점의 선택" 의 시작.',
        ('09-subspace-independence.html', 'Week 9. 부분공간·일차독립'),
        ('11-linear-transform-rotation.html', 'Week 11. 선형변환 (1)')),
    ('11강_선형변환1_회전반사스케일 (작업중).md', '11-linear-transform-rotation.html',
        'Week 11. 선형변환 (1) — 회전·반사·스케일',
        '행렬을 "공간을 휘게 하는 함수" 로 보는 새 관점. 회전·반사·스케일·전단의 표현행렬과, 합성 = 곱셈이라는 핵심 사실.',
        ('10-basis-dimension.html', 'Week 10. 기저·차원'),
        ('12-kernel-range-rank.html', 'Week 12. 선형변환 (2) — 핵·치역·계수')),
    ('12강_선형변환2_핵치역계수 (작업중).md', '12-kernel-range-rank.html',
        'Week 12. 선형변환 (2) — 핵·치역·계수',
        '변환의 "도달 가능한 곳"(치역·열공간) 과 "사라지는 정보"(핵·영공간). 차원정리 한 줄로 모든 시스템의 해 구조를 정리한다.',
        ('11-linear-transform-rotation.html', 'Week 11. 선형변환 (1)'),
        ('13-eigenvalue-eigenvector.html', 'Week 13. 고윳값·고유벡터')),
    ('13강_고윳값과고유벡터 (작업중).md', '13-eigenvalue-eigenvector.html',
        'Week 13. 고윳값·고유벡터',
        '거의 모든 변환에는 "방향이 안 바뀌는 특별한 벡터" 가 있다. 그 본질적 축을 찾는 도구가 고유값·고유벡터.',
        ('12-kernel-range-rank.html', 'Week 12. 선형변환 (2)'),
        ('14-diagonalization-projection.html', 'Week 14. 대각화·정사영')),
    ('14강_대각화와정사영 (작업중).md', '14-diagonalization-projection.html',
        'Week 14. 대각화·정사영 (응용 맛보기)',
        '$A=PDP^{-1}$ 로 거듭제곱·피보나치를 한 줄에. 정사영으로 최소제곱 회귀까지. 한 학기를 정리하는 응용 두 도구.',
        ('13-eigenvalue-eigenvector.html', 'Week 13. 고윳값·고유벡터'),
        ('15-final-review.html', 'Week 15. 기말고사 / 종합 정리')),
]

NAV = '''  <nav>
    <a href="../index.html">로봇공학특론</a>
    <a href="../dl.html">딥러닝 &amp; 머신러닝</a>
    <a href="../mech.html">기전공학기초</a>
    <a href="../mechatronics.html">메카트로닉스</a>
    <a href="../control.html">자동제어</a>
    <a href="../mpc.html">MPC</a>
    <a href="../path-planning.html">경로계획 &amp; 추종</a>
    <a href="../calculus.html">미분적분학</a>
    <a href="../linear-algebra.html" class="active">선형대수학</a>
  </nav>'''


def strip_frontmatter(text):
    """Remove the leading --- ... --- block."""
    if text.startswith('---'):
        end = text.find('\n---', 3)
        if end != -1:
            return text[end + 4:].lstrip()
    return text


def convert_inline(line):
    """Convert markdown inline syntax to HTML (preserving math)."""
    # Protect math first
    placeholders = []

    def protect(m):
        placeholders.append(m.group(0))
        return f'\x00{len(placeholders)-1}\x00'

    # Display math $$...$$
    line = re.sub(r'\$\$[^$]+\$\$', protect, line)
    # Inline math $...$ (single $)
    line = re.sub(r'\$[^$\n]+?\$', protect, line)

    # Bold **x**
    line = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', line)
    # Italic *x* (avoid clashing with bold leftovers)
    line = re.sub(r'(?<!\*)\*([^*\n]+)\*(?!\*)', r'<em>\1</em>', line)
    # Inline code `x`
    line = re.sub(r'`([^`]+)`', r'<code>\1</code>', line)

    # Restore math
    def restore(m):
        return placeholders[int(m.group(1))]
    line = re.sub(r'\x00(\d+)\x00', restore, line)
    return line


def convert_body(md_text):
    """Convert the body of the markdown into HTML."""
    text = strip_frontmatter(md_text)
    lines = text.split('\n')

    out = []
    i = 0
    in_table = False
    table_rows = []
    in_html_block = 0  # depth of <div>/<svg> blocks
    skip_to_blank = False

    def flush_table():
        nonlocal table_rows
        if not table_rows:
            return
        # First row is header, second is alignment, rest is data
        if len(table_rows) >= 2:
            header = table_rows[0]
            data = table_rows[2:]
            out.append('  <table>')
            out.append('    <thead><tr>' + ''.join(f'<th>{convert_inline(c.strip())}</th>' for c in header) + '</tr></thead>')
            out.append('    <tbody>')
            for row in data:
                out.append('      <tr>' + ''.join(f'<td>{convert_inline(c.strip())}</td>' for c in row) + '</tr>')
            out.append('    </tbody>')
            out.append('  </table>')
        table_rows = []

    while i < len(lines):
        ln = lines[i]
        stripped = ln.rstrip()

        # Skip raw HTML blocks (svg, div) — pass through unchanged
        if in_html_block > 0:
            out.append(ln)
            in_html_block += stripped.count('<svg') + stripped.count('<div')
            in_html_block -= stripped.count('</svg>') + stripped.count('</div>')
            in_html_block = max(0, in_html_block)
            i += 1
            continue

        # Detect start of svg or div block
        if re.match(r'\s*<(svg|div)[\s>]', stripped):
            in_html_block = stripped.count('<svg') + stripped.count('<div')
            in_html_block -= stripped.count('</svg>') + stripped.count('</div>')
            out.append(ln)
            if in_html_block <= 0:
                in_html_block = 0
            i += 1
            continue

        # Slide separator: ignore
        if stripped == '---':
            i += 1
            continue

        # Headers
        m = re.match(r'^(#{1,6})\s+(.*)$', stripped)
        if m:
            level = len(m.group(1))
            content = convert_inline(m.group(2))
            # Strip leading emoji/icon for cleaner h2
            if level == 1:
                # Skip the very first h1 (course name) and the second h1 (title) — handled by template
                i += 1
                continue
            out.append(f'  <h{level}>{content}</h{level}>')
            i += 1
            continue

        # Tables (lines containing | and not in code block)
        if '|' in stripped and stripped.count('|') >= 2:
            # collect contiguous table rows
            cells = [c for c in stripped.strip().strip('|').split('|')]
            table_rows.append(cells)
            i += 1
            continue
        else:
            if table_rows:
                flush_table()

        # Display math block
        if stripped.startswith('$$') and stripped.endswith('$$') and len(stripped) > 4:
            out.append(f'  <p>{stripped}</p>')
            i += 1
            continue
        if stripped.startswith('$$'):
            # multi-line display math
            block = [stripped]
            i += 1
            while i < len(lines) and not lines[i].rstrip().endswith('$$'):
                block.append(lines[i])
                i += 1
            if i < len(lines):
                block.append(lines[i].rstrip())
                i += 1
            out.append('  <p>' + '\n'.join(block) + '</p>')
            continue

        # Bullet list
        if re.match(r'^\s*[-*]\s+', stripped):
            items = []
            while i < len(lines) and re.match(r'^\s*[-*]\s+', lines[i].rstrip()):
                item = re.sub(r'^\s*[-*]\s+', '', lines[i].rstrip())
                items.append(convert_inline(item))
                i += 1
            out.append('  <ul>')
            for it in items:
                out.append(f'    <li>{it}</li>')
            out.append('  </ul>')
            continue

        # Numbered list
        if re.match(r'^\s*\d+\.\s+', stripped):
            items = []
            while i < len(lines) and re.match(r'^\s*\d+\.\s+', lines[i].rstrip()):
                item = re.sub(r'^\s*\d+\.\s+', '', lines[i].rstrip())
                items.append(convert_inline(item))
                i += 1
            out.append('  <ol>')
            for it in items:
                out.append(f'    <li>{it}</li>')
            out.append('  </ol>')
            continue

        # Blank line
        if not stripped:
            out.append('')
            i += 1
            continue

        # Quote (> ...)
        if stripped.startswith('>'):
            content = convert_inline(stripped.lstrip('>').strip())
            out.append(f'  <blockquote><p>{content}</p></blockquote>')
            i += 1
            continue

        # Plain paragraph
        # Collect contiguous non-blank lines
        para = [convert_inline(stripped)]
        i += 1
        while i < len(lines):
            nxt = lines[i].rstrip()
            if not nxt or re.match(r'^(#{1,6}\s|\s*[-*]\s|\s*\d+\.\s|\$\$|>|<(svg|div))', nxt):
                break
            if '|' in nxt and nxt.count('|') >= 2:
                break
            if nxt == '---':
                break
            para.append(convert_inline(nxt))
            i += 1
        out.append('  <p>' + ' '.join(para) + '</p>')

    if table_rows:
        flush_table()

    # Replace .hl boxes (markdown-only blue highlight) with .tip (closest CSS)
    html = '\n'.join(out)
    html = html.replace('class="hl"', 'class="tip"')
    return html


HEAD_TPL = '''<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — Study Page</title>
<link rel="stylesheet" href="../assets/style.css">
<script defer src="../assets/syntax.js"></script>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"
 onload="renderMathInElement(document.body,{{delimiters:[{{left:'$$',right:'$$',display:true}},{{left:'$',right:'$',display:false}}]}})"></script>
</head>
<body>
<header class="site-header"><div class="wrap">
  <h1><a href="../index.html">Study Page</a></h1>
{nav}
</div></header>

<main class="wrap">
  <p style="color:var(--muted);font-size:13px"><a href="../linear-algebra.html">← 강의 목록</a></p>
  <h1 class="page-title">{title}</h1>
  <p class="lead">{lead}</p>

{body}

  <div class="prevnext">
    <a href="{prev_href}"><small>← 이전</small>{prev_label}</a>
    <a class="next" href="{next_href}"><small>다음 →</small>{next_label}</a>
  </div>
</main>

<footer class="site-footer"><div class="wrap"><p>© SAIL, Kongju National University</p></div></footer>
</body>
</html>
'''


def build(md_path, html_name, title, lead, prev_pair, next_pair):
    md = (SRC_DIR / md_path).read_text(encoding='utf-8')
    body = convert_body(md)
    html = HEAD_TPL.format(
        title=title,
        nav=NAV,
        lead=lead,
        body=body,
        prev_href=prev_pair[0],
        prev_label=prev_pair[1],
        next_href=next_pair[0],
        next_label=next_pair[1],
    )
    (OUT_DIR / html_name).write_text(html, encoding='utf-8')
    print(f'  wrote {html_name} ({len(html.splitlines())} lines)')


if __name__ == '__main__':
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for md, html, title, lead, prev, nxt in LECTURES:
        build(md, html, title, lead, prev, nxt)
    print('Done')
