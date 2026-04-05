import streamlit as st
import base64
import time
from firebase_config import init_firebase, get_game_ref
from game_logic import (
    fetch_random_face, generate_game_id,
    create_game_state, compute_round_winner
)

st.set_page_config(
    page_title="Punchline IA",
    page_icon="🎭",
    layout="centered"
)

# ── Init session ──────────────────────────────────────────────────────────────
for key, default in [
    ("game_id", None),
    ("player_name", None),
    ("is_host", False),
    ("home_view", "menu"),
    ("dark_mode", False),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ── Thème clair / sombre ──────────────────────────────────────────────────────
dark = st.session_state.dark_mode

if dark:
    BG          = "#0f1117"
    BG2         = "#1a1d27"
    BG3         = "#22263a"
    TEXT        = "#e8eaf6"
    TEXT2       = "#9096b0"
    BLUE        = "#5c8fff"
    BLUE_DARK   = "#3a6fdf"
    BORDER      = "#2e3250"
    SUCCESS_BG  = "#0d2318"
    SUCCESS_BDR = "#2ea05a"
    INFO_BG     = "#0d1730"
    INFO_BDR    = "#3a6fdf"
    CARD_BG     = "#1a1d27"
    CARD_BDR    = "#2e3250"
    WIN_BG      = "#0d2318"
    WIN_BDR     = "#2ea05a"
else:
    BG          = "#ffffff"
    BG2         = "#f8f9fa"
    BG3         = "#f1f3f4"
    TEXT        = "#1a1a2e"
    TEXT2       = "#5f6368"
    BLUE        = "#4285f4"
    BLUE_DARK   = "#3367d6"
    BORDER      = "#d2e3fc"
    SUCCESS_BG  = "#e6f4ea"
    SUCCESS_BDR = "#34a853"
    INFO_BG     = "#e8f0fe"
    INFO_BDR    = "#4285f4"
    CARD_BG     = "#ffffff"
    CARD_BDR    = "#e0e0e0"
    WIN_BG      = "#e6f4ea"
    WIN_BDR     = "#34a853"

st.markdown(f"""
<style>
* {{ box-sizing: border-box; }}

/* ── Fond global ── */
.stApp {{
    background-color: {BG} !important;
}}
section[data-testid="stSidebar"] {{
    display: none;
}}
.block-container {{
    max-width: 520px !important;
    padding: 0.5rem 1rem 5rem 1rem !important;
    background-color: {BG} !important;
}}

/* ── Texte global ── */
body, p, div, span, label {{
    color: {TEXT} !important;
}}
h1, h2, h3, h4 {{
    color: {TEXT} !important;
}}
.stMarkdown p {{
    color: {TEXT} !important;
}}

/* ── Toggle thème ── */
.theme-bar {{
    display: flex;
    justify-content: flex-end;
    align-items: center;
    padding: 8px 0 4px 0;
    gap: 8px;
}}
.theme-label {{
    font-size: 0.82em;
    color: {TEXT2};
}}

/* ── Hero ── */
.hero {{
    text-align: center;
    padding: 24px 0 20px 0;
}}
.hero-emoji {{ font-size: 52px; line-height: 1; margin-bottom: 6px; }}
.hero-title {{
    font-size: 1.9em;
    font-weight: 800;
    color: {TEXT} !important;
    margin: 0 0 6px 0;
}}
.hero-sub {{
    font-size: 0.92em;
    color: {TEXT2} !important;
    line-height: 1.55;
    margin: 0;
}}

/* ── Cards menu ── */
.menu-card {{
    background: {BG2};
    border: 1.5px solid {BORDER};
    border-radius: 18px;
    padding: 22px 18px 14px 18px;
    margin: 10px 0;
    text-align: center;
}}
.menu-card-emoji {{ font-size: 30px; margin-bottom: 5px; }}
.menu-card-title {{
    font-size: 1.1em;
    font-weight: 700;
    color: {TEXT} !important;
    margin: 0 0 3px 0;
}}
.menu-card-desc {{
    font-size: 0.86em;
    color: {TEXT2} !important;
    margin: 0 0 14px 0;
}}

/* ── Boutons ── */
div.stButton > button {{
    border-radius: 12px !important;
    font-weight: 600 !important;
    font-size: 1em !important;
    padding: 12px 0 !important;
    width: 100%;
    transition: all 0.18s !important;
    background: {BG2} !important;
    color: {BLUE} !important;
    border: 1.5px solid {BLUE} !important;
}}
div.stButton > button[kind="primary"] {{
    background: {BLUE} !important;
    border-color: {BLUE} !important;
    color: white !important;
}}
div.stButton > button[kind="primary"]:hover {{
    background: {BLUE_DARK} !important;
    border-color: {BLUE_DARK} !important;
}}
div.stButton > button:not([kind="primary"]):hover {{
    background: {INFO_BG} !important;
}}

/* ── Inputs ── */
div.stTextInput > div > div > input,
div.stTextArea > div > div > textarea,
div.stNumberInput > div > div > input {{
    border-radius: 10px !important;
    font-size: 1em !important;
    padding: 10px 14px !important;
    background: {BG2} !important;
    color: {TEXT} !important;
    border-color: {BORDER} !important;
}}
div.stSlider > div {{
    color: {TEXT} !important;
}}

/* ── Code partie ── */
.game-code {{
    background: {INFO_BG};
    border-radius: 16px;
    padding: 18px;
    text-align: center;
    margin: 14px 0;
    border: 1.5px solid {INFO_BDR};
}}
.game-code-label {{
    font-size: 0.78em;
    color: {BLUE} !important;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    font-weight: 700;
    margin-bottom: 4px;
}}
.game-code-value {{
    font-size: 2.8em;
    font-weight: 900;
    color: {TEXT} !important;
    letter-spacing: 0.22em;
    line-height: 1;
}}

/* ── Boîtes statut ── */
.box-info {{
    background: {INFO_BG};
    border-left: 4px solid {INFO_BDR};
    border-radius: 8px;
    padding: 11px 14px;
    margin: 8px 0;
    font-size: 0.91em;
    color: {TEXT} !important;
}}
.box-success {{
    background: {SUCCESS_BG};
    border-left: 4px solid {SUCCESS_BDR};
    border-radius: 8px;
    padding: 11px 14px;
    margin: 8px 0;
    font-size: 0.91em;
    color: {TEXT} !important;
}}
.box-wait {{
    background: {INFO_BG};
    border-left: 4px solid {INFO_BDR};
    border-radius: 8px;
    padding: 11px 14px;
    margin: 8px 0;
    font-size: 0.91em;
    color: {TEXT} !important;
}}

/* ── Chip joueur ── */
.player-chip {{
    display: inline-block;
    background: {BG3};
    border-radius: 20px;
    padding: 5px 13px;
    margin: 3px 3px 3px 0;
    font-size: 0.9em;
    color: {TEXT} !important;
    font-weight: 500;
    border: 1px solid {BORDER};
}}

/* ── Image compacte (phase écriture) ── */
.img-compact {{
    border-radius: 14px;
    overflow: hidden;
    margin: 10px 0 14px 0;
    box-shadow: 0 3px 16px rgba(0,0,0,0.18);
    max-height: 200px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: {BG3};
}}
.img-compact img {{
    width: 100%;
    max-height: 200px;
    object-fit: cover;
    object-position: center top;
    display: block;
}}

/* ── Image pleine (vote/résultats) ── */
.img-full {{
    border-radius: 16px;
    overflow: hidden;
    margin: 10px 0 16px 0;
    box-shadow: 0 4px 20px rgba(0,0,0,0.18);
}}
.img-full img {{
    width: 100%;
    display: block;
}}

/* ── Carte punchline ── */
.punchline-card {{
    background: {CARD_BG};
    border: 1.5px solid {CARD_BDR};
    border-radius: 14px;
    padding: 15px 17px 13px 17px;
    margin: 10px 0 4px 0;
}}
.punchline-card-winner {{
    background: {WIN_BG};
    border: 1.5px solid {WIN_BDR};
    border-radius: 14px;
    padding: 15px 17px 13px 17px;
    margin: 10px 0 4px 0;
}}
.pc-identity {{
    font-size: 1em;
    font-weight: 700;
    color: {TEXT} !important;
    margin-bottom: 2px;
}}
.pc-job {{
    font-size: 0.84em;
    color: {TEXT2} !important;
    margin-bottom: 10px;
}}
.pc-quote {{
    font-size: 1.02em;
    font-style: italic;
    color: {TEXT} !important;
    border-left: 3px solid {BLUE};
    padding-left: 10px;
    margin: 0;
    line-height: 1.5;
}}
.pc-votes {{
    font-size: 0.82em;
    font-weight: 700;
    color: {BLUE} !important;
    margin-top: 8px;
}}

/* ── Formulaire fiche (phase écriture) ── */
.fiche-form {{
    background: {BG2};
    border-radius: 16px;
    padding: 18px 16px 14px 16px;
    border: 1.5px solid {BORDER};
    margin-top: 4px;
}}

/* ── Score row ── */
.score-row {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 14px;
    border-radius: 10px;
    margin: 5px 0;
    background: {BG2};
    font-size: 0.96em;
    color: {TEXT} !important;
    border: 1px solid {BORDER};
}}
.score-row-top {{
    background: {INFO_BG};
    border-color: {INFO_BDR};
    font-weight: 700;
}}
.score-pts {{
    font-weight: 800;
    color: {BLUE} !important;
}}

/* ── Badge tour ── */
.round-badge {{
    display: inline-block;
    background: {BLUE};
    color: white !important;
    border-radius: 20px;
    padding: 3px 14px;
    font-size: 0.8em;
    font-weight: 700;
    margin-bottom: 6px;
    letter-spacing: 0.03em;
}}

/* ── Séparateur ── */
hr {{
    border-color: {BORDER} !important;
    margin: 14px 0 !important;
}}

/* ── Footer ── */
.footer {{
    text-align: center;
    color: {TEXT2} !important;
    font-size: 0.78em;
    margin-top: 28px;
    padding-top: 10px;
    border-top: 1px solid {BORDER};
}}
.footer a {{ color: {BLUE} !important; }}

/* ── Progress label ── */
.prog-label {{
    font-size: 0.8em;
    color: {TEXT2} !important;
    margin-bottom: 3px;
    text-align: right;
}}
</style>
""", unsafe_allow_html=True)

# ── Firebase ──────────────────────────────────────────────────────────────────
init_firebase()

def get_game() -> dict:
    return get_game_ref(st.session_state.game_id).get() or {}

def update_game(data: dict):
    get_game_ref(st.session_state.game_id).update(data)

# ── Helpers UI ────────────────────────────────────────────────────────────────

def theme_toggle():
    """Petit bouton lune/soleil en haut à droite."""
    icon = "☀️ Clair" if dark else "🌙 Sombre"
    col = st.columns([4, 1])[1]
    with col:
        if st.button(icon, key="theme_btn"):
            st.session_state.dark_mode = not dark
            st.rerun()

def info_box(text):
    st.markdown(
        f'<div class="box-info">ℹ️ {text}</div>',
        unsafe_allow_html=True
    )

def success_box(text):
    st.markdown(
        f'<div class="box-success">✅ {text}</div>',
        unsafe_allow_html=True
    )

def wait_box(text):
    st.markdown(
        f'<div class="box-wait">⏳ {text}</div>',
        unsafe_allow_html=True
    )

def safe_progress(done: int, total: int, label: str = ""):
    ratio = min(done / max(total, 1), 1.0)
    if label:
        st.markdown(
            f'<div class="prog-label">{label}</div>',
            unsafe_allow_html=True
        )
    st.progress(ratio)

def round_badge(current, total):
    st.markdown(
        f'<div class="round-badge">Tour {current} / {total}</div>',
        unsafe_allow_html=True
    )

def show_image(img_b64: str, compact: bool = False):
    """
    compact=True  → petite image (phase écriture, pour laisser la place au formulaire)
    compact=False → image pleine largeur (vote, résultats)
    """
    if not img_b64:
        return
    css_class = "img-compact" if compact else "img-full"
    st.markdown(
        f'<div class="{css_class}">'
        f'<img src="data:image/jpeg;base64,{img_b64}"/>'
        f'</div>',
        unsafe_allow_html=True
    )

def punchline_card(fiche: dict, author: str,
                   nb_votes: int = None, winner: bool = False,
                   medal: str = ""):
    """
    Rendu HTML sécurisé d'une carte punchline.
    unsafe_allow_html=True obligatoire — c'était le bug original.
    """
    css = "punchline-card-winner" if winner else "punchline-card"
    votes_html = (
        f'<div class="pc-votes">{nb_votes} vote(s)</div>'
        if nb_votes is not None else ""
    )
    medal_html = f"<span>{medal}</span> " if medal else ""
    st.markdown(f"""
<div class="{css}">
    <div class="pc-identity">{medal_html}{fiche.get('prenom','?')}, {fiche.get('age','?')} ans</div>
    <div class="pc-job">💼 {fiche.get('metier','?')} &nbsp;·&nbsp; par <em>{author}</em></div>
    <p class="pc-quote">« {fiche.get('punchline','?')} »</p>
    {votes_html}
</div>
""", unsafe_allow_html=True)

def score_table(scores: dict, highlight_winners=None):
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    medals = ["🥇", "🥈", "🥉"]
    max_pts = sorted_scores[0][1] if sorted_scores else 0
    for rank, (p, s) in enumerate(sorted_scores):
        is_top = (s == max_pts)
        css = "score-row score-row-top" if is_top else "score-row"
        medal = medals[rank] if rank < 3 else f"{rank+1}."
        crown = " 🏆" if highlight_winners and p in highlight_winners else ""
        st.markdown(f"""
<div class="{css}">
    <span>{medal} {p}{crown}</span>
    <span class="score-pts">{s} pts</span>
</div>
""", unsafe_allow_html=True)

# ── ACCUEIL ───────────────────────────────────────────────────────────────────

def screen_home():
    theme_toggle()
    view = st.session_state.home_view

    if view == "menu":
        st.markdown(f"""
<div class="hero">
    <div class="hero-emoji">🎭</div>
    <h1 class="hero-title">Punchline IA</h1>
    <p class="hero-sub">Inventez l'identité et la réplique<br>
    de visages générés par IA.<br>Le plus drôle remporte la manche !</p>
</div>
""", unsafe_allow_html=True)

        st.markdown(f"""
<div class="menu-card">
    <div class="menu-card-emoji">🎲</div>
    <p class="menu-card-title">Nouvelle partie</p>
    <p class="menu-card-desc">Crée une partie et partage le code à tes amis.</p>
</div>
""", unsafe_allow_html=True)
        if st.button("Créer une partie", use_container_width=True, type="primary"):
            st.session_state.home_view = "create"
            st.rerun()

        st.markdown(f"""
<div class="menu-card">
    <div class="menu-card-emoji">🚪</div>
    <p class="menu-card-title">Rejoindre</p>
    <p class="menu-card-desc">Entre le code donné par l'hôte.</p>
</div>
""", unsafe_allow_html=True)
        if st.button("Rejoindre une partie", use_container_width=True):
            st.session_state.home_view = "join"
            st.rerun()

        st.markdown(f"""
<div class="footer">
    Images · <a href="https://thispersondoesnotexist.com">thispersondoesnotexist.com</a>
</div>
""", unsafe_allow_html=True)

    elif view == "create":
        theme_toggle()
        if st.button("← Retour"):
            st.session_state.home_view = "menu"
            st.rerun()
        st.markdown("## 🎲 Créer une partie")
        info_box("Tu seras l'hôte. Tes amis rejoignent avec le code.")
        name = st.text_input("Ton prénom", max_chars=20,
                             placeholder="Ex : Sophie", key="host_name")
        num_rounds = st.slider("Nombre de tours", min_value=3, max_value=20, value=5)
        if st.button("🚀 Créer la partie", use_container_width=True, type="primary"):
            if not name.strip():
                st.error("Entre ton prénom !")
                return
            game_id = generate_game_id()
            get_game_ref(game_id).set(create_game_state(name.strip(), num_rounds))
            st.session_state.update({
                "game_id": game_id,
                "player_name": name.strip(),
                "is_host": True,
                "home_view": "menu"
            })
            st.rerun()

    elif view == "join":
        theme_toggle()
        if st.button("← Retour"):
            st.session_state.home_view = "menu"
            st.rerun()
        st.markdown("## 🚪 Rejoindre une partie")
        info_box("Demande le code 6 caractères à l'hôte.")
        code = st.text_input("Code de partie", max_chars=6,
                             placeholder="AZ48KP", key="join_code").upper().strip()
        name = st.text_input("Ton prénom", max_chars=20,
                             placeholder="Ex : Lucas", key="join_name")
        if st.button("✅ Rejoindre", use_container_width=True, type="primary"):
            if not code or not name.strip():
                st.error("Remplis tous les champs !")
                return
            game_ref = get_game_ref(code)
            game = game_ref.get()
            if not game:
                st.error("Partie introuvable.")
                return
            if game.get("status") != "waiting":
                st.error("Cette partie a déjà commencé.")
                return
            n = name.strip()
            if n in game.get("players", []):
                st.error(f"Le prénom « {n} » est déjà pris.")
                return
            players = game.get("players", []) + [n]
            scores = game.get("scores", {})
            scores[n] = 0
            game_ref.update({"players": players, "scores": scores})
            st.session_state.update({
                "game_id": code,
                "player_name": n,
                "is_host": False,
                "home_view": "menu"
            })
            st.rerun()

# ── LOBBY ─────────────────────────────────────────────────────────────────────

def screen_lobby(game: dict):
    theme_toggle()
    players = game.get("players", [])
    game_id = st.session_state.game_id

    st.markdown("## 🎭 Salle d'attente")
    st.markdown(f"""
<div class="game-code">
    <div class="game-code-label">Code de la partie</div>
    <div class="game-code-value">{game_id}</div>
</div>
""", unsafe_allow_html=True)

    info_box("Partage ce code. Tes amis peuvent rejoindre jusqu'au lancement.")
    st.markdown(f"**Joueurs ({len(players)})**")
    chips = "".join(
        f'<span class="player-chip">{"👑 " if p == game.get("host") else ""}{p}</span>'
        for p in players
    )
    st.markdown(f'<div style="margin:8px 0 14px 0">{chips}</div>',
                unsafe_allow_html=True)
    st.caption(f"Nombre de tours : **{game.get('num_rounds', 5)}**")

    if st.session_state.is_host:
        if len(players) < 2:
            wait_box("En attente d'au moins un autre joueur...")
        else:
            if st.button("🚀 Lancer !", use_container_width=True, type="primary"):
                with st.spinner("Chargement du premier visage IA..."):
                    try:
                        img_b64 = base64.b64encode(fetch_random_face()).decode()
                        update_game({
                            "status": "writing", "image_data": img_b64,
                            "punchlines": {}, "votes": {}, "round_winner": None
                        })
                    except Exception as e:
                        st.error(f"Erreur : {e}")
        time.sleep(3)
        st.rerun()
    else:
        wait_box("En attente que l'hôte lance la partie...")
        time.sleep(3)
        st.rerun()

# ── PHASE ÉCRITURE — UX mobile optimisée ─────────────────────────────────────

def screen_writing(game: dict):
    theme_toggle()
    player = st.session_state.player_name
    current_round = game.get("current_round", 1)
    num_rounds = game.get("num_rounds", 5)
    punchlines = game.get("punchlines", {}) or {}
    players = game.get("players", [])

    round_badge(current_round, num_rounds)
    st.markdown("## ✍️ Qui est-ce ?")

    # Image COMPACTE — 200px max — pour laisser le formulaire visible sans scroller
    show_image(game.get("image_data"), compact=True)

    if player not in punchlines:
        # Formulaire dans une carte visuelle
        st.markdown(f'<div class="fiche-form">', unsafe_allow_html=True)
        st.markdown("**Inventez son identité**")

        col1, col2 = st.columns([3, 2])
        with col1:
            prenom = st.text_input("Prénom", max_chars=30,
                                   key=f"prenom_{current_round}",
                                   placeholder="Jean-Michel",
                                   label_visibility="collapsed")
        with col2:
            age = st.number_input("Âge", min_value=1, max_value=120,
                                  value=35, key=f"age_{current_round}",
                                  label_visibility="collapsed")

        metier = st.text_input("💼 Métier", max_chars=50,
                               key=f"metier_{current_round}",
                               placeholder="Vendeur de matelas",
                               label_visibility="collapsed")

        punchline = st.text_area("💬 Réplique",
                                 max_chars=200, height=80,
                                 key=f"punchline_{current_round}",
                                 placeholder="« Non mais tu me prends pour qui là ? »",
                                 label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)

        # Placeholders sous les inputs pour guider l'utilisateur
        st.markdown(
            f'<div style="display:flex;gap:6px;margin:-6px 0 10px 0;">'
            f'<span style="flex:3;font-size:0.75em;color:{TEXT2};padding-left:4px;">Prénom</span>'
            f'<span style="flex:2;font-size:0.75em;color:{TEXT2};padding-left:4px;">Âge</span>'
            f'</div>',
            unsafe_allow_html=True
        )

        if st.button("✅ Valider ma fiche", use_container_width=True, type="primary"):
            if not prenom.strip() or not metier.strip() or not punchline.strip():
                st.error("Remplis tous les champs !")
            else:
                get_game_ref(st.session_state.game_id)\
                    .child("punchlines").child(player).set({
                        "prenom": prenom.strip(),
                        "age": int(age),
                        "metier": metier.strip(),
                        "punchline": punchline.strip()
                    })
                st.rerun()
    else:
        fiche = punchlines[player]
        success_box(
            f"<strong>{fiche['prenom']}</strong>, {fiche['age']} ans, "
            f"<em>{fiche['metier']}</em><br>« {fiche['punchline']} »"
        )
        count_done = len(punchlines)
        count_total = len(players)
        safe_progress(count_done, count_total,
                      f"{count_done}/{count_total} joueurs prêts")

        if count_done >= count_total:
            if st.button("➡️ Passer au vote !",
                         use_container_width=True, type="primary"):
                if get_game().get("status") == "writing":
                    update_game({"status": "voting"})
                st.rerun()
        else:
            wait_box(f"En attente des autres... ({count_done}/{count_total})")
            time.sleep(3)
            st.rerun()

# ── PHASE VOTE ────────────────────────────────────────────────────────────────

def screen_voting(game: dict):
    import random
    theme_toggle()
    player = st.session_state.player_name
    current_round = game.get("current_round", 1)
    num_rounds = game.get("num_rounds", 5)
    punchlines = game.get("punchlines", {}) or {}
    votes = game.get("votes", {}) or {}
    players = game.get("players", [])

    round_badge(current_round, num_rounds)
    st.markdown("## 🗳️ Vote !")

    # Image pleine largeur pour la phase vote
    show_image(game.get("image_data"), compact=False)

    if player not in votes:
        st.markdown("**Quelle fiche t'a le plus convaincu ?**")

        items = list(punchlines.items())
        random.seed(f"{st.session_state.game_id}_{current_round}")
        random.shuffle(items)

        for author, fiche in items:
            # ✅ FIX : unsafe_allow_html=True présent dans punchline_card
            punchline_card(fiche, author)
            if author != player:
                if st.button(
                    "👍 Voter pour cette fiche",
                    key=f"vote_{author}",
                    use_container_width=True
                ):
                    get_game_ref(st.session_state.game_id)\
                        .child("votes").child(player).set(author)
                    st.rerun()
            else:
                st.markdown(
                    f'<div style="font-size:0.8em;color:{TEXT2};'
                    f'margin:-2px 0 8px 4px;">← ta fiche</div>',
                    unsafe_allow_html=True
                )
            st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    else:
        success_box("Tu as voté !")
        count_voted = len(votes)
        count_total = len(players)
        safe_progress(count_voted, count_total,
                      f"{count_voted}/{count_total} votes reçus")

        if count_voted >= count_total:
            if st.button("📊 Voir les résultats",
                         use_container_width=True, type="primary"):
                if get_game().get("status") == "voting":
                    winners, vote_counts = compute_round_winner(punchlines, votes)
                    scores = game.get("scores", {p: 0 for p in players})
                    if winners:
                        pts = max(vote_counts.values())
                        for w in winners:
                            scores[w] = scores.get(w, 0) + pts
                    update_game({
                        "status": "results",
                        "round_winner": winners,
                        "scores": scores
                    })
                st.rerun()
        else:
            wait_box(f"En attente des autres... ({count_voted}/{count_total})")
            time.sleep(3)
            st.rerun()

# ── RÉSULTATS ─────────────────────────────────────────────────────────────────

def screen_results(game: dict):
    theme_toggle()
    current_round = game.get("current_round", 1)
    num_rounds = game.get("num_rounds", 5)
    punchlines = game.get("punchlines", {}) or {}
    votes = game.get("votes", {}) or {}
    scores = game.get("scores", {}) or {}
    winners = game.get("round_winner") or []
    players = game.get("players", [])
    if isinstance(winners, str):
        winners = [winners]

    round_badge(current_round, num_rounds)
    st.markdown("## 🏆 Résultats")

    show_image(game.get("image_data"), compact=False)

    if winners:
        if len(winners) == 1:
            success_box(f"🥇 Vainqueur du tour : <strong>{winners[0]}</strong> !")
        else:
            noms = " &amp; ".join(f"<strong>{w}</strong>" for w in winners)
            success_box(f"🤝 Égalité ! {noms} — points partagés !")

    st.markdown("---")
    st.markdown("**Toutes les fiches**")
    _, vote_counts = compute_round_winner(punchlines, votes)
    sorted_fiches = sorted(punchlines.items(),
                           key=lambda x: vote_counts.get(x[0], 0), reverse=True)
    medals = ["🥇", "🥈", "🥉"]
    for rank, (author, fiche) in enumerate(sorted_fiches):
        punchline_card(
            fiche, author,
            nb_votes=vote_counts.get(author, 0),
            winner=(author in winners),
            medal=medals[rank] if rank < 3 else f"{rank+1}."
        )

    st.markdown("---")
    st.markdown("**🎯 Scores cumulés**")
    score_table(scores)
    st.markdown("---")

    if current_round >= num_rounds:
        if st.button("🎉 Classement final !",
                     use_container_width=True, type="primary"):
            if get_game().get("status") == "results":
                update_game({"status": "finished"})
            st.rerun()
    else:
        if st.button(f"➡️ Tour {current_round + 1}",
                     use_container_width=True, type="primary"):
            if get_game().get("status") == "results":
                with st.spinner("Chargement..."):
                    try:
                        img_b64 = base64.b64encode(fetch_random_face()).decode()
                        update_game({
                            "status": "writing",
                            "current_round": current_round + 1,
                            "image_data": img_b64,
                            "punchlines": {}, "votes": {}, "round_winner": None
                        })
                    except Exception as e:
                        st.error(f"Erreur : {e}")
            st.rerun()

# ── FIN ───────────────────────────────────────────────────────────────────────

def screen_finished(game: dict):
    theme_toggle()
    scores = game.get("scores", {}) or {}
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    max_pts = sorted_scores[0][1] if sorted_scores else 0
    champions = [p for p, s in sorted_scores if s == max_pts]

    st.balloons()
    st.markdown("## 🎉 Fin de partie !")
    if len(champions) == 1:
        st.markdown(f"### 🏆 Champion : **{champions[0]}** — {max_pts} pts !")
    else:
        noms = " & ".join(f"**{c}**" for c in champions)
        st.markdown(f"### 🤝 Égalité ! {noms} — {max_pts} pts chacun !")

    st.markdown("---")
    st.markdown("**Classement final**")
    score_table(scores, highlight_winners=champions)
    st.markdown("---")

    if st.button("🔄 Nouvelle partie", use_container_width=True, type="primary"):
        st.session_state.update({
            "game_id": None, "player_name": None,
            "is_host": False, "home_view": "menu"
        })
        st.rerun()

# ── ROUTEUR ───────────────────────────────────────────────────────────────────

def main():
    if not st.session_state.game_id:
        screen_home()
        return
    game = get_game()
    routing = {
        "waiting":  screen_lobby,
        "writing":  screen_writing,
        "voting":   screen_voting,
        "results":  screen_results,
        "finished": screen_finished,
    }
    routing.get(game.get("status", "waiting"), screen_lobby)(game)

if __name__ == "__main__":
    main()