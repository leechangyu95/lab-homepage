# Robotics & Autonomous Driving Lab — 배경지식 홈페이지

신입생을 위한 MPC / CBF / 자율주행 배경지식 정적 사이트입니다. GitHub Pages 무료 호스팅용.

## 구조
```
index.html                    홈
background/
  control-basics.html         제어 기초 (상태공간, LQR)
  mpc.html                    모델 예측 제어
  cbf.html                    제어 장벽 함수
  autonomous-driving.html     자율주행 응용
assets/style.css              공통 스타일
```

- 수식: MathJax (CDN)
- 코드 하이라이트: Prism (CDN)
- 그림: 인라인 SVG (외부 의존성 없음)

## 로컬 미리보기
브라우저로 `index.html` 을 직접 열거나:
```bash
python -m http.server 8000
```
후 http://localhost:8000 접속.

## GitHub Pages 배포
1. GitHub에서 새 저장소 생성 (예: `lab-homepage`)
2. 이 디렉터리를 push:
   ```bash
   git init
   git add .
   git commit -m "init lab homepage"
   git branch -M main
   git remote add origin https://github.com/<USER>/<REPO>.git
   git push -u origin main
   ```
3. 저장소 **Settings → Pages** → Source: `Deploy from a branch` → Branch: `main` / `(root)` → Save
4. 1~2분 뒤 `https://<USER>.github.io/<REPO>/` 에서 접속 가능

> 사용자 사이트로 쓰려면 저장소 이름을 `<USER>.github.io` 로 만드세요.

## 콘텐츠 추가/수정
- 새 배경지식 페이지는 `background/` 에 HTML 파일 추가 후, 각 페이지 상단 `<nav>` 와 `index.html` 카드/목록에 링크 추가.
- 수식: `$...$` (인라인) / `$$...$$` (블록)
- 코드: `<pre><code class="language-python">...</code></pre>`
