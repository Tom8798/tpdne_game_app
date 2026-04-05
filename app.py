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

st.markdown("""
<style>
    /* ── Boîtes custom ── */
    .custom-info {
        background-color: #e8f0fe;
        border-left: 4px solid #4285f4;
        border-radius: 6px;
        padding: 12px 16px;
        margin: 8px 0;
        color: #1a1a2e;
    }
    .custom-success {
        background-color: #e6f4ea;
        border-left: 4px solid #34a853;
        border-radius: 6px;
        padding: 12px 16px;
        margin: 8px 0;
        color: #1a1a2e;
    }
    .custom-wait {
        background-color: #e8f0fe;
        border-left: 4px solid #4285f4;
        border-radius: 6px;
        padding: 12px 16px;
        margin: 8px 0;
        color: #1a1a2e;
    }
    .punchline-card {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 10px;
        padding: 16px 20px;
        margin: 8px 0;
    }
    .progress-label {
        font-size: 0.85em;
        color: #5f6368;
        margin-bottom: 4px;
    }

    /* ── Page d'accueil ── */
    .home-hero {
        text-align: center;
        padding: 40px 0 20px 0;
    }
    .home-hero h1 {
        font-size: 3em;
        margin-bottom: 0;
    }
    .home-hero p {
        font-size: 1.15em;
        color: #5f6368;
        margin-top: 8px;
    }
    .home-card {
        background: #ffffff;
        border: 1.5px solid #d2e3fc;
        border-radius: 16px;
        padding: 32px 28px;
        margin: 12px 0;
        box-shadow: 0 2px 12px rgba(66,133,244,0.07);
        text-align: center;
    }
    .home-card h2 {
        font-size: 1.4em;
        margin-bottom: 6px;
        color: #1a1a2e;
    }
    .home-card p {
        color: #5f6368;
        font-size: 0.95em;
        margin-bottom: 20px;
    }

    /* ── Boutons principaux en bleu ── */
    div.stButton > button[kind="primary"] {
        background-color: #4285f4 !important;
        border-color: #4285f4 !important;
        color: white !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 10px 0 !important;
        transition: background 0.2s;
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: #3367d6 !important;
        border-color: #3367d6 !important;
    }
    /* Boutons secondaires (sans type="primary") aussi en bleu doux */
    div.stButton > button:not([kind="primary"]) {
        border-color: #4285f4 !important;
        color: #4285f4 !important;
        border-radius: 8px !important;
    }
</style>
""", unsafe_allow_html=True)

# ── Helpers UI ───────────────────────────────────────────────────────────────

def info_box(text):
    st.markdown(f'<div class="custom-info">ℹ️ {text}</div>', unsafe_allow_html=True)

def success_box(text):
    st.markdown(f'<div class="custom-success">✅ {text}</div>', unsafe_allow_html=True)

def wait_box(text):
    st.markdown(f'<div class="custom-wait">⏳ {text}</div>', unsafe_allow_html=True)

def safe_progress(done: int, total: int, label: str = ""):
    ratio = min(done / max(total, 1), 1.0)
    if label:
        st.markdown(f'<div class="progress-label">{label}</div>', unsafe_allow_html=True)
    st.progress(ratio)

# ── Firebase ─────────────────────────────────────────────────────────────────

init_firebase()

if "game_id" not in st.session_state:
    st.session_state.game_id = None
if "player_name" not in st.session_state:
    st.session_state.player_name = None
if "is_host" not in st.session_state:
    st.session_state.is_host = False
if "home_view" not in st.session_state:
    # "menu" | "create" | "join"
    st.session_state.home_view = "menu"

def get_game() -> dict:
    ref = get_game_ref(st.session_state.game_id)
    return ref.get() or {}

def update_game(data: dict):
    ref = get_game_ref(st.session_state.game_id)
    ref.update(data)

# ── ÉCRAN D'ACCUEIL ───────────────────────────────────────────────────────────

def screen_home():
    # Hero
    st.markdown("""
    <div class="home-hero">
        <h1>🎭 Punchline IA</h1>
        <p>Inventez l'identité et la réplique des visages générés par IA.<br>
        Le plus drôle remporte la manche !</p>
    </div>
    """, unsafe_allow_html=True)

    view = st.session_state.home_view

    # ── Menu principal ────────────────────────────────────────────────────────
    if view == "menu":
        col1, col2 = st.columns(2, gap="large")

        with col1:
            st.markdown("""
            <div class="home-card">
                <h2>🎲 Nouvelle partie</h2>
                <p>Crée une partie et invite tes amis avec un code.</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Créer une partie", use_container_width=True, type="primary"):
                st.session_state.home_view = "create"
                st.rerun()

        with col2:
            st.markdown("""
            <div class="home-card">
                <h2>🚪 Rejoindre</h2>
                <p>Entre le code donné par l'hôte pour rejoindre la partie.</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Rejoindre une partie", use_container_width=True, type="primary"):
                st.session_state.home_view = "join"
                st.rerun()

        st.markdown("---")
        st.markdown("""
        <div style="text-align:center; color:#9aa0a6; font-size:0.85em;">
            🖼️ Images générées par <a href="https://thispersondoesnotexist.com" 
            target="_blank" style="color:#4285f4;">thispersondoesnotexist.com</a>
        </div>
        """, unsafe_allow_html=True)

    # ── Formulaire Créer ──────────────────────────────────────────────────────
    elif view == "create":
        if st.button("← Retour", key="back_create"):
            st.session_state.home_view = "menu"
            st.rerun()

        st.markdown("## 🎲 Créer une partie")
        info_box("Tu seras l'hôte. Tes amis rejoindront avec le code affiché dans le lobby.")

        player_name = st.text_input("Ton prénom", max_chars=20, key="host_name")
        num_rounds = st.slider("Nombre de tours", min_value=3, max_value=20, value=5)

        st.markdown("---")
        if st.button("🚀 Créer la partie", use_container_width=True, type="primary"):
            if not player_name.strip():
                st.error("Entre ton prénom !")
                return
            game_id = generate_game_id()
            game_state = create_game_state(player_name.strip(), num_rounds)
            get_game_ref(game_id).set(game_state)
            st.session_state.game_id = game_id
            st.session_state.player_name = player_name.strip()
            st.session_state.is_host = True
            st.session_state.home_view = "menu"
            st.rerun()

    # ── Formulaire Rejoindre ──────────────────────────────────────────────────
    elif view == "join":
        if st.button("← Retour", key="back_join"):
            st.session_state.home_view = "menu"
            st.rerun()

        st.markdown("## 🚪 Rejoindre une partie")
        info_box("Demande le code à 6 caractères à l'hôte de la partie.")

        game_id_input = st.text_input(
            "Code de partie", max_chars=6, key="join_code",
            placeholder="Ex : AZ48KP"
        ).upper().strip()
        player_name = st.text_input("Ton prénom", max_chars=20, key="join_name")

        st.markdown("---")
        if st.button("✅ Rejoindre", use_container_width=True, type="primary"):
            if not game_id_input or not player_name.strip():
                st.error("Remplis tous les champs !")
                return

            game_ref = get_game_ref(game_id_input)
            game = game_ref.get()

            if not game:
                st.error("Partie introuvable. Vérifie le code.")
                return
            if game.get("status") != "waiting":
                st.error("Cette partie a déjà commencé.")
                return

            name = player_name.strip()
            existing = game.get("players", [])
            if name in existing:
                st.error(f"Le prénom « {name} » est déjà pris. Choisis-en un autre.")
                return

            updated_players = existing + [name]
            updated_scores = game.get("scores", {})
            updated_scores[name] = 0
            game_ref.update({"players": updated_players, "scores": updated_scores})

            st.session_state.game_id = game_id_input
            st.session_state.player_name = name
            st.session_state.is_host = False
            st.session_state.home_view = "menu"
            st.rerun()

# ── LOBBY ─────────────────────────────────────────────────────────────────────

def screen_lobby(game: dict):
    game_id = st.session_state.game_id
    players = game.get("players", [])

    st.title("🎭 Salle d'attente")
    st.markdown(f"### Code de la partie : `{game_id}`")
    info_box("Partage ce code avec tes amis. Ils peuvent rejoindre jusqu'au lancement.")

    st.subheader(f"Joueurs connectés ({len(players)})")
    for p in players:
        host_tag = " 👑" if p == game.get("host") else ""
        st.markdown(f"- **{p}**{host_tag}")

    st.caption(f"Nombre de tours : **{game.get('num_rounds', 5)}**")
    st.divider()

    if st.session_state.is_host:
        if len(players) < 2:
            wait_box("En attente d'au moins un autre joueur...")
        else:
            if st.button("🚀 Lancer la partie !", use_container_width=True, type="primary"):
                with st.spinner("Chargement du premier visage IA..."):
                    try:
                        img_bytes = fetch_random_face()
                        img_b64 = base64.b64encode(img_bytes).decode()
                        update_game({
                            "status": "writing",
                            "image_data": img_b64,
                            "punchlines": {},
                            "votes": {},
                            "round_winner": None
                        })
                    except Exception as e:
                        st.error(f"Erreur chargement image : {e}")
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

    st.title(f"✍️ Tour {current_round} / {num_rounds}")
    st.caption("Regardez ce visage et inventez son identité + sa réplique !")

    img_b64 = game.get("image_data")
    if img_b64:
        img_bytes = base64.b64decode(img_b64)
        st.image(img_bytes, width=400)

    st.divider()

    if player not in punchlines:
        st.subheader("Qui est cette personne selon toi ?")

        col1, col2 = st.columns(2)
        with col1:
            prenom = st.text_input("Prénom", max_chars=30, key=f"prenom_{current_round}",
                                   placeholder="Ex: Jean-Michel")
            age = st.number_input("Âge", min_value=1, max_value=120,
                                  value=35, key=f"age_{current_round}")
        with col2:
            metier = st.text_input("Métier", max_chars=50, key=f"metier_{current_round}",
                                   placeholder="Ex: Vendeur de matelas")

        punchline = st.text_area(
            "Sa réplique signature 💬",
            max_chars=200, height=80,
            key=f"punchline_{current_round}",
            placeholder="Ex: « Non mais tu me prends pour qui là ? »"
        )

        if st.button("✅ Valider ma fiche", use_container_width=True, type="primary"):
            if not prenom.strip() or not metier.strip() or not punchline.strip():
                st.error("Remplis tous les champs !")
            else:
                fiche = {
                    "prenom": prenom.strip(),
                    "age": int(age),
                    "metier": metier.strip(),
                    "punchline": punchline.strip()
                }
                ref = get_game_ref(st.session_state.game_id)
                ref.child("punchlines").child(player).set(fiche)
                st.rerun()
    else:
        fiche = punchlines[player]
        success_box(
            f"Fiche enregistrée — "
            f"<strong>{fiche.get('prenom')}</strong>, {fiche.get('age')} ans, "
            f"<em>{fiche.get('metier')}</em> — « {fiche.get('punchline')} »"
        )

        count_done = len(punchlines)
        count_total = len(players)
        safe_progress(count_done, count_total,
                      f"{count_done}/{count_total} joueurs ont rempli leur fiche")

        if count_done >= count_total:
            if st.button("➡️ Passer au vote !",
                         use_container_width=True, type="primary"):
                if get_game().get("status") == "writing":
                    update_game({"status": "voting"})
                st.rerun()
        else:
            wait_box(f"En attente des autres joueurs... ({count_done}/{count_total})")
            time.sleep(3)
            st.rerun()

# ── PHASE VOTE ────────────────────────────────────────────────────────────────

def screen_voting(game: dict):
    player = st.session_state.player_name
    current_round = game.get("current_round", 1)
    num_rounds = game.get("num_rounds", 5)
    punchlines = game.get("punchlines", {}) or {}
    votes = game.get("votes", {}) or {}
    players = game.get("players", [])

    st.title(f"🗳️ Tour {current_round} / {num_rounds} — Vote !")
    st.caption("Quelle fiche t'a le plus convaincu ou fait rire ?")

    img_b64 = game.get("image_data")
    if img_b64:
        img_bytes = base64.b64decode(img_b64)
        st.image(img_bytes, width=400)

    st.divider()

    if player not in votes:
        st.subheader("Les fiches des joueurs :")

        import random
        items = list(punchlines.items())
        random.seed(f"{st.session_state.game_id}_{current_round}")
        random.shuffle(items)

        for author, fiche in items:
            st.markdown(f"""
<div class="punchline-card">
    <strong>🧑 {fiche.get('prenom', '?')}</strong>, {fiche.get('age', '?')} ans —
    <em>{fiche.get('metier', '?')}</em><br><br>
    💬 <em>« {fiche.get('punchline', '?')} »</em>
</div>
""", unsafe_allow_html=True)
            if author != player:
                if st.button("👍 Voter pour cette fiche", key=f"vote_{author}"):
                    ref = get_game_ref(st.session_state.game_id)
                    ref.child("votes").child(player).set(author)
                    st.rerun()
            else:
                st.caption("_(c'est ta fiche)_")
            st.divider()

    else:
        success_box("Tu as voté !")

        count_voted = len(votes)
        count_total = len(players)
        safe_progress(count_voted, count_total,
                      f"{count_voted}/{count_total} joueurs ont voté")

        if count_voted >= count_total:
            if st.button("📊 Voir les résultats du tour",
                         use_container_width=True, type="primary"):
                if get_game().get("status") == "voting":
                    winners, vote_counts = compute_round_winner(punchlines, votes)
                    scores = game.get("scores", {p: 0 for p in players})
                    if winners:
                        points_du_tour = max(vote_counts.values())
                        for w in winners:
                            scores[w] = scores.get(w, 0) + points_du_tour
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

# ── PHASE RÉSULTATS ───────────────────────────────────────────────────────────

def screen_results(game: dict):
    current_round = game.get("current_round", 1)
    num_rounds = game.get("num_rounds", 5)
    punchlines = game.get("punchlines", {}) or {}
    votes = game.get("votes", {}) or {}
    scores = game.get("scores", {}) or {}
    winners = game.get("round_winner") or []
    players = game.get("players", [])

    # Compatibilité si round_winner est encore une string (ancienne partie)
    if isinstance(winners, str):
        winners = [winners]

    st.title(f"🏆 Résultats — Tour {current_round}")

    img_b64 = game.get("image_data")
    if img_b64:
        img_bytes = base64.b64decode(img_b64)
        col_img, col_win = st.columns([1, 1])
        with col_img:
            st.image(img_bytes, width=280)
        with col_win:
            if winners:
                if len(winners) == 1:
                    w = winners[0]
                    fiche = punchlines.get(w, {})
                    st.markdown(f"### 🥇 Vainqueur : **{w}**")
                    st.markdown(f"""
<div class="custom-success">
    <strong>{fiche.get('prenom')}</strong>, {fiche.get('age')} ans,
    <em>{fiche.get('metier')}</em><br><br>
    💬 <em>« {fiche.get('punchline')} »</em>
</div>
""", unsafe_allow_html=True)
                else:
                    # Égalité
                    noms = " & ".join(f"**{w}**" for w in winners)
                    st.markdown(f"### 🤝 Égalité ! {noms}")
                    for w in winners:
                        fiche = punchlines.get(w, {})
                        st.markdown(f"""
<div class="custom-success">
    <em>{w}</em> — <strong>{fiche.get('prenom')}</strong>,
    {fiche.get('age')} ans, <em>{fiche.get('metier')}</em><br>
    💬 <em>« {fiche.get('punchline')} »</em>
</div>
""", unsafe_allow_html=True)

    st.subheader("Toutes les fiches du tour")
    _, vote_counts = compute_round_winner(punchlines, votes)
    sorted_fiches = sorted(punchlines.items(),
                           key=lambda x: vote_counts.get(x[0], 0), reverse=True)
    medals = ["🥇", "🥈", "🥉"]

    for rank, (author, fiche) in enumerate(sorted_fiches):
        nb_votes = vote_counts.get(author, 0)
        medal = medals[rank] if rank < 3 else f"{rank+1}."
        is_winner = author in winners
        card_style = "custom-success" if is_winner else "punchline-card"
        st.markdown(f"""
<div class="{card_style}">
    {medal} <strong>{author}</strong> — {nb_votes} vote(s)<br>
    <strong>{fiche.get('prenom')}</strong>, {fiche.get('age')} ans,
    <em>{fiche.get('metier')}</em><br>
    💬 <em>« {fiche.get('punchline')} »</em>
</div>
""", unsafe_allow_html=True)

    st.divider()
    st.subheader("🎯 Scores cumulés")
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    for rank, (p, s) in enumerate(sorted_scores):
        prefix = medals[rank] if rank < 3 else f"{rank+1}."
        st.markdown(f"{prefix} **{p}** — {s} pts")

    st.divider()

    if current_round >= num_rounds:
        if st.button("🎉 Voir le classement final !",
                     use_container_width=True, type="primary"):
            if get_game().get("status") == "results":
                update_game({"status": "finished"})
            st.rerun()
    else:
        if st.button(f"➡️ Lancer le tour {current_round + 1}",
                     use_container_width=True, type="primary"):
            if get_game().get("status") == "results":
                with st.spinner("Chargement du prochain visage..."):
                    try:
                        img_bytes = fetch_random_face()
                        img_b64 = base64.b64encode(img_bytes).decode()
                        update_game({
                            "status": "writing",
                            "current_round": current_round + 1,
                            "image_data": img_b64,
                            "punchlines": {},
                            "votes": {},
                            "round_winner": None
                        })
                    except Exception as e:
                        st.error(f"Erreur chargement image : {e}")
            st.rerun()

# ── ÉCRAN FINAL ───────────────────────────────────────────────────────────────

def screen_finished(game: dict):
    scores = game.get("scores", {}) or {}
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    st.balloons()
    st.title("🎉 Fin de partie !")

    if sorted_scores:
        max_pts = sorted_scores[0][1]
        champions = [p for p, s in sorted_scores if s == max_pts]
        medals = ["🥇", "🥈", "🥉"]

        if len(champions) == 1:
            st.markdown(f"## 🏆 Champion : **{champions[0]}** avec **{max_pts} pt(s)** !")
        else:
            noms = " & ".join(f"**{c}**" for c in champions)
            st.markdown(f"## 🤝 Égalité parfaite ! {noms} — **{max_pts} pt(s)** chacun !")

    st.subheader("Classement final")
    medals = ["🥇", "🥈", "🥉"]
    for rank, (p, s) in enumerate(sorted_scores):
        prefix = medals[rank] if rank < 3 else f"{rank+1}."
        st.markdown(f"{prefix} **{p}** — {s} pts")

    st.divider()
    if st.button("🔄 Nouvelle partie", use_container_width=True, type="primary"):
        st.session_state.game_id = None
        st.session_state.player_name = None
        st.session_state.is_host = False
        st.session_state.home_view = "menu"
        st.rerun()

# ── ROUTEUR ───────────────────────────────────────────────────────────────────

def main():
    if not st.session_state.game_id:
        screen_home()
        return

    game = get_game()
    status = game.get("status", "waiting")

    routing = {
        "waiting":  screen_lobby,
        "writing":  screen_writing,
        "voting":   screen_voting,
        "results":  screen_results,
        "finished": screen_finished,
    }

    screen_fn = routing.get(status, screen_lobby)
    screen_fn(game)

if __name__ == "__main__":
    main()