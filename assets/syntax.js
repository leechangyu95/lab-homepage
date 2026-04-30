// Lightweight Python syntax highlighter for <pre><code> blocks.
// Tokens: keywords, builtins, strings (incl. triple-quoted, f/r prefixes),
// numbers, comments, decorators, def/class names, function calls, self/cls.
(function(){
  const KW = new Set(['False','None','True','and','as','assert','async','await',
    'break','class','continue','def','del','elif','else','except','finally',
    'for','from','global','if','import','in','is','lambda','nonlocal','not',
    'or','pass','raise','return','try','while','with','yield','match','case']);
  const BUILTIN = new Set(['abs','all','any','bin','bool','bytes','callable',
    'chr','classmethod','complex','dict','dir','divmod','enumerate','eval',
    'exec','filter','float','format','frozenset','getattr','globals','hasattr',
    'hash','help','hex','id','input','int','isinstance','issubclass','iter',
    'len','list','locals','map','max','min','next','object','oct','open','ord',
    'pow','print','property','range','repr','reversed','round','set','setattr',
    'slice','sorted','staticmethod','str','sum','super','tuple','type','vars',
    'zip','__init__','__name__','__main__','__call__','__repr__','__str__']);
  const SOFT = new Set(['self','cls']);

  const esc = (s)=>s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');

  function highlight(src){
    const n = src.length;
    let i = 0, out = '';
    let prevTok = null; // last non-space identifier (to detect def/class names)
    while(i < n){
      const c = src[i];
      // Comment
      if(c === '#'){
        let j = src.indexOf('\n', i); if(j === -1) j = n;
        out += '<span class="tok-com">'+esc(src.slice(i,j))+'</span>';
        i = j; continue;
      }
      // String prefixes (r, b, f, u, rb, fr, etc.) followed by quote
      const pmatch = src.slice(i).match(/^([rRbBuUfF]{1,2})(['"])/);
      if(pmatch){
        const pref = pmatch[1];
        const q = pmatch[2];
        // triple?
        if(src[i+pref.length] === q && src[i+pref.length+1] === q && src[i+pref.length+2] === q){
          const tq = q+q+q;
          let end = src.indexOf(tq, i+pref.length+3);
          end = (end === -1) ? n : end + 3;
          out += '<span class="tok-str">'+esc(src.slice(i,end))+'</span>';
          i = end; continue;
        }
        // single-line
        let j = i+pref.length+1;
        while(j < n && src[j] !== q && src[j] !== '\n'){
          if(src[j] === '\\' && j+1 < n) j += 2; else j++;
        }
        if(j < n && src[j] === q) j++;
        out += '<span class="tok-str">'+esc(src.slice(i,j))+'</span>';
        i = j; continue;
      }
      // Triple-quoted string (no prefix)
      if((c === '"' || c === "'") && src[i+1] === c && src[i+2] === c){
        const tq = c+c+c;
        let end = src.indexOf(tq, i+3);
        end = (end === -1) ? n : end + 3;
        out += '<span class="tok-str">'+esc(src.slice(i,end))+'</span>';
        i = end; continue;
      }
      // Single-line string (no prefix)
      if(c === '"' || c === "'"){
        let j = i+1;
        while(j < n && src[j] !== c && src[j] !== '\n'){
          if(src[j] === '\\' && j+1 < n) j += 2; else j++;
        }
        if(j < n && src[j] === c) j++;
        out += '<span class="tok-str">'+esc(src.slice(i,j))+'</span>';
        i = j; continue;
      }
      // Decorator (@name.path) — only at start of line; otherwise it's matmul.
      if(c === '@'){
        let p = i-1;
        while(p >= 0 && (src[p] === ' ' || src[p] === '\t')) p--;
        const atLineStart = (p < 0 || src[p] === '\n');
        if(atLineStart){
          let j = i+1;
          while(j < n && /[a-zA-Z0-9_.]/.test(src[j])) j++;
          out += '<span class="tok-deco">'+esc(src.slice(i,j))+'</span>';
          i = j; continue;
        }
        // matmul operator — fall through as plain punctuation
      }
      // Number
      if(/[0-9]/.test(c) || (c === '.' && /[0-9]/.test(src[i+1] || ''))){
        let j = i;
        if(src[j] === '0' && (src[j+1] === 'x' || src[j+1] === 'X')){
          j += 2;
          while(j < n && /[0-9a-fA-F_]/.test(src[j])) j++;
        } else {
          while(j < n && /[0-9_]/.test(src[j])) j++;
          if(src[j] === '.' && /[0-9]/.test(src[j+1] || '')){
            j++;
            while(j < n && /[0-9_]/.test(src[j])) j++;
          }
          if(src[j] === 'e' || src[j] === 'E'){
            j++;
            if(src[j] === '+' || src[j] === '-') j++;
            while(j < n && /[0-9_]/.test(src[j])) j++;
          }
          if(src[j] === 'j' || src[j] === 'J') j++;
        }
        out += '<span class="tok-num">'+esc(src.slice(i,j))+'</span>';
        i = j; continue;
      }
      // Identifier
      if(/[a-zA-Z_]/.test(c)){
        let j = i;
        while(j < n && /[a-zA-Z0-9_]/.test(src[j])) j++;
        const id = src.slice(i,j);
        let cls = null;
        if(prevTok === 'def') cls = 'tok-fn';
        else if(prevTok === 'class') cls = 'tok-cls';
        else if(KW.has(id)) cls = 'tok-kw';
        else if(SOFT.has(id)) cls = 'tok-self';
        else if(BUILTIN.has(id)) cls = 'tok-builtin';
        else {
          // function call?
          let k = j;
          while(k < n && (src[k] === ' ' || src[k] === '\t')) k++;
          if(src[k] === '(') cls = 'tok-call';
        }
        if(cls) out += '<span class="'+cls+'">'+esc(id)+'</span>';
        else out += esc(id);
        prevTok = id;
        i = j; continue;
      }
      // Whitespace — keep prevTok
      if(c === ' ' || c === '\t' || c === '\n' || c === '\r'){
        out += c; i++; continue;
      }
      // Punctuation/operator — reset prevTok unless it's a dot (member access)
      if(c !== '.') prevTok = null;
      out += esc(c);
      i++;
    }
    return out;
  }

  function run(){
    document.querySelectorAll('pre > code').forEach(el => {
      if(el.dataset.hl) return;
      // Only highlight Python-like content. Skip if the block opts out via class="nohl".
      if(el.classList.contains('nohl')) return;
      const code = el.textContent;
      el.innerHTML = highlight(code);
      el.dataset.hl = '1';
    });
  }
  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', run);
  else run();
})();

// Header nav → clickable dropdown. Wraps the existing <nav> at runtime so
// no per-page HTML changes are needed as the course list grows.
(function(){
  function init(){
    const wrap = document.querySelector('.site-header .wrap');
    if(!wrap) return;
    const nav = wrap.querySelector('nav');
    if(!nav || nav.dataset.dropdownReady) return;

    const active = nav.querySelector('a.active');
    const label = active ? active.textContent.trim() : '강의 목록';

    const shell = document.createElement('div');
    shell.className = 'nav-shell';

    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'nav-toggle';
    btn.setAttribute('aria-expanded', 'false');
    btn.setAttribute('aria-haspopup', 'true');
    const labelEl = document.createElement('span');
    labelEl.className = 'nav-toggle-label';
    labelEl.textContent = label;
    const arrowEl = document.createElement('span');
    arrowEl.className = 'nav-toggle-arrow';
    arrowEl.setAttribute('aria-hidden', 'true');
    arrowEl.textContent = '▾';
    btn.appendChild(labelEl);
    btn.appendChild(arrowEl);

    nav.classList.add('nav-dropdown');
    nav.dataset.dropdownReady = '1';
    nav.parentNode.insertBefore(shell, nav);
    shell.appendChild(btn);
    shell.appendChild(nav);

    function close(){
      nav.classList.remove('open');
      btn.setAttribute('aria-expanded', 'false');
    }
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const open = nav.classList.toggle('open');
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    document.addEventListener('click', (e) => {
      if(!shell.contains(e.target)) close();
    });
    document.addEventListener('keydown', (e) => {
      if(e.key === 'Escape') close();
    });
  }
  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
