from datetime import date, datetime
import json
import os
import plotly.express as px
import psycopg2
import pandas as pd
from pypdf import PdfReader
import requests
import streamlit as st
from poisson_laskuri import render_poisson_tab

st.set_page_config(page_title="Epicbet Dashboard", layout="wide")

st.title("🎲 Epicbet — Pelikassan & EV:n seuranta")

# --- TIETOKANTAYHTEYS (SUPABASE) ---
def get_db_connection():
    return psycopg2.connect(
        host="db.icywiagkvqlplfyrkuhq.supabase.co",
        database="postgres",
        user="postgres",
        password="WLpulelShZbg6BdL",
        port=5432
    )

def load_bets_from_db():
    try:
        connection = get_db_connection()
        query = "SELECT * FROM bets ORDER BY id DESC;"
        df = pd.read_sql(query, connection)
        connection.close()
        
        bets_list = []
        for _, row in df.iterrows():
            status_map = {
                'PENDING': 'Avoin',
                'WON': 'Voitto 🟢',
                'LOST': 'Tappio 🔴',
                'VOID': 'Mitätöity 🟡'
            }
            bets_list.append({
                "id": row.get("id"),
                "Päiväys": str(row.get("match_date", "")),
                "Sarja": row.get("league", ""),
                "Ottelu": f"{row.get('home_team', '')} - {row.get('away_team', '')}",
                "Valinta": row.get("selected_pick", ""),
                "Kerroin": row.get("odds", 0.0),
                "Raja": f"{row.get('calculated_fair_odds', 0.0):.2f}",
                "Arvio %": "-", 
                "EV %": "-",
                "Panos (€)": row.get("stake", 0.0),
                "Tila": status_map.get(row.get("status", "PENDING"), "Avoin"),
                "Paluu (€)": (row.get("stake", 0.0) * row.get("odds", 0.0)) if row.get("status") == 'WON' else (0.0 if row.get("status") != 'VOID' else row.get("stake", 0.0))
            })
        return bets_list
    except Exception as e:
        st.error(f"Virhe tietokannan luvussa: {e}")
        return []

if "bets" not in st.session_state:
    st.session_state.bets = load_bets_from_db()


# --- AUTOMAATTINEN NHL-OTTELUIDEN HAKU PÄIVÄMÄÄRÄLLÄ ---
@st.cache_data(ttl=3600)
def fetch_nhl_matches_by_date(target_date: str):
    try:
        url = f"https://api-web.nhle.com/v1/schedule/{target_date}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            match_list = []
            for game_week in data.get("gameWeek", []):
                for game in game_week.get("games", []):
                    away = (
                        game.get("awayTeam", {}).get("placeName", {}).get("default", "")
                        + " "
                        + game.get("awayTeam", {}).get("commonName", {}).get("default", "")
                    )
                    home = (
                        game.get("homeTeam", {}).get("placeName", {}).get("default", "")
                        + " "
                        + game.get("homeTeam", {}).get("commonName", {}).get("default", "")
                    )
                    match_list.append(f"{away.strip()} - {home.strip()}")
            if match_list:
                return match_list
    except Exception:
        pass

    return [f"Ei NHL-otteluita päivänä {target_date}"]


# --- LIIGAN OTTELUOHJELMA ---
LIIGA_SCHEDULE = {
    "2026-10-21": ["K-Espoo - KooKoo", "Tappara - Ässät"],
    "2026-10-22": ["JYP - HPK"],
    "2026-10-23": [
        "Jukurit - Ilves",
        "Kärpät - KalPa",
        "Lukko - TPS",
        "Sport - SaiPa",
        "K-Espoo - HIFK",
    ],
    "2026-10-24": [
        "HPK - HIFK",
        "Ilves - Jukurit",
        "JYP - Ässät",
        "KooKoo - Jokerit",
        "Kärpät - KalPa",
        "Pelicans - Tappara",
        "Sport - SaiPa",
        "TPS - Lukko",
    ],
    "2026-10-27": ["KalPa - Sport"],
    "2026-10-28": [
        "HIFK - Ilves",
        "Jukurit - Lukko",
        "JYP - Tappara",
        "K-Espoo - TPS",
        "KooKoo - Ässät",
        "Kärpät - HPK",
        "Pelicans - SaiPa",
    ],
}


# --- SIVUPALKKI: KASSANHALLINTA & EV-LASKURI ---
st.sidebar.header("⚙️ EV & Kelly -Laskuri")

current_bankroll = st.sidebar.number_input(
    "Nykyinen kassa (€)",
    value=44.90,
    step=1.0,
    key="sidebar_current_bankroll_input",
)

target_bankroll = st.sidebar.number_input(
    "Tavoitesaldo (€)",
    value=60.0,
    step=1.0,
    key="sidebar_target_bankroll_input",
)
st.sidebar.markdown("---")

# --- PÄIVÄMÄÄRÄN VALINTA & SARJAT ---
st.sidebar.subheader("📅 Päivä & Ottelut")
selected_date = st.sidebar.date_input(
    "Valitse pelipäivä",
    value=date.today(),
    key="sidebar_selected_date_input",
)
date_str = selected_date.strftime("%Y-%m-%d")

selected_league = st.sidebar.selectbox(
    "Valitse sarja / liiga",
    ["NHL", "SM-liiga", "Valioliiga"],
    key="sidebar_selected_league_select",
)

if selected_league == "NHL":
    current_match_list = fetch_nhl_matches_by_date(date_str)
elif selected_league == "SM-liiga":
    current_match_list = LIIGA_SCHEDULE.get(
        date_str, [f"Ei merkittyjä Liiga-pelejä päivälle {date_str}"]
    )
else:
    current_match_list = [
        "Tottenham - Coventry City",
        "Manchester City - Arsenal",
        "Liverpool - Chelsea",
        "Aston Villa - Newcastle",
    ]

selected_match = st.sidebar.selectbox(
    "Valitse ottelu listasta",
    current_match_list,
    key="sidebar_selected_match_select",
)

sport = selected_league
match_title = selected_match

st.sidebar.caption(f"📌 Aktiivinen kohde: **{sport}** | **{match_title}**")

st.sidebar.markdown("---")
st.sidebar.subheader("📊 1X2 Kertoimet & Bookkerin Arvio")

col_o1, col_ox, col_o2 = st.sidebar.columns(3)
odds_1 = col_o1.number_input(
    "1 (Koti)", value=2.20, min_value=1.01, step=0.01, key="sidebar_odds_1_input"
)
odds_x = col_ox.number_input(
    "X (Tasa)", value=4.33, min_value=1.01, step=0.01, key="sidebar_odds_x_input"
)
odds_2 = col_o2.number_input(
    "2 (Vieras)", value=2.75, min_value=1.01, step=0.01, key="sidebar_odds_2_input"
)
imp_1 = 1 / odds_1
imp_x = 1 / odds_x
imp_2 = 1 / odds_2
total_imp = imp_1 + imp_x + imp_2
margin_pct = (total_imp - 1.0) * 100

fair_prob_1 = (imp_1 / total_imp) * 100
fair_prob_x = (imp_x / total_imp) * 100
fair_prob_2 = (imp_2 / total_imp) * 100

st.sidebar.caption(
    f"ℹ️ Talon marginaali: **{margin_pct:.1f}%** | Reilu palautus:"
    f" **{100/total_imp:.1f}%**"
)

st.sidebar.markdown("---")
st.sidebar.subheader("🎯 Valittu veto & Oma Arvio")

selection_type = st.sidebar.radio(
    "Pelattava merkki",
    ["1 (Kotivoitto)", "X (Tasapeli)", "2 (Vierasvoitto)"],
    key="sidebar_selection_type_radio",
)