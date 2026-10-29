import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime

# -----------------------------------------------------------------------------
# 1. ASETUKSET JA SUPABASE API -YHTEYS
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Epicbet — Pelikassan & EV:n seuranta",
    page_icon="🎲",
    layout="wide"
)

# Haetaan Supabase-asetukset Streamlit secretsistä
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except Exception:
    SUPABASE_URL = ""
    SUPABASE_KEY = ""

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

def fetch_bets_from_supabase():
    """Hakee vedot Supabasesta REST API:n kautta."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return []
    try:
        url = f"{SUPABASE_URL}/rest/v1/bets?select=*"
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            data = response.json()
            bets = []
            for row in data:
                bets.append({
                    "id": row.get("id"),
                    "Päivä": row.get("paiva", ""),
                    "Sarja": row.get("sarja", ""),
                    "Ottelu": row.get("ottelu", ""),
                    "Kohde": row.get("kohde", ""),
                    "Kerroin": float(row.get("kerroin", 1.0)),
                    "Panos": float(row.get("panos", 0.0)),
                    "Arvio (%)": float(row.get("arvio_prosentti", 0.0)),
                    "Tulos": row.get("tulos", "Avoin"),
                    "Lunastus": float(row.get("lunastus", 0.0))
                })
            return bets
        else:
            return []
    except Exception:
        return []

def save_bet_to_supabase(bet):
    """Tallentaa uuden vedon Supabaseen."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return False
    try:
        url = f"{SUPABASE_URL}/rest/v1/bets"
        payload = {
            "paiva": bet.get("Päivä"),
            "sarja": bet.get("Sarja"),
            "ottelu": bet.get("Ottelu"),
            "kohde": bet.get("Kohde"),
            "kerroin": bet.get("Kerroin"),
            "panos": bet.get("Panos"),
            "arvio_prosentti": bet.get("Arvio (%)"),
            "tulos": bet.get("Tulos"),
            "lunastus": bet.get("Lunastus", 0.0)
        }
        response = requests.post(url, headers=HEADERS, json=payload)
        return response.status_code in [200, 201]
    except Exception:
        return False

def update_bet_in_supabase(bet_id, updated_fields):
    """Päivittää olemassa olevaa vetoa Supabasessa."""
    if not SUPABASE_URL or not SUPABASE_KEY or not bet_id:
        return False
    try:
        url = f"{SUPABASE_URL}/rest/v1/bets?id=eq.{bet_id}"
        payload = {}
        if "Tulos" in updated_fields:
            payload["tulos"] = updated_fields["Tulos"]
        if "Lunastus" in updated_fields:
            payload["lunastus"] = updated_fields["Lunastus"]
        
        response = requests.patch(url, headers=HEADERS, json=payload)
        return response.status_code in [200, 204]
    except Exception:
        return False

def delete_bet_from_supabase(bet_id):
    """Poistaa vedon Supabasesta."""
    if not SUPABASE_URL or not SUPABASE_KEY or not bet_id:
        return False
    try:
        url = f"{SUPABASE_URL}/rest/v1/bets?id=eq.{bet_id}"
        response = requests.delete(url, headers=HEADERS)
        return response.status_code in [200, 204]
    except Exception:
        return False

# Ladataan vedot session stateen
if "bets" not in st.session_state:
    st.session_state.bets = fetch_bets_from_supabase()

# -----------------------------------------------------------------------------
# 2. UI - PÄÄVALIKKO & VÄLILEHDET
# -----------------------------------------------------------------------------
st.title("🎲 Epicbet — Pelikassan & EV:n seuranta")

tab1, tab2, tab3 = st.tabs([
    "📈 Poisson & Laskurit", 
    "📋 Bet Manager & Historia", 
    "✏️ Hallinnoi vetoja"
])

# -----------------------------------------------------------------------------
# VÄLILEHTI 1: Poisson & Laskurit
# -----------------------------------------------------------------------------
with tab1:
    st.subheader("⚽ Poisson & Rajakerroin -laskuri")
    st.markdown("Syötä joukkueiden maaliodotukset (xG) ja tarkastele ottelun todennäköisyyksiä, rajakerroimia sekä odotusarvoa (EV).")
    
    col1, col2 = st.columns(2)
    with col1:
        home_xg = st.number_input("Kotijoukkueen xG", min_value=0.0, max_value=10.0, value=1.5, step=0.05)
    with col2:
        away_xg = st.number_input("Vierasjoukkueen xG", min_value=0.0, max_value=10.0, value=1.2, step=0.05)

    st.info(f"Odotusarvot laskettu: Kotona {home_xg} | Vieraissa {away_xg}")

# -----------------------------------------------------------------------------
# VÄLILEHTI 2: Bet Manager & Historia
# -----------------------------------------------------------------------------
with tab2:
    st.subheader("📋 Bet Manager & Historia")
    
    st.session_state.bets = fetch_bets_from_supabase()
    bets = st.session_state.bets

    if bets:
        df = pd.DataFrame(bets)
        st.dataframe(df, use_container_width=True)
        total_bets = len(df)
        st.metric("Avoimet / Kirjatut vedot yhteensä", total_bets)
    else:
        st.info("Ei vielä tallennettuja vetoja tietokannassa. Lisää ensimmäinen vetosi 'Hallinnoi vetoja' -välilehdeltä!")

# -----------------------------------------------------------------------------
# VÄLILEHTI 3: Hallinnoi vetoja
# -----------------------------------------------------------------------------
with tab3:
    st.subheader("✏️ Lisää uusi veto tai päivitä olemassa olevia")
    
    with st.form("add_bet_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            p_date = st.date_input("Päivä", value=datetime.today())
            league = st.text_input("Sarja / Liiga", "Liiga")
        with col2:
            match = st.text_input("Ottelu", "TPS - Tappara")
            market = st.text_input("Kohde", "1X2 (Kotivoitto)")
        with col3:
            odds = st.number_input("Kerroin", min_value=1.01, value=2.00, step=0.01)
            stake = st.number_input("Panos (€)", min_value=0.10, value=10.00, step=1.00)
            est_prob = st.number_input("Arvio (%)", min_value=1.0, max_value=100.0, value=50.0, step=0.5)

        submitted = st.form_submit_button("Tallenna veto Supabaseen")
        if submitted:
            new_bet = {
                "Päivä": str(p_date),
                "Sarja": league,
                "Ottelu": match,
                "Kohde": market,
                "Kerroin": odds,
                "Panos": stake,
                "Arvio (%)": est_prob,
                "Tulos": "Avoin",
                "Lunastus": 0.0
            }
            success = save_bet_to_supabase(new_bet)
            if success:
                st.success("Veto tallennettu onnistuneesti pilvitietokantaan!")
                st.session_state.bets = fetch_bets_from_supabase()
                st.rerun()
            else:
                st.error("Tallennus epäonnistui. Tarkista Supabase-yhteysasetukset.")

    st.markdown("---")
    st.subheader("Poista tai merkitse vetojen tuloksia")
    
    current_bets = fetch_bets_from_supabase()
    if current_bets:
        for b in current_bets:
            col_a, col_b, col_c = st.columns([3, 2, 1])
            with col_a:
                st.text(f"{b.get('Päivä')} | {b.get('Ottelu')} ({b.get('Kohde')}) - Kerroin: {b.get('Kerroin')}")
            with col_b:
                current_status = b.get("Tulos", "Avoin")
                status_idx = ["Avoin", "Voitto 🟢", "Tappio 🔴", "Push 🟡"].index(current_status) if current_status in ["Avoin", "Voitto 🟢", "Tappio 🔴", "Push 🟡"] else 0
                new_status = st.selectbox("Tulos", ["Avoin", "Voitto 🟢", "Tappio 🔴", "Push 🟡"], index=status_idx, key=f"status_{b['id']}")
                if new_status != current_status:
                    update_bet_in_supabase(b["id"], {"Tulos": new_status})
            with col_c:
                if st.button("Poista", key=f"del_{b['id']}"):
                    delete_bet_from_supabase(b["id"])
                    st.success("Veto poistettu!")
                    st.rerun()
    else:
        st.write("Ei poistettavia tai muokattavia vetoja.")