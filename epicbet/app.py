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

if "1" in selection_type:
    odds = odds_1
    suggested_p = fair_prob_1
elif "X" in selection_type:
    odds = odds_x
    suggested_p = fair_prob_x
else:
    odds = odds_2
    suggested_p = fair_prob_2

st.sidebar.markdown(f"**Oma todennäköisyysarvio kohteelle {selection_type} (%)**")

fair_str = f"Bookkeri ({suggested_p:.1f}%)"
preset_choice = st.sidebar.segmented_control(
    "Valitse %-pika-arvio",
    options=["40%", "45%", "50%", "55%", "60%", fair_str, "Muu / Syötä tarkka"],
    default="50%",
    key="sidebar_preset_choice_segmented",
)

if preset_choice == "40%":
    prob_percent = 40.0
elif preset_choice == "45%":
    prob_percent = 45.0
elif preset_choice == "50%":
    prob_percent = 50.0
elif preset_choice == "55%":
    prob_percent = 55.0
elif preset_choice == "60%":
    prob_percent = 60.0
elif preset_choice == fair_str:
    prob_percent = round(suggested_p, 1)
else:
    prob_percent = st.sidebar.number_input(
        "Syötä tarkka %-arvio",
        value=50.0,
        min_value=1.0,
        max_value=99.0,
        step=0.5,
        key="sidebar_prob_percent_input",
    )

est_prob = prob_percent / 100.0
fair_odds = 1.0 / est_prob if est_prob > 0 else 0.0
st.sidebar.info(f"🎯 **Tarvittava minimikerroin (+EV):** vähintään **{fair_odds:.2f}**")

kelly_fraction_choice = st.sidebar.selectbox(
    "Kelly-jakaja (Säätää riskitasoa)",
    options=[0.125, 0.25, 0.50, 1.00],
    index=1,
    format_func=lambda x: {
        0.125: "1/8 Kelly (Erittäin varovainen)",
        0.25: "1/4 Kelly (Suositus / Maltillinen)",
        0.50: "1/2 Kelly (Korkea riski)",
        1.00: "Full Kelly (Maksimiriski)",
    }[x],
    key="sidebar_kelly_fraction_select",
)

ev = (est_prob * odds) - 1.0
b = odds - 1.0
kelly_full = ((est_prob * odds - 1.0) / b) if b > 0 else 0
suggested_stake_pct = max(0.0, kelly_full * kelly_fraction_choice)
suggested_stake_eur = current_bankroll * suggested_stake_pct
default_stake = max(0.10, suggested_stake_eur) if ev > 0 else 1.00

st.sidebar.markdown("---")
actual_stake = st.sidebar.number_input(
    "Asetettava panos (€)",
    value=float(round(default_stake, 2)),
    min_value=0.10,
    step=0.10,
    key="sidebar_actual_stake_input",
)

st.sidebar.markdown("---")
if ev > 0:
    st.sidebar.success(
        f"✅ **+EV (Ylikerroin!):** +{ev*100:.1f}%\n\nTarjous {odds:.2f} > Raja"
        f" {fair_odds:.2f}"
    )
    st.sidebar.metric(
        "Suositeltu Kelly-panos",
        f"{suggested_stake_eur:.2f} €",
        f"{suggested_stake_pct*100:.1f}% kassasta",
    )
else:
    st.sidebar.error(
        f"❌ **-EV (Alikerroin):** {ev*100:.1f}%\n\nTarjous {odds:.2f} < Raja"
        f" {fair_odds:.2f}"
    )

if st.sidebar.button("➕ Tallenna veto seurantaan", key="sidebar_add_bet_button"):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        insert_query = """
            INSERT INTO bets (
                match_date, league, home_team, away_team, 
                bet_market, selected_pick, odds, closing_odds, stake, 
                model_xg_home, model_xg_away, calculated_fair_odds, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """
        
        parts = match_title.split(" - ")
        h_team = parts[0] if len(parts) > 0 else "Koti"
        a_team = parts[1] if len(parts) > 1 else "Vieras"
        
        full_datetime = datetime.combine(selected_date, datetime.now().time())
        
        cursor.execute(insert_query, (
            full_datetime, sport, h_team, a_team,
            "1X2", selection_type, odds, odds, actual_stake,
            0.0, 0.0, fair_odds, 'PENDING'
        ))
        
        connection.commit()
        cursor.close()
        connection.close()
        
        st.sidebar.success("Veto tallennettu Supabaseen!")
        st.session_state.bets = load_bets_from_db()
        st.rerun()
    except Exception as e:
        st.sidebar.error(f"Virhe tallennuksessa: {e}")


# --- PÄÄSIVU: KASSAN KEHITYS & MITTARIT ---
col1, col2, col3 = st.columns(3)
col1.metric("Nykyinen kassa", f"{current_bankroll:.2f} €")
col2.metric(
    "Tavoite",
    f"{target_bankroll:.2f} €",
    f"-{target_bankroll - current_bankroll:.2f} €",
)
progress_pct = (
    (current_bankroll / target_bankroll) * 100 if target_bankroll > 0 else 0
)
col3.metric("Edistyminen", f"{progress_pct:.1f}%")

st.markdown("---")

# --- LUODAAN VÄLILEHDET ---
tab1, tab2, tab3 = st.tabs(["📈 Poisson & Laskurit", "📋 Bet Manager & Historia", "✏️ Hallinnoi vetoja"])

# -------------------------------------------------------------------------
# VÄLILEHTI 1: POISSON & LASKURIT
# -------------------------------------------------------------------------
with tab1:
    st.subheader("📈 Poisson & Rajakerroin -laskuri")
    render_poisson_tab()

# -------------------------------------------------------------------------
# VÄLILEHTI 2: BET MANAGER & HISTORIA
# -------------------------------------------------------------------------
with tab2:
    st.subheader("📋 Bet Manager — Vedonlyöntihistoria & Hallinta")

    df_bets = load_bets_from_db()

    if df_bets:
        total_staked = sum(b.get("Panos (€)", 0.0) for b in df_bets)
        total_returned = sum(b.get("Paluu (€)", 0.0) for b in df_bets)
        net_profit = total_returned - total_staked

        profit_color = "green" if net_profit >= 0 else "red"
        st.caption(
            f"📊 Yhteensä asetettu: **{total_staked:.2f} €** | Palautukset:"
            f" **{total_returned:.2f} €** | Netto: <span"
            f" style='color:{profit_color};'>**{net_profit:+.2f} €**</span>",
            unsafe_allow_html=True,
        )

        st.markdown("---")
        st.dataframe(pd.DataFrame(df_bets), use_container_width=True)
    else:
        st.info("Ei vetoja tietokannassa.")

# -------------------------------------------------------------------------
# VÄLILEHTI 3: HALLINNOI VETOJA
# -------------------------------------------------------------------------
with tab3:
    st.subheader("✏️ Vetojen tulosten päivitys (Supabase)")
    
    raw_df_bets = pd.DataFrame()
    try:
        connection = get_db_connection()
        raw_df_bets = pd.read_sql("SELECT * FROM bets ORDER BY id ASC;", connection)
        connection.close()
    except Exception as e:
        st.error(f"Virhe haettaessa vetoja päivitystä varten: {e}")

    if not raw_df_bets.empty:
        bet_ids = raw_df_bets['id'].tolist()
        selected_bet_id = st.selectbox("Valitse vedon ID jota muokataan", bet_ids)
        
        selected_row = raw_df_bets[raw_df_bets['id'] == selected_bet_id].iloc[0]
        st.info(f"**Ottelu:** {selected_row['home_team']} – {selected_row['away_team']} | **Kohde:** {selected_row['selected_pick']} | **Kerroin:** {selected_row['odds']} | **Nykyinen status:** {selected_row['status']}")
        
        col_status1, col_status2 = st.columns(2)
        with col_status1:
            new_status = st.selectbox("Uusi status", ["PENDING", "WON", "LOST", "VOID"], key="status_select_tab3")
        
        with col_status2:
            st.write("") 
            st.write("")
            update_button = st.button("Päivitä status kantaan")
            
        if update_button:
            try:
                connection = get_db_connection()
                cursor = connection.cursor()
                update_query = "UPDATE bets SET status = %s WHERE id = %s;"
                cursor.execute(update_query, (new_status, int(selected_bet_id)))
                connection.commit()
                cursor.close()
                connection.close()
                
                st.success(f"Veto ID {selected_bet_id} päivitetty statukselle: {new_status}!")
                st.rerun()
            except Exception as e:
                st.error(f"Virhe päivityksessä: {e}")
    else:
        st.info("Ei päivitettäviä vetoja tietokannassa.")