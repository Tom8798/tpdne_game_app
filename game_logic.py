import requests
import time
import random
import string

# ── Génération d'image ──────────────────────────────────────────────────────

def fetch_random_face() -> bytes:
    """
    Récupère une image de visage IA depuis thispersondoesnotexist.com.
    Le site génère une nouvelle image à chaque requête grâce au cache-busting.
    """
    cache_bust = random.randint(1, 999999)
    url = f"https://thispersondoesnotexist.com/?v={cache_bust}"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://thispersondoesnotexist.com/"
    }
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    return response.content  # bytes JPEG

# ── Identifiants ────────────────────────────────────────────────────────────

def generate_game_id(length: int = 6) -> str:
    """Génère un code de partie court et lisible (ex: AZ48KP)."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

# ── Structure d'une partie ──────────────────────────────────────────────────

def create_game_state(host_name: str, num_rounds: int) -> dict:
    """
    L'hôte crée la partie. Les autres joueurs rejoignent ensuite librement.
    Plus besoin de saisir tous les prénoms en avance.
    """
    return {
        "status": "waiting",
        "current_round": 1,
        "num_rounds": num_rounds,
        "host": host_name,
        "players": [host_name],          # seul l'hôte au départ
        "scores": {host_name: 0},
        "current_image_url": None,
        "image_data": None,
        "punchlines": {},                # {"Alice": {"nom": ..., "age": ..., "metier": ..., "punchline": ...}}
        "votes": {},
        "round_winner": None,
        "created_at": time.time()
    }

def compute_round_winner(punchlines: dict, votes: dict) -> tuple:
    """
    Calcule le(s) vainqueur(s) d'une manche.
    En cas d'égalité, TOUS les ex-æquo reçoivent les points.
    Retourne (liste_vainqueurs, dict_votes_comptes)
    """
    if not punchlines:
        return [], {}

    vote_counts = {player: 0 for player in punchlines}
    for voter, voted_for in votes.items():
        if voted_for in vote_counts:
            vote_counts[voted_for] += 1

    if not vote_counts:
        return [], vote_counts

    max_votes = max(vote_counts.values())
    
    # Tous ceux qui ont le score maximum
    winners = [p for p, v in vote_counts.items() if v == max_votes]

    return winners, vote_counts