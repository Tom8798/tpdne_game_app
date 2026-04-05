import streamlit as st
import base64
import time
from firebase_config import init_firebase, get_game_ref
from game_logic import (
    fetch_random_face, generate_game_id,
    create_game_state, compute_round_winner
)

# ── Config page ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Punchline IA",
    page_icon="🎭",
    layout="centered"
)

# CSS personnalisé — remplace les rouges Streamlit par du bleu/neutre
st.markdown("""
<style>
    /* Boîtes d'info en bleu */
    .custom-info {
        background-color: #e8f0fe;
        border-left: 4px solid #4285f4;
        border-radius: 6px;
        padding: 12px 16px;
        margin: 8px 0;
        color: #1a1a2e;
    }
    /* Boîtes de succès en vert */
    .custom-success {
        background-color: #e6f4ea;
        border-left: 4px solid #34a853;
        border-radius: 6px;
        padding: 12px 16px;
        margin: 8px 0;
        color: #1a1a2e;
    }
    /* Boîtes neutres/warning en orange doux */
    .custom-wait {
        background-color: #fef7e0;
        border-left: 4px solid #fbbc04;
        border-radius: 6px;
        padding: 12px 16px;
        margin: 8px 0;
        color: #1a1a2e;
    }
    /* Carte punchline */
    .punchline-card {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 10px;
        padding: 16px 20px;
        margin: 8px 0;
    }
    /* Barre de progression custom */
    .progress-label {
        font-size: 0.85em;
        color: #5f6368;
        margin-bottom: 4px;
    }
</style>
""", unsafe_allow_html=True)

def info_box(text):
    st.markdown(f'<div class="custom-info">ℹ️ {text}</div>', unsafe_allow_html=True)

def success_box(text):
    st.markdown(f'<div class="custom-success">✅ {text}</div>', unsafe_allow_html=True)

def wait_box(text):
    st.markdown(f'<div class="custom-wait">⏳ {text}</div>', unsafe_allow_html=True)

# Initialise Firebase
init_firebase()

# ── Session locale ──────────────────────────────────────────────────────────
if "game_id" not in st.session_state:
    st.session_state.game_id = None
if "player_name" not in st.session_state:
    st.session_state.player_name = None
if "is_host" not in st.session_state:
    st.session_state.is_host = False

# ── Helpers ─────────────────────────────────────────────────────────────────

def get_game() -> dict:
    ref = get_game_ref(st.session_state.game_id)
    return ref.get() or {}

def update_game(data: dict):
    ref = get_game_ref(st.session_state.game_id)
    ref.update(data)

def safe_progress(done: int, total: int, label: str = ""):
    """Progress bar sans jamais dépasser 1.0."""
    ratio = min(done / max(total, 1), 1.0)
    if label:
        st.markdown(f'<div class="progress-label">{label}</div>', unsafe_allow_html=True)
    st.progress(ratio)

# ── ÉCRAN D'ACCUEIL ─────────────────────────────────────────────────────────

def screen_home():
    st.title("🎭 Punchline IA")
    st.caption("Attribuez un nom, un âge, un métier et une réplique aux visages générés par IA !")
    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🎲 Créer une partie")
        st.caption("Tu seras l'hôte. Les autres joueurs rejoignent ensuite avec le code.")
        player_name_host = st.text_input("Ton prénom", key="host_name", max_chars=20)
        num_rounds = st.slider("Nombre de tours", min_value=3, max_value=20, value=5)

        if st.button("Créer la partie", use_container_width=True, type="primary"):
            if not player_name_host.strip():
                st.error("Entre ton prénom !")
                return
            game_id = generate_game_id()
            game_state = create_game_state(player_name_host.strip(), num_rounds)
            get_game_ref(game_id).set(game_state)
            st.session_state.game_id = game_id
            st.session_state.player_name = player_name_host.strip()
            st.session_state.is_host = True
            st.rerun()

    with col2:
        st.subheader("🚪 Rejoindre une partie")
        st.caption("Entre le code donné par l'hôte et ton prénom.")
        game_id_input = st.text_input("Code de partie (6 caractères)", max_chars=6, key="join_code").upper().strip()
        player_name_join = st.text_input("Ton prénom", key="join_name", max_chars=20)

        if st.button("Rejoindre", use_container_width=True):
            if not game_id_input or not player_name_join.strip():
                st.error("Remplis tous les champs !")
                return

            game_ref = get_game_ref(game_id_input)
            game = game_ref.get()

            if not game:
                st.error("Partie introuvable. Vérifie le code.")
                return

            if game.get("status") != "waiting":
                st.error("Cette partie a déjà commencé, tu ne peux plus rejoindre.")
                return

            name = player_name_join.strip()
            existing_players = game.get("players", [])

            # Gestion des doublons de prénom
            if name in existing_players:
                st.error(f"Le prénom « {name} » est déjà pris dans cette partie. Choisis-en un autre.")
                return

            # Ajoute le joueur dynamiquement
            updated_players = existing_players + [name]
            updated_scores = game.get("scores", {})
            updated_scores[name] = 0
            game_ref.update({
                "players": updated_players,
                "scores": updated_scores
            })

            st.session_state.game_id = game_id_input
            st.session_state.player_name = name
            st.session_state.is_host = False
            st.rerun()

# ── LOBBY ────────────────────────────────────────────────────────────────────

def screen_lobby(game: dict):
    game_id = st.session_state.game_id
    players = game.get("players", [])

    st.title("🎭 Salle d'attente")
    st.markdown(f"### Code de la partie : `{game_id}`")
    info_box("Partage ce code avec tes amis. Ils peuvent rejoindre jusqu'au lancement.")

    st.subheader(f"Joueurs connectés ({len(players)})")
    for p in players:
        host_tag = " 👑 hôte" if p == game.get("host") else ""
        st.markdown(f"- **{p}**{host_tag}")

    st.caption(f"Nombre de tours : **{game.get('num_rounds', 5)}**")
    st.divider()

    if st.session_state.is_host:
        if len(players) < 2:
            wait_box("En attente d'au moins un autre joueur avant de pouvoir lancer...")
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
        # Rafraîchit pour voir les nouveaux joueurs arriver
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
            f"**{fiche.get('prenom')}**, {fiche.get('age')} ans, "
            f"*{fiche.get('metier')}* — « {fiche.get('punchline')} »"
        )

        count_done = len(punchlines)
        count_total = len(players)
        safe_progress(count_done, count_total,
                      f"{count_done}/{count_total} joueurs ont rempli leur fiche")

        if count_done >= count_total:
            # ✅ FIX : n'importe qui (pas seulement l'hôte) peut déclencher
            # le passage au vote dès que tout le monde a soumis.
            # Le premier à cliquer change le statut, les autres voient le rerun.
            if st.button("➡️ Tout le monde a joué — Passer au vote !",
                         use_container_width=True, type="primary"):
                current = get_game().get("status")
                if current == "writing":   # évite les double-clics
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
    st.caption("Quelle fiche t'a le plus fait rire ou convaincu ?")

    img_b64 = game.get("image_data")
    if img_b64:
        img_bytes = base64.b64decode(img_b64)
        st.image(img_bytes, width=400)

    st.divider()

    if player not in votes:
        st.subheader("Les fiches des joueurs :")

        # Mélange l'ordre pour ne pas avantager le premier
        import random
        items = list(punchlines.items())
        # Graine stable par tour pour que l'ordre soit identique pour tous
        random.seed(f"{st.session_state.game_id}_{current_round}")
        random.shuffle(items)

        for author, fiche in items:
            with st.container():
                st.markdown(f"""
<div class="punchline-card">
    <strong>🧑 {fiche.get('prenom', '?')}</strong>, {fiche.get('age', '?')} ans —
    <em>{fiche.get('metier', '?')}</em><br><br>
    💬 <em>« {fiche.get('punchline', '?')} »</em>
</div>
""", unsafe_allow_html=True)
                # On ne peut pas voter pour sa propre fiche
                if author != player:
                    if st.button(f"👍 Voter pour cette fiche", key=f"vote_{author}"):
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
            # ✅ FIX identique : tout joueur peut déclencher les résultats
            if st.button("📊 Voir les résultats du tour",
                         use_container_width=True, type="primary"):
                current_status = get_game().get("status")
                if current_status == "voting":
                    winner, vote_counts = compute_round_winner(punchlines, votes)
                    scores = game.get("scores", {p: 0 for p in players})
                    if winner:
                        scores[winner] = scores.get(winner, 0) + vote_counts[winner]
                    update_game({
                        "status": "results",
                        "round_winner": winner,
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
    winner = game.get("round_winner")
    players = game.get("players", [])

    st.title(f"🏆 Résultats — Tour {current_round}")

    img_b64 = game.get("image_data")
    if img_b64:
        img_bytes = base64.b64decode(img_b64)
        col_img, col_win = st.columns([1, 1])
        with col_img:
            st.image(img_bytes, width=280)
        with col_win:
            if winner and winner in punchlines:
                fiche = punchlines[winner]
                st.markdown(f"### 🥇 Vainqueur : **{winner}**")
                st.markdown(f"""
<div class="custom-success">
    <strong>{fiche.get('prenom')}</strong>, {fiche.get('age')} ans, <em>{fiche.get('metier')}</em><br><br>
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
        st.markdown(f"""
<div class="punchline-card">
    {medal} <strong>{author}</strong> — {nb_votes} vote(s)<br>
    <strong>{fiche.get('prenom')}</strong>, {fiche.get('age')} ans, <em>{fiche.get('metier')}</em><br>
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

    # ✅ FIX : tout joueur peut avancer, guard contre double-clic
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
        champion, pts = sorted_scores[0]
        st.markdown(f"## 🏆 Champion : **{champion}** avec **{pts} point(s)** !")

    st.subheader("Classement final")
    medals = ["🥇", "🥈", "🥉"]
    for rank, (p, s) in enumerate(sorted_scores):
        prefix = medals[rank] if rank < 3 else f"{rank+1}."
        st.markdown(f"{prefix} **{p}** — {s} pts")

    st.divider()
    if st.button("🔄 Nouvelle partie", use_container_width=True):
        st.session_state.game_id = None
        st.session_state.player_name = None
        st.session_state.is_host = False
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