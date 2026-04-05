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

# ── CSS responsive mobile-first ───────────────────────────────────────────────
st.markdown("""
<style>
/* ── Reset & base ── */
* { box-sizing: border-box; }

/* ── Largeur max centrée ── */
.block-container {
    max-width: 520px !important;
    padding: 2rem 1rem 5rem 1rem !important;
}

/* Cache le header Streamlit (bandeau avec logo et menu) */
header[data-testid="stHeader"] {{
    display: none !important;
}}

/* Cache aussi le bouton "Deploy" et la toolbar */
.stToolbar {{
    display: none !important;
}}
[data-testid="stToolbar"] {{
    display: none !important;
}}

/* Compense l'espace que le header prenait */
.stApp > div:first-child {{
    padding-top: 0 !important;
}}

/* ── Hero accueil ── */
.hero {
    text-align: center;
    padding: 32px 0 24px 0;
}
.hero-emoji {
    font-size: 56px;
    line-height: 1;
    margin-bottom: 8px;
}
.hero-title {
    font-size: 2em;
    font-weight: 700;
    color: #1a1a2e;
    margin: 0 0 8px 0;
}
.hero-sub {
    font-size: 0.95em;
    color: #5f6368;
    line-height: 1.5;
    margin: 0;
}

/* ── Cards boutons accueil ── */
.menu-card {
    background: #ffffff;
    border: 1.5px solid #d2e3fc;
    border-radius: 16px;
    padding: 24px 20px 16px 20px;
    margin: 10px 0;
    text-align: center;
    transition: box-shadow 0.2s;
}
.menu-card:hover { box-shadow: 0 4px 18px rgba(66,133,244,0.13); }
.menu-card-emoji { font-size: 32px; margin-bottom: 6px; }
.menu-card-title {
    font-size: 1.15em;
    font-weight: 600;
    color: #1a1a2e;
    margin: 0 0 4px 0;
}
.menu-card-desc {
    font-size: 0.88em;
    color: #5f6368;
    margin: 0 0 16px 0;
}

/* ── Boutons ── */
div.stButton > button {
    border-radius: 12px !important;
    font-weight: 600 !important;
    font-size: 1em !important;
    padding: 12px 0 !important;
    width: 100%;
    transition: all 0.2s !important;
}
div.stButton > button[kind="primary"] {
    background: #4285f4 !important;
    border-color: #4285f4 !important;
    color: white !important;
}
div.stButton > button[kind="primary"]:hover {
    background: #3367d6 !important;
    border-color: #3367d6 !important;
}
div.stButton > button:not([kind="primary"]) {
    border-color: #4285f4 !important;
    color: #4285f4 !important;
    background: white !important;
}

/* ── Inputs ── */
div.stTextInput > div > div > input,
div.stTextArea > div > div > textarea,
div.stNumberInput > div > div > input {
    border-radius: 10px !important;
    font-size: 1em !important;
    padding: 10px 14px !important;
}

/* ── Code de partie (gros et lisible) ── */
.game-code {
    background: #e8f0fe;
    border-radius: 14px;
    padding: 18px;
    text-align: center;
    margin: 12px 0;
}
.game-code-label {
    font-size: 0.82em;
    color: #4285f4;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-weight: 600;
    margin-bottom: 4px;
}
.game-code-value {
    font-size: 2.6em;
    font-weight: 800;
    color: #1a1a2e;
    letter-spacing: 0.18em;
    line-height: 1;
}

/* ── Boîtes de statut ── */
.box-info {
    background: #e8f0fe;
    border-left: 4px solid #4285f4;
    border-radius: 8px;
    padding: 12px 14px;
    margin: 8px 0;
    font-size: 0.93em;
    color: #1a1a2e;
}
.box-success {
    background: #e6f4ea;
    border-left: 4px solid #34a853;
    border-radius: 8px;
    padding: 12px 14px;
    margin: 8px 0;
    font-size: 0.93em;
    color: #1a1a2e;
}
.box-wait {
    background: #e8f0fe;
    border-left: 4px solid #4285f4;
    border-radius: 8px;
    padding: 12px 14px;
    margin: 8px 0;
    font-size: 0.93em;
    color: #1a1a2e;
}

/* ── Carte joueur lobby ── */
.player-chip {
    display: inline-block;
    background: #f1f3f4;
    border-radius: 20px;
    padding: 6px 14px;
    margin: 4px 4px 4px 0;
    font-size: 0.93em;
    color: #1a1a2e;
    font-weight: 500;
}

/* ── Image IA ── */
.img-wrapper {
    border-radius: 16px;
    overflow: hidden;
    margin: 12px 0;
    box-shadow: 0 4px 20px rgba(0,0,0,0.12);
}
.img-wrapper img { width: 100%; display: block; }

/* ── Carte punchline ── */
.punchline-card {
    background: #ffffff;
    border: 1.5px solid #e0e0e0;
    border-radius: 14px;
    padding: 16px 18px;
    margin: 10px 0;
}
.punchline-card-winner {
    background: #e6f4ea;
    border: 1.5px solid #34a853;
    border-radius: 14px;
    padding: 16px 18px;
    margin: 10px 0;
}
.punchline-identity {
    font-size: 1em;
    font-weight: 600;
    color: #1a1a2e;
    margin-bottom: 4px;
}
.punchline-job {
    font-size: 0.88em;
    color: #5f6368;
    margin-bottom: 10px;
}
.punchline-text {
    font-size: 1.05em;
    font-style: italic;
    color: #1a1a2e;
    border-left: 3px solid #4285f4;
    padding-left: 10px;
    margin: 0;
}

/* ── Barre de progression ── */
.prog-label {
    font-size: 0.82em;
    color: #5f6368;
    margin-bottom: 4px;
    text-align: right;
}

/* ── Score tableau ── */
.score-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 14px;
    border-radius: 10px;
    margin: 5px 0;
    background: #f8f9fa;
    font-size: 0.97em;
}
.score-row-top {
    background: #e8f0fe;
    font-weight: 700;
}
.score-pts {
    font-weight: 700;
    color: #4285f4;
}

/* ── Tour badge ── */
.round-badge {
    display: inline-block;
    background: #4285f4;
    color: white;
    border-radius: 20px;
    padding: 3px 14px;
    font-size: 0.82em;
    font-weight: 600;
    margin-bottom: 8px;
}

/* ── Footer ── */
.footer {
    text-align: center;
    color: #9aa0a6;
    font-size: 0.78em;
    margin-top: 32px;
    padding-top: 12px;
    border-top: 1px solid #f1f3f4;
}

/* ── Bouton retour ── */
.back-btn { margin-bottom: 8px; }
</style>
""", unsafe_allow_html=True)

# ── Helpers UI ────────────────────────────────────────────────────────────────

def info_box(text):
    st.markdown(f'<div class="box-info">ℹ️ {text}</div>', unsafe_allow_html=True)

def success_box(text):
    st.markdown(f'<div class="box-success">✅ {text}</div>', unsafe_allow_html=True)

def wait_box(text):
    st.markdown(f'<div class="box-wait">⏳ {text}</div>', unsafe_allow_html=True)

def safe_progress(done: int, total: int, label: str = ""):
    ratio = min(done / max(total, 1), 1.0)
    if label:
        st.markdown(f'<div class="prog-label">{label}</div>', unsafe_allow_html=True)
    st.progress(ratio)

def round_badge(current, total):
    st.markdown(
        f'<div class="round-badge">Tour {current} / {total}</div>',
        unsafe_allow_html=True
    )

def show_image(img_b64: str):
    """Affiche l'image IA avec style mobile."""
    if img_b64:
        img_bytes = base64.b64decode(img_b64)
        b64_str = base64.b64encode(img_bytes).decode()
        st.markdown(
            f'<div class="img-wrapper">'
            f'<img src="data:image/jpeg;base64,{b64_str}"/>'
            f'</div>',
            unsafe_allow_html=True
        )

def punchline_card(fiche: dict, author: str,
                   nb_votes: int = None, winner: bool = False,
                   medal: str = ""):
    css = "punchline-card-winner" if winner else "punchline-card"
    votes_str = f" — <strong>{nb_votes} vote(s)</strong>" if nb_votes is not None else ""
    st.markdown(f"""
<div class="{css}">
    <div class="punchline-identity">
        {medal} {fiche.get('prenom', '?')}, {fiche.get('age', '?')} ans
        {votes_str}
    </div>
    <div class="punchline-job">💼 {fiche.get('metier', '?')} · par <em>{author}</em></div>
    <p class="punchline-text">« {fiche.get('punchline', '?')} »</p>
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
        winner_tag = " 🏆" if highlight_winners and p in highlight_winners else ""
        st.markdown(f"""
<div class="{css}">
    <span>{medal} {p}{winner_tag}</span>
    <span class="score-pts">{s} pts</span>
</div>
""", unsafe_allow_html=True)

# ── Firebase ──────────────────────────────────────────────────────────────────

init_firebase()

for key, default in [
    ("game_id", None),
    ("player_name", None),
    ("is_host", False),
    ("home_view", "menu"),
]:
    if key not in st.session_state:
        st.session_state[key] = default

def get_game() -> dict:
    return get_game_ref(st.session_state.game_id).get() or {}

def update_game(data: dict):
    get_game_ref(st.session_state.game_id).update(data)

# ── ACCUEIL ───────────────────────────────────────────────────────────────────

def screen_home():
    view = st.session_state.home_view

    if view == "menu":
        st.markdown("""
<div class="hero">
    <div class="hero-emoji">🎭</div>
    <h1 class="hero-title">Punchline IA</h1>
    <p class="hero-sub">Inventez l'identité et la réplique<br>
    de visages générés par intelligence artificielle.<br>
    Le plus drôle remporte la manche !</p>
</div>
""", unsafe_allow_html=True)

        st.markdown("""
<div class="menu-card">
    <div class="menu-card-emoji">🎲</div>
    <p class="menu-card-title">Nouvelle partie</p>
    <p class="menu-card-desc">Crée une partie et partage le code à tes amis.</p>
</div>
""", unsafe_allow_html=True)
        if st.button("Créer une partie", use_container_width=True, type="primary"):
            st.session_state.home_view = "create"
            st.rerun()

        st.markdown("""
<div class="menu-card">
    <div class="menu-card-emoji">🚪</div>
    <p class="menu-card-title">Rejoindre une partie</p>
    <p class="menu-card-desc">Entre le code donné par l'hôte.</p>
</div>
""", unsafe_allow_html=True)
        if st.button("Rejoindre une partie", use_container_width=True):
            st.session_state.home_view = "join"
            st.rerun()

        st.markdown("""
<div class="footer">
    Images · <a href="https://thispersondoesnotexist.com" 
    style="color:#4285f4;">thispersondoesnotexist.com</a>
</div>
""", unsafe_allow_html=True)

    elif view == "create":
        st.markdown('<div class="back-btn">', unsafe_allow_html=True)
        if st.button("← Retour"):
            st.session_state.home_view = "menu"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("## 🎲 Créer une partie")
        info_box("Tu seras l'hôte. Tes amis rejoindront avec le code affiché dans le lobby.")

        name = st.text_input("Ton prénom", max_chars=20, key="host_name",
                             placeholder="Ex : Sophie")
        num_rounds = st.slider("Nombre de tours", min_value=3, max_value=20, value=5)

        if st.button("🚀 Créer la partie", use_container_width=True, type="primary"):
            if not name.strip():
                st.error("Entre ton prénom !")
                return
            game_id = generate_game_id()
            get_game_ref(game_id).set(create_game_state(name.strip(), num_rounds))
            st.session_state.game_id = game_id
            st.session_state.player_name = name.strip()
            st.session_state.is_host = True
            st.session_state.home_view = "menu"
            st.rerun()

    elif view == "join":
        st.markdown('<div class="back-btn">', unsafe_allow_html=True)
        if st.button("← Retour"):
            st.session_state.home_view = "menu"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("## 🚪 Rejoindre une partie")
        info_box("Demande le code 6 caractères à l'hôte.")

        code = st.text_input("Code de partie", max_chars=6,
                             placeholder="Ex : AZ48KP", key="join_code").upper().strip()
        name = st.text_input("Ton prénom", max_chars=20,
                             placeholder="Ex : Lucas", key="join_name")

        if st.button("✅ Rejoindre", use_container_width=True, type="primary"):
            if not code or not name.strip():
                st.error("Remplis tous les champs !")
                return
            game_ref = get_game_ref(code)
            game = game_ref.get()
            if not game:
                st.error("Partie introuvable. Vérifie le code.")
                return
            if game.get("status") != "waiting":
                st.error("Cette partie a déjà commencé.")
                return
            n = name.strip()
            if n in game.get("players", []):
                st.error(f"Le prénom « {n} » est déjà pris.")
                return
            updated_players = game.get("players", []) + [n]
            updated_scores = game.get("scores", {})
            updated_scores[n] = 0
            game_ref.update({"players": updated_players, "scores": updated_scores})
            st.session_state.game_id = code
            st.session_state.player_name = n
            st.session_state.is_host = False
            st.session_state.home_view = "menu"
            st.rerun()

# ── LOBBY ─────────────────────────────────────────────────────────────────────

def screen_lobby(game: dict):
    players = game.get("players", [])
    game_id = st.session_state.game_id

    st.markdown("## 🎭 Salle d'attente")

    # Code en grand, facile à lire et recopier sur mobile
    st.markdown(f"""
<div class="game-code">
    <div class="game-code-label">Code de la partie</div>
    <div class="game-code-value">{game_id}</div>
</div>
""", unsafe_allow_html=True)

    info_box("Partage ce code. Tes amis peuvent rejoindre jusqu'au lancement.")

    st.markdown(f"**Joueurs connectés ({len(players)})**")
    chips = "".join(
        f'<span class="player-chip">{"👑 " if p == game.get("host") else ""}{p}</span>'
        for p in players
    )
    st.markdown(f'<div style="margin:8px 0 16px 0">{chips}</div>', unsafe_allow_html=True)
    st.caption(f"Nombre de tours : **{game.get('num_rounds', 5)}**")

    if st.session_state.is_host:
        if len(players) < 2:
            wait_box("En attente d'au moins un autre joueur...")
        else:
            if st.button("🚀 Lancer la partie !", use_container_width=True, type="primary"):
                with st.spinner("Chargement du premier visage IA..."):
                    try:
                        img_b64 = base64.b64encode(fetch_random_face()).decode()
                        update_game({
                            "status": "writing",
                            "image_data": img_b64,
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

# ── PHASE ÉCRITURE ────────────────────────────────────────────────────────────

def screen_writing(game: dict):
    player = st.session_state.player_name
    current_round = game.get("current_round", 1)
    num_rounds = game.get("num_rounds", 5)
    punchlines = game.get("punchlines", {}) or {}
    players = game.get("players", [])

    round_badge(current_round, num_rounds)
    st.markdown("## ✍️ Qui est cette personne ?")

    show_image(game.get("image_data"))

    if player not in punchlines:
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            prenom = st.text_input("Prénom", max_chars=30,
                                   key=f"prenom_{current_round}",
                                   placeholder="Jean-Michel")
        with col2:
            age = st.number_input("Âge", min_value=1, max_value=120,
                                  value=35, key=f"age_{current_round}")

        metier = st.text_input("Métier", max_chars=50,
                               key=f"metier_{current_round}",
                               placeholder="Vendeur de matelas")

        punchline = st.text_area("💬 Sa réplique signature",
                                 max_chars=200, height=90,
                                 key=f"punchline_{current_round}",
                                 placeholder="« Non mais tu me prends pour qui là ? »")

        if st.button("✅ Valider ma fiche", use_container_width=True, type="primary"):
            if not prenom.strip() or not metier.strip() or not punchline.strip():
                st.error("Remplis tous les champs !")
            else:
                get_game_ref(st.session_state.game_id).child("punchlines").child(player).set({
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
            f"<em>{fiche['metier']}</em> — « {fiche['punchline']} »"
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
    player = st.session_state.player_name
    current_round = game.get("current_round", 1)
    num_rounds = game.get("num_rounds", 5)
    punchlines = game.get("punchlines", {}) or {}
    votes = game.get("votes", {}) or {}
    players = game.get("players", [])

    round_badge(current_round, num_rounds)
    st.markdown("## 🗳️ Vote pour ta fiche préférée !")

    show_image(game.get("image_data"))

    if player not in votes:
        st.markdown("---")
        items = list(punchlines.items())
        random.seed(f"{st.session_state.game_id}_{current_round}")
        random.shuffle(items)

        for author, fiche in items:
            punchline_card(fiche, author)
            if author != player:
                if st.button("👍 Voter pour cette fiche",
                             key=f"vote_{author}",
                             use_container_width=True):
                    get_game_ref(st.session_state.game_id)\
                        .child("votes").child(player).set(author)
                    st.rerun()
            else:
                st.caption("_(c'est ta fiche — tu ne peux pas voter pour toi-même)_")
            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
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
            wait_box(f"En attente des autres votes... ({count_voted}/{count_total})")
            time.sleep(3)
            st.rerun()

# ── RÉSULTATS ─────────────────────────────────────────────────────────────────

def screen_results(game: dict):
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
    st.markdown("## 🏆 Résultats du tour")

    show_image(game.get("image_data"))

    # Annonce vainqueur(s)
    if winners:
        if len(winners) == 1:
            success_box(f"🥇 Vainqueur : <strong>{winners[0]}</strong> !")
        else:
            noms = " & ".join(f"<strong>{w}</strong>" for w in winners)
            success_box(f"🤝 Égalité ! {noms} — points partagés !")

    # Toutes les fiches classées
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

    # Tableau des scores
    st.markdown("---")
    st.markdown("**🎯 Scores cumulés**")
    score_table(scores)

    st.markdown("---")
    if current_round >= num_rounds:
        if st.button("🎉 Voir le classement final !",
                     use_container_width=True, type="primary"):
            if get_game().get("status") == "results":
                update_game({"status": "finished"})
            st.rerun()
    else:
        if st.button(f"➡️ Tour {current_round + 1}",
                     use_container_width=True, type="primary"):
            if get_game().get("status") == "results":
                with st.spinner("Chargement du prochain visage..."):
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

# ── FIN DE PARTIE ─────────────────────────────────────────────────────────────

def screen_finished(game: dict):
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
        st.markdown(f"### 🤝 Égalité parfaite ! {noms} — {max_pts} pts chacun !")

    st.markdown("---")
    st.markdown("**Classement final**")
    score_table(scores, highlight_winners=champions)

    st.markdown("---")
    if st.button("🔄 Nouvelle partie", use_container_width=True, type="primary"):
        for key in ["game_id", "player_name", "is_host"]:
            st.session_state[key] = None if key != "is_host" else False
        st.session_state.home_view = "menu"
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