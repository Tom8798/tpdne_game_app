import firebase_admin
from firebase_admin import credentials, db
import streamlit as st
import json

def init_firebase():
    """Initialise Firebase une seule fois par session Streamlit."""
    if not firebase_admin._apps:
        # Les secrets sont dans .streamlit/secrets.toml
        cred_dict = dict(st.secrets["firebase_credentials"])
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred, {
            'databaseURL': st.secrets["firebase_url"]
        })

def get_game_ref(game_id: str):
    """Retourne la référence Firebase pour une partie donnée."""
    return db.reference(f"/games/{game_id}")