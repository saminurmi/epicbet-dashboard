import streamlit as st
import pandas as pd
import requests
import math
from datetime import datetime

# -----------------------------------------------------------------------------
# 1. ASETUKSET JA SUPABASE API -YHTEYS
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Epicbet — Pelikassan & EV:n seuranta",
    page_icon="🎲",
    layout="wide"
)

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
        response = requests.patch(url, headers=HEADERS, json=updated_fields)
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

# Apufunktio Poisson-todennäköisyydelle
def poisson_prob(lmbda, k):
    return (math.exp(-lmbda) * (lmbda ** k)) / math.factorial(k)

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
    st.markdown("Syötä joukkueiden maaliodotukset (xG) laskeaksesi ottelun todennäköisyydet, 1X2-rajakertoimet sekä odotusarvon (EV).")
    
    col1, col2 = st.columns(2)
    with col1:
        home_xg = st.number_input("Kotijoukkueen xG", min_value=0.0, max_value=10.0, value=1.5, step=0.05)
    with col2:
        away_xg = st.number_input("Vierasjoukkueen xG", min_value=0.0, max_value=10.0, value=1.1, step=0.05)

    # Lasketaan maaliodotusten pohjalta todennäköisyydet (max 6 maalia per joukkue riittää kattamaan 99% tapauksista)
    max_goals = 6
    home_probs = [poisson_prob(home_xg, i) for i in range(max_goals + 1)]
    away_probs = [poisson_prob(away_xg, i) for i in range(max_goals + 1)]

    home_win = 0
    draw = 0
    away_win = 0

    for h in range(max_goals + 1):
        for a in range(max_goals + 1):
            p = home_probs[h] * away_probs[a]
            if h > a:
                home_win += p
            elif h == a:
                draw += p
            else:
                away_win += p

    # Muunnetaan rajakertoimiksi (1 / todennäköisyys)
    fair_1 = 1 / home_win if home_win > 0 else 0
    fair_x = 1 / draw if draw > 0 else 0
    fair_2 = 1 / away_win if away_win > 0 else 0

    st.markdown("---")
    st.markdown("### 📊 Lasketut todennäköisyydet ja rajakertoimet")
    
    res_col1, res_col2, res_col3 = st.columns(3)
    with res_col1:
        st.metric("Kotivoitto (1)", f"{home_win*100:.1f}%", f"Rajakerroin: {fair_1:.2f}")
    with res_col2:
        st.metric("Tasapeli (X)", f"{draw*100:.1f}%", f"Rajakerroin: {fair_x:.2f}")
    with res_col3:
        st.metric("Vierasvoitto (2)", f"{away_win*100:.1f}%", f"Rajakerroin: {fair_2:.2f}")

    st.markdown("---")
    st.subheader("💡 EV (Odotusarvo) & Kelly-laskuri")
    ev_col1, ev_col2 = st.columns(2)
    with ev_col1:
        market_odds = st.number_input("Tarjolla oleva kerroin", min_value=1.01, value=2.10, step=0.01)
        chosen_prob = st.slider("Oma arvio kohteelle (%)", min_value=1.0, max_value=100.0, value=float(round(home_win*100, 1)), step=0.5)
    with ev_col2:
        bankroll = st.number_input("Kassasi koko (€)", min_value=10.0, value=1000.0, step=50.0)
        kelly_fraction = st.selectbox("Kellyn kerrin", [1.0, 0.5, 0.25], index=1)

    # EV = (Kerroin * Todennäköisyys) - 1
    prob_dec = chosen_prob / 100.0
    ev_val = (market_odds * prob_dec) - 1.0
    
    # Kelly % = (p * b - q) / b  missä b = kerroin - 1, q = 1 - p
    b_val = market_odds - 1.0
    q_val = 1.0 - prob_dec
    kelly_pct = ((prob_dec * b_val - q_val) / b_val) if b_val > 0 else 0
    kelly_pct = max(0.0, kelly_pct) * kelly_fraction
    recommended_stake = bankroll * kelly_pct

    st.markdown(f"**Odotusarvo (EV):** `{ev_val*100:+.2f}%`")
    if ev_val > 0:
        st.success(je: f"Kohde on ylikerroin! Suositeltava panos (Kelly {kelly_fraction}x): **{recommended_stake:.2f} €** ({kelly_pct*100:.2f}% kassasta)")
    else:
        st.warning("Ei pelattavaa (EV negatiivinen tai nolla).")

# -----------------------------------------------------------------------------
# VÄLILEHTI 2: Bet Manager & Historia
# -----------------------------------------------------------------------------
with tab2:
    st.subheader("📋 Bet Manager & Historia")
    
    bets = fetch_bets_from_supabase()

    if bets:
        df = pd.DataFrame(bets)
        st.dataframe(df, use_container_width=True)
        
        total_bets = len(df)
        total_staked = df["Panos"].sum()
        st.metric("Vedot yhteensä", total_bets, f"Panokset yht: {total_staked:.2f} €")
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
                st.rerun()
            else:
                st.error("Tallennus epäonnistui. Tarkista Supabase-yhteysasetukset.")

    st.markdown("---")
    st.subheader("Muokkaa tai poista olemassa olevia vetoja")
    
    current_bets = fetch_bets_from_supabase()
    if current_bets:
        for b in current_bets:
            col_a, col_b, col_c = st.columns([3, 2, 1])
            with col_a:
                st.text(f"{b.get('Päivä')} | {b.get('Ottelu')} ({b.get('Kohde')}) - K: {b.get('Kerroin')}")
            with col_b:
                current_status = b.get("Tulos", "Avoin")
                statuses = ["Avoin", "Voitto 🟢", "Tappio 🔴", "Push 🟡"]
                status_idx = statuses.index(current_status) if current_status in statuses else 0
                new_status = st.selectbox("Tulos", statuses, index=status_idx, key=f"status_{b['id']}")
                if new_status != current_status:
                    update_bet_in_supabase(b["id"], {"tulos": new_status})
                    st.rerun()
            with col_c:
                if st.button("Poista", key=f"del_{b['id']}"):
                    delete_bet_from_supabase(b["id"])
                    st.success("Veto poistettu!")
                    st.rerun()
    else:
        st.write("Ei muokattavia vetoja.")