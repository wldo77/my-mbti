import html
import json

import streamlit as st
import streamlit.components.v1 as components


st.set_page_config(
    page_title="MBTI 단짝 포켓몬 찾기",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# MBTI별 포켓몬 정보와 결과에 사용할 강조색
POKEMON = {
    "INTJ": {
        "ko": "뮤츠", "en": "Mewtwo", "id": 150,
        "type": "에스퍼", "feature": "날카로운 지능과 강한 집중력",
        "reason": "큰 그림을 읽고 차근차근 전략을 세우는 모습이 잘 어울려요.\n조용히 깊이 생각하는 당신 곁에서 뮤츠는 든든한 두뇌 파트너가 되어 줄 거예요.",
        "accent": "#A78BDE", "ink": "#6843A5", "emoji": "🔮",
    },
    "INTP": {
        "ko": "메타몽", "en": "Ditto", "id": 132,
        "type": "노말", "feature": "상황에 따라 자유롭게 변신하는 호기심쟁이",
        "reason": "메타몽처럼 새로운 가능성을 관찰하고 실험하는 걸 좋아하죠.\n정해진 틀에 얽매이지 않는 둘은 엉뚱하고 멋진 아이디어를 함께 만들 수 있어요.",
        "accent": "#B7A0E6", "ink": "#6A4F9E", "emoji": "🧩",
    },
    "ENTJ": {
        "ko": "리자몽", "en": "Charizard", "id": 6,
        "type": "불꽃 / 비행", "feature": "자신감 넘치는 리더 기질과 강력한 추진력",
        "reason": "목표를 정하면 거침없이 나아가는 에너지가 닮았어요.\n리자몽과 함께라면 큰 도전도 멋지게 이끌어 갈 수 있을 거예요.",
        "accent": "#F28C45", "ink": "#B94D1D", "emoji": "🔥",
    },
    "ENTP": {
        "ko": "팬텀", "en": "Gengar", "id": 94,
        "type": "고스트 / 독", "feature": "장난기 가득하고 예측할 수 없는 매력",
        "reason": "새로운 아이디어와 재치 있는 장난을 즐기는 점이 닮았어요.\n팬텀과 함께라면 지루할 틈 없이 기발한 모험이 계속될 거예요.",
        "accent": "#9C83D6", "ink": "#59409A", "emoji": "👻",
    },
    "INFJ": {
        "ko": "라프라스", "en": "Lapras", "id": 131,
        "type": "물 / 얼음", "feature": "차분하고 다정한 마음, 편안한 동행",
        "reason": "다른 사람의 마음을 세심하게 살피는 당신과 라프라스는 잘 맞아요.\n서두르지 않고 깊은 이야기를 나누며 잔잔한 위로를 주고받을 수 있답니다.",
        "accent": "#73BFD0", "ink": "#247A91", "emoji": "🌊",
    },
    "INFP": {
        "ko": "이브이", "en": "Eevee", "id": 133,
        "type": "노말", "feature": "풍부한 가능성과 포근한 매력",
        "reason": "자기만의 세계와 다양한 가능성을 소중히 여기는 점이 닮았어요.\n이브이는 당신의 다정한 마음과 개성 있는 꿈을 편안하게 응원해 줄 거예요.",
        "accent": "#D7A66B", "ink": "#925B25", "emoji": "🍯",
    },
    "ENFJ": {
        "ko": "피카츄", "en": "Pikachu", "id": 25,
        "type": "전기", "feature": "밝고 씩씩하며 친구를 응원하는 에너지",
        "reason": "주변 사람들에게 힘을 주고 함께 기뻐하는 모습이 닮았어요.\n피카츄의 반짝이는 에너지가 당신의 따뜻한 리더십을 더욱 빛내 줄 거예요.",
        "accent": "#F2C94C", "ink": "#9A6A00", "emoji": "⚡",
    },
    "ENFP": {
        "ko": "토게피", "en": "Togepi", "id": 175,
        "type": "페어리", "feature": "희망과 행운을 전하는 사랑스러운 분위기",
        "reason": "새로운 만남과 즐거운 가능성을 반기는 점이 꼭 닮았어요.\n호기심 많은 당신과 토게피가 함께하면 작은 하루도 특별한 모험이 될 거예요.",
        "accent": "#E9A9C6", "ink": "#A04478", "emoji": "🌈",
    },
    "ISTJ": {
        "ko": "거북왕", "en": "Blastoise", "id": 9,
        "type": "물", "feature": "든든한 방어력과 책임감 있는 태도",
        "reason": "맡은 일을 꾸준히 해내고 약속을 중요하게 생각하는 점이 잘 맞아요.\n거북왕은 어떤 상황에서도 믿고 등을 맡길 수 있는 든든한 단짝이에요.",
        "accent": "#78A9E8", "ink": "#285E9E", "emoji": "💧",
    },
    "ISFJ": {
        "ko": "이상해씨", "en": "Bulbasaur", "id": 1,
        "type": "풀 / 독", "feature": "온화하고 친절하며 동료를 잘 돌봄",
        "reason": "주변을 세심하게 챙기고 작은 도움도 아끼지 않는 모습이 닮았어요.\n이상해씨와 함께라면 서로의 속도를 존중하며 천천히 성장할 수 있어요.",
        "accent": "#83C987", "ink": "#27713B", "emoji": "🌱",
    },
    "ESTJ": {
        "ko": "괴력몬", "en": "Machamp", "id": 68,
        "type": "격투", "feature": "힘과 끈기, 바로 행동으로 옮기는 실행력",
        "reason": "계획을 세우고 팀이 목표를 이루도록 이끄는 면이 잘 어울려요.\n괴력몬은 당신의 성실한 노력에 힘을 보태는 믿음직한 파트너가 될 거예요.",
        "accent": "#E58D91", "ink": "#9B3C46", "emoji": "💪",
    },
    "ESFJ": {
        "ko": "푸린", "en": "Jigglypuff", "id": 39,
        "type": "노말 / 페어리", "feature": "노래와 놀이로 분위기를 부드럽게 만드는 친구",
        "reason": "사람들과 어울리고 모두가 편안한 분위기를 만드는 점이 닮았어요.\n푸린의 노래와 당신의 다정함이 모이면 모임마다 웃음이 가득할 거예요.",
        "accent": "#F2A8C9", "ink": "#A83F79", "emoji": "🎤",
    },
    "ISTP": {
        "ko": "루카리오", "en": "Lucario", "id": 448,
        "type": "격투 / 강철", "feature": "민첩하고 침착하며 기운을 읽는 감각",
        "reason": "필요한 순간 빠르게 상황을 파악하고 직접 해결하는 점이 닮았어요.\n루카리오와 함께라면 말이 많지 않아도 서로를 믿는 멋진 팀이 될 수 있어요.",
        "accent": "#6EA9D9", "ink": "#245987", "emoji": "🥋",
    },
    "ISFP": {
        "ko": "리피아", "en": "Leafeon", "id": 470,
        "type": "풀", "feature": "자연을 닮은 차분함과 섬세한 감각",
        "reason": "아름다운 것과 편안한 순간을 소중히 여기는 점이 닮았어요.\n리피아와 숲길을 걸으며 나만의 감성과 평화로운 시간을 나눠 보세요.",
        "accent": "#9BCB79", "ink": "#4A7628", "emoji": "🍃",
    },
    "ESTP": {
        "ko": "갸라도스", "en": "Gyarados", "id": 130,
        "type": "물 / 비행", "feature": "강렬한 힘과 과감한 돌파력",
        "reason": "생각만 하기보다 직접 부딪치며 경험하는 에너지가 닮았어요.\n갸라도스와 함께라면 예상 밖의 상황도 자신 있게 돌파하는 짜릿한 팀이 되겠어요.",
        "accent": "#5CA9DA", "ink": "#155E90", "emoji": "🌪️",
    },
    "ESFP": {
        "ko": "잠만보", "en": "Snorlax", "id": 143,
        "type": "노말", "feature": "느긋하고 편안한 분위기와 큰 포용력",
        "reason": "사람들과 즐거운 시간을 보내고 순간의 행복을 누리는 점이 잘 맞아요.\n잠만보와 맛있는 간식을 나누며 웃고 쉬는 것만으로도 최고의 하루가 될 거예요.",
        "accent": "#7FB7A5", "ink": "#286B59", "emoji": "🍙",
    },
}

# 전체 화면 톤과 버튼 디자인
st.markdown(
    """
    <style>
      :root { --cream: #fff9e9; --butter: #ffe9a8; --honey: #f4c85d; --brown: #604b2b; }
      .stApp { background: linear-gradient(180deg, #fff9e9 0%, #fff4d2 55%, #fffaf0 100%); color: #604b2b; }
      [data-testid="stHeader"] { background: rgba(255,249,233,0.8); }
      [data-testid="stAppViewContainer"] .main .block-container { max-width: 1100px; padding-top: 1.6rem; padding-bottom: 3rem; }
      html, body, [class*="css"] { font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif; }
      h1, h2, h3 { font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif !important; font-weight: 800; color: #604b2b; }
      .hero { text-align:center; padding: 1.35rem 1.2rem 1.2rem; border: 2px solid #f6df9c; background: rgba(255,255,255,.72); border-radius: 28px; box-shadow: 0 8px 24px rgba(130,95,25,.08); }
      .hero-kicker { display:inline-block; background:#fff0bd; color:#8a641d; border-radius:999px; padding:7px 15px; font-size:17px; font-weight:700; margin-bottom:12px; }
      .hero h1 { font-size: clamp(2.3rem, 5vw, 3.6rem); margin: 0 0 .4rem; line-height:1.15; font-weight:900; }
      .hero p { font-size:19px; margin: 0.3rem 0; color:#80673d; }
      .section-label { font-family:'Malgun Gothic','Apple SD Gothic Neo',sans-serif; font-weight:800; font-size:1.55rem; margin:1.55rem 0 .5rem; color:#684e22; }
      .section-help { font-size:1.05rem; color:#8a744f; margin-bottom:.7rem; }
      .stButton > button { min-height: 3.4rem; border-radius: 16px; border: 2px solid #f2d887; background: #fffdf5; color: #725522; font-family:'Malgun Gothic','Apple SD Gothic Neo',sans-serif; font-weight:800; font-size:1.16rem; box-shadow:0 3px 0 #f1dea7; transition: transform .15s ease, box-shadow .15s ease, background .15s ease; }
      .stButton > button:hover { border-color:#e5b83e; background:#fff0bd; color:#684613; transform:translateY(-2px); box-shadow:0 5px 0 #ebcd78; }
      .stButton > button:focus { border-color:#cfa02a; color:#684613; }
      .tip { text-align:center; color:#9a835b; font-size:15px; padding:12px 0 0; }
      .footer-note { color:#9a835b; font-size:13px; text-align:center; padding:20px 5px 0; }
      div[data-testid="stAlert"] { border-radius: 16px; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <div class="hero-kicker">🌼 오늘의 작은 성격 탐험</div>
      <h1>나의 MBTI 단짝 포켓몬은?</h1>
      <p>나와 찰떡궁합인 포켓몬을 만나 봐요!</p>
      <p style="font-size:15px;color:#a1885a;margin-top:10px;">16가지 유형 중 내 MBTI를 골라 주세요 ✨</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if "selected_mbti" not in st.session_state:
    st.session_state.selected_mbti = None

st.markdown('<div class="section-label">🧡 내 MBTI 선택하기</div>', unsafe_allow_html=True)
st.markdown('<div class="section-help">잘 모르겠다면 평소 내 모습과 가장 가까운 유형을 골라 보세요.</div>', unsafe_allow_html=True)

MBTI_ORDER = [
    "INTJ", "INTP", "ENTJ", "ENTP",
    "INFJ", "INFP", "ENFJ", "ENFP",
    "ISTJ", "ISFJ", "ESTJ", "ESFJ",
    "ISTP", "ISFP", "ESTP", "ESFP",
]

# 4열 버튼 그리드
for start in range(0, len(MBTI_ORDER), 4):
    cols = st.columns(4, gap="medium")
    for col, mbti in zip(cols, MBTI_ORDER[start:start + 4]):
        with col:
            label = f"✅ {mbti}" if st.session_state.selected_mbti == mbti else mbti
            if st.button(label, key=f"mbti_{mbti}", use_container_width=True):
                st.session_state.selected_mbti = mbti
                st.balloons()

st.markdown('<div class="tip">💡 유형 버튼을 누르면 단짝 포켓몬과 만날 수 있어요. 결과 그림도 눌러 보세요!</div>', unsafe_allow_html=True)


def make_result_html(mbti: str, pokemon: dict) -> str:
    """결과 카드를 렌더링하는 HTML/CSS/JS. 외부 프런트엔드 파일은 필요 없습니다."""
    ko = html.escape(pokemon["ko"])
    en = html.escape(pokemon["en"])
    ptype = html.escape(pokemon["type"])
    feature = html.escape(pokemon["feature"])
    reason_lines = "<br>".join(html.escape(line) for line in pokemon["reason"].split("\n"))
    accent = pokemon["accent"]
    ink = pokemon["ink"]
    emoji = html.escape(pokemon["emoji"])
    image_url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{pokemon['id']}.png"
    fallback_url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{pokemon['id']}.png"
    # json.dumps로 JS 문자열 이스케이프
    fallback_js = json.dumps(fallback_url)

    return f'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  * {{ box-sizing:border-box; }}
  html, body {{ margin:0; padding:0; background:transparent; color:#604b2b; font-family:Arial,'Malgun Gothic',sans-serif; }}
  .result-card {{ position:relative; overflow:hidden; display:flex; align-items:stretch; gap:24px; padding:25px; border-radius:27px; border:2px solid color-mix(in srgb, {accent} 65%, white); background:linear-gradient(135deg,#fffef8 0%,#fff8e6 100%); box-shadow:0 10px 30px rgba(128,92,22,.11); }}
  .result-card:before {{ content:""; position:absolute; width:210px;height:210px;border-radius:50%; background:{accent}; opacity:.13; top:-93px;left:-80px; }}
  .art-side {{ position:relative; flex:0 0 42%; min-width:220px; display:flex; flex-direction:column; justify-content:center; align-items:center; padding:7px 0; }}
  .art-frame {{ position:relative; display:grid; place-items:center; width:min(100%,300px); aspect-ratio:1/1; border-radius:28px; background:radial-gradient(circle at 50% 43%, #fff 0%, color-mix(in srgb, {accent} 19%, #fff8e6) 66%, #fff4d5 100%); border:1px solid color-mix(in srgb, {accent} 38%, white); }}
  .pokemon-art {{ width:94%; height:94%; object-fit:contain; cursor:pointer; user-select:none; filter:drop-shadow(0 8px 5px rgba(90,70,30,.13)); transition:transform .3s cubic-bezier(.2,.8,.2,1), filter .3s ease; animation:arrival .7s cubic-bezier(.2,.8,.3,1) both, bob 3.1s ease-in-out .8s infinite; transform-origin:50% 72%; position:relative; z-index:2; }}
  .pokemon-art:hover {{ transform:translateY(-7px) rotate(-5deg) scale(1.08); filter:drop-shadow(0 14px 8px rgba(90,70,30,.22)); }}
  .pokemon-art:active {{ transform:scale(.92) rotate(4deg); }}
  .art-hint {{ margin-top:10px; color:#937c53; font-size:13px; text-align:center; }}
  .info-side {{ position:relative; flex:1; min-width:0; display:flex; flex-direction:column; justify-content:center; padding:8px 4px; }}
  .match-pill {{ align-self:flex-start; border-radius:999px; padding:7px 13px; font-weight:800; font-size:14px; color:{ink}; background:color-mix(in srgb, {accent} 24%, white); margin-bottom:12px; }}
  h1 {{ color:{ink}; font-size:clamp(28px,3.2vw,39px); line-height:1.12; margin:0 0 4px; letter-spacing:-.6px; }}
  .english {{ color:{ink}; font-size:18px; font-weight:700; margin-bottom:16px; opacity:.82; }}
  .mini-heading {{ font-size:14px; font-weight:800; color:#a17c39; letter-spacing:.4px; margin:10px 0 5px; }}
  .type-chip {{ display:inline-block; border-radius:10px; padding:6px 12px; color:{ink}; border:1px solid color-mix(in srgb, {accent} 55%, white); background:color-mix(in srgb, {accent} 17%, white); font-size:16px; font-weight:800; }}
  .feature {{ font-size:17px; line-height:1.55; color:#6d5b3b; font-weight:700; }}
  .reason {{ color:#705f43; font-size:16px; line-height:1.75; background:#fffdf7; border-left:4px solid {accent}; padding:11px 13px; border-radius:0 13px 13px 0; }}
  .signature {{ margin-top:14px; font-size:15px; font-weight:800; color:{ink}; }}
  .sparkle {{ position:absolute; z-index:3; pointer-events:none; font-size:22px; animation:sparkle 1s ease-out forwards; }}
  #confetti {{ position:fixed; inset:0; width:100%; height:100%; pointer-events:none; z-index:20; }}
  @keyframes arrival {{ 0%{{opacity:0;transform:translateY(24px) scale(.72) rotate(-8deg)}} 65%{{opacity:1;transform:translateY(-6px) scale(1.06) rotate(3deg)}} 100%{{transform:translateY(0) scale(1) rotate(0)}} }}
  @keyframes bob {{ 0%,100%{{translate:0 0}} 50%{{translate:0 -7px}} }}
  @keyframes sparkle {{ 0%{{opacity:0;transform:translate(-50%,-50%) scale(.3) rotate(0)}} 25%{{opacity:1}} 100%{{opacity:0;transform:translate(var(--dx),var(--dy)) scale(1.5) rotate(35deg)}} }}
  @media (max-width:650px) {{ .result-card{{flex-direction:column;gap:12px;padding:18px}} .art-side{{min-width:0}} .art-frame{{width:min(78vw,280px)}} .info-side{{padding:4px 2px}} h1{{font-size:32px}} .reason{{font-size:15px}} }}
  @media (prefers-reduced-motion: reduce) {{ .pokemon-art{{animation:none;transition:none}} *{{scroll-behavior:auto!important}} }}
</style>
</head>
<body>
<canvas id="confetti"></canvas>
<section class="result-card" id="resultCard">
  <div class="art-side">
    <div class="art-frame" id="artFrame">
      <span style="position:absolute;top:13px;left:16px;font-size:24px;opacity:.75">✦</span>
      <span style="position:absolute;right:17px;bottom:15px;font-size:22px;opacity:.75">✧</span>
      <img id="pokemonArt" class="pokemon-art" src="{image_url}" alt="{ko} 포켓몬 그림">
    </div>
    <div class="art-hint">👆 그림을 톡 눌러 반짝 효과를 확인해 보세요!</div>
  </div>
  <div class="info-side">
    <div class="match-pill">{emoji} {mbti}의 오늘의 단짝</div>
    <h1>{ko}</h1>
    <div class="english">{en}</div>
    <div class="mini-heading">POKÉMON TYPE · 타입</div>
    <div><span class="type-chip">{ptype}</span></div>
    <div class="mini-heading">✨ 이런 매력이 있어요</div>
    <div class="feature">{feature}</div>
    <div class="mini-heading">💛 왜 잘 어울릴까요?</div>
    <div class="reason">{reason_lines}</div>
    <div class="signature">{emoji} 너와 함께라면 매일이 조금 더 특별해!</div>
  </div>
</section>
<script>
(function() {{
  const canvas = document.getElementById('confetti');
  const ctx = canvas.getContext('2d');
  const colors = ['{accent}', '#FFD166', '#FFE9A8', '#F6A6B7', '#FFFFFF', '#B7DDA5'];
  let pieces = [];
  let frameId = null;
  function resize() {{
    const dpr = window.devicePixelRatio || 1;
    canvas.width = Math.max(1, window.innerWidth * dpr);
    canvas.height = Math.max(1, window.innerHeight * dpr);
    canvas.style.width = window.innerWidth + 'px';
    canvas.style.height = window.innerHeight + 'px';
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }}
  function celebrate() {{
    resize();
    pieces = Array.from({{length:105}}, () => ({{
      x: Math.random() * window.innerWidth,
      y: -20 - Math.random() * window.innerHeight * .65,
      w: 5 + Math.random() * 7,
      h: 7 + Math.random() * 9,
      vx: (Math.random() - .5) * 3.2,
      vy: 2 + Math.random() * 4.2,
      spin: Math.random() * 6,
      vs: (Math.random() - .5) * .2,
      color: colors[Math.floor(Math.random() * colors.length)],
      alpha: 1
    }}));
    if (frameId) cancelAnimationFrame(frameId);
    let ticks = 0;
    function draw() {{
      ctx.clearRect(0, 0, window.innerWidth, window.innerHeight);
      pieces.forEach(p => {{
        p.x += p.vx; p.y += p.vy; p.spin += p.vs;
        if (ticks > 45) p.alpha = Math.max(0, p.alpha - .012);
        ctx.save(); ctx.globalAlpha = p.alpha; ctx.translate(p.x, p.y); ctx.rotate(p.spin);
        ctx.fillStyle = p.color; ctx.fillRect(-p.w / 2, -p.h / 2, p.w, p.h); ctx.restore();
      }});
      ticks++;
      if (ticks < 135) frameId = requestAnimationFrame(draw);
      else {{ ctx.clearRect(0, 0, window.innerWidth, window.innerHeight); frameId = null; }}
    }}
    draw();
  }}
  const art = document.getElementById('pokemonArt');
  const frame = document.getElementById('artFrame');
  const fallbackImage = {fallback_js};
  art.addEventListener('error', function() {{
    if (!art.dataset.fallbackTried) {{ art.dataset.fallbackTried = '1'; art.src = fallbackImage; }}
  }});
  art.addEventListener('click', function(event) {{
    const rect = frame.getBoundingClientRect();
    const x = event.clientX - rect.left; const y = event.clientY - rect.top;
    for (let i = 0; i < 7; i++) {{
      const star = document.createElement('span'); star.className = 'sparkle';
      star.textContent = ['✦','✧','♥','✨','★'][Math.floor(Math.random() * 5)];
      star.style.left = x + 'px'; star.style.top = y + 'px';
      star.style.color = colors[Math.floor(Math.random() * colors.length)];
      star.style.setProperty('--dx', ((Math.random() - .5) * 125) + 'px');
      star.style.setProperty('--dy', (-30 - Math.random() * 100) + 'px');
      frame.appendChild(star); setTimeout(() => star.remove(), 1050);
    }}
    art.animate([{{transform:'scale(1) rotate(0deg)'}},{{transform:'scale(1.12) rotate(-8deg)'}},{{transform:'scale(.96) rotate(5deg)'}},{{transform:'scale(1) rotate(0deg)'}}], {{duration:520,easing:'cubic-bezier(.2,.8,.3,1)'}});
    celebrate();
  }});
  window.addEventListener('resize', resize);
  // 결과가 나타날 때도 작은 축하 효과를 한 번 보여 줍니다.
  if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) celebrate();
}})();
</script>
</body>
</html>'''


if st.session_state.selected_mbti:
    selected = st.session_state.selected_mbti
    pokemon = POKEMON[selected]
    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='section-label'>🎉 짝꿍 찾기 성공! <span style='color:{pokemon['ink']}'>{selected}</span>의 단짝을 소개할게요</div>",
        unsafe_allow_html=True,
    )
    components.html(make_result_html(selected, pokemon), height=560, scrolling=False)
    st.markdown(
        "<div class='footer-note'>포켓몬 이미지는 <a href='https://github.com/PokeAPI/sprites' target='_blank' rel='noreferrer'>PokeAPI Sprites</a> 저장소에서 불러옵니다.\nMBTI와 포켓몬의 조합은 재미를 위한 창작 콘텐츠예요. 🌼</div>",
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        """
        <div style="text-align:center;margin:28px auto 4px;max-width:600px;padding:20px;border-radius:22px;background:rgba(255,255,255,.6);border:1px dashed #e9cc7c;">
          <div style="font-size:40px;">🥚✨</div>
          <div style="font-size:22px;font-weight:800;color:#765a27;margin:8px 0;">어떤 포켓몬이 기다리고 있을까요?</div>
          <div style="font-size:16px;color:#9a8050;">위에서 MBTI를 선택하면 단짝의 모습이 나타나요.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
