from datetime import date, datetime
import json
import os
from bet_editor import render_bet_editor
import plotly.express as px
import pandas as pd
import requests
import streamlit as st
from poisson_laskuri import render_poisson_tab
from poisson_laskuri import laske_kaikki_todennakoisyydet
from poisson_model import calculate_match_markets

st.set_page_config(page_title="Epicbet Dashboard", layout="wide")

st.title("🎲 Epicbet — Pelikassan & EV:n seuranta")

# --- TIETOKANTAYHTEYS (SUPABASE REST API) ---
SUPABASE_URL = "https://icywiagkvqlplfyrkuhq.supabase.co"
SUPABASE_KEY = "sb_publishable_lY34TugK8aoguFdyD-z0UQ_imN2Dmg6"

try:
    if "SUPABASE_URL" in st.secrets:
        SUPABASE_URL = st.secrets["SUPABASE_URL"]
    if "SUPABASE_KEY" in st.secrets and st.secrets["SUPABASE_KEY"] != "sinun_supabase_anon_tai_service_role_avain":
        SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except Exception:
    pass

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

def load_bets_from_db():
    """Hakee vedot Supabasesta REST API:n kautta."""
    if not SUPABASE_KEY:
        return []
    try:
        url = f"{SUPABASE_URL}/rest/v1/bets?select=*&order=id.desc"
        response = requests.get(url, headers=HEADERS, timeout=5)
        if response.status_code == 200:
            data = response.json()
            bets_list = []
            for row in data:
                status_map = {
                    'PENDING': 'Avoin',
                    'WON': 'Voitto 🟢',
                    'LOST': 'Tappio 🔴',
                    'VOID': 'Mitätöity 🟡'
                }
                stake = float(row.get("stake", 0.0) or 0.0)
                odds = float(row.get("odds", 0.0) or 0.0)
                fair_o = float(row.get("calculated_fair_odds", 0.0) or 0.0)
                status = row.get("status", "PENDING")
                
                # Tarkistetaan ensin onko kantaan tallennettu erillinen payout (esim. manuaalinen tappio/voitto)
                db_payout = row.get("payout")
                if db_payout is not None:
                    paluu = float(db_payout)
                else:
                    # Fallback vanhalle logiikalle, jos payout on tyhjä
                    if status == 'WON':
                        paluu = stake * odds
                    elif status == 'VOID':
                        paluu = stake
                    else:
                        paluu = 0.0

                ev_val = ((1.0 / fair_o) * odds - 1.0) * 100 if fair_o > 0 else 0.0

                bets_list.append({
                    "id": row.get("id"),
                    "Päiväys": str(row.get("match_date", ""))[:16],
                    "Sarja": row.get("league", ""),
                    "Ottelu": f"{row.get('home_team', '')} - {row.get('away_team', '')}",
                    "Markkina": row.get("bet_market", "1X2"),
                    "Valinta": row.get("selected_pick", ""),
                    "Kerroin": odds,
                    "Raja": f"{fair_o:.2f}",
                    "EV %": f"+{ev_val:.1f}%" if ev_val > 0 else f"{ev_val:.1f}%",
                    "Panos (€)": stake,
                    "Tila": status_map.get(status, "Avoin"),
                    "Paluu (€)": paluu
                })
            return bets_list
        return []
    except Exception as e:
        return []
def load_matches_from_db(league_name: str, date_str: str):
    """Hakee tietokantaan tallennetut ottelut tietylle päivälle ja sarjalle ilman duplikaatteja."""
    if not SUPABASE_KEY:
        return []
    try:
        url = f"{SUPABASE_URL}/rest/v1/matches?select=*&league=eq.{league_name}&match_date=eq.{date_str}&order=id.asc"
        response = requests.get(url, headers=HEADERS, timeout=5)
        if response.status_code == 200:
            data = response.json()
            matches_set = set()
            for row in data:
                match_str = f"{row.get('home_team')} - {row.get('away_team')}"
                matches_set.add(match_str)
            return list(matches_set)
        return []
    except Exception:
        return []

if "bets" not in st.session_state:
    st.session_state.bets = load_bets_from_db()


@st.cache_data(ttl=60)  # Lyhyempi tai pois päältä, jotta uudet näkyy heti
def hae_ottelut_paivalle(target_date: str):
    match_list = []

    # 1. Haetaan Supabasesta kyseisen päivän NHL-ottelut (jos sarake on olemassa)
    try:
        m_url = (
            f"{SUPABASE_URL}/rest/v1/matches"
            f"?match_date=eq.{target_date}&select=home_team,away_team,league"
        )
        resp = requests.get(m_url, headers=HEADERS, timeout=5)
        if resp.status_code == 200:
            for m in resp.json():
                # Jos sarake 'league' löytyy, otetaan vain NHL-ottelut
                if "league" in m and m["league"] and m["league"] != "NHL":
                    continue
                ottelu_str = f"{str(m.get('home_team', '')).strip()} - {str(m.get('away_team', '')).strip()}"
                if ottelu_str.strip(" -") and ottelu_str not in match_list:
                    match_list.append(ottelu_str)
    except Exception:
        pass

    # 2. Haetaan NHL-apin ottelut kyseiselle päivälle (tarkistetaan gameWeek-päivä)
    try:
        url = f"https://api-web.nhle.com/v1/schedule/{target_date}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            for game_week in data.get("gameWeek", []):
                if game_week.get("date") != target_date:
                    continue
                for game in game_week.get("games", []):
                    home = (
                        game.get("homeTeam", {}).get("placeName", {}).get("default", "")
                        + " "
                        + game.get("homeTeam", {}).get("commonName", {}).get("default", "")
                    )
                    away = (
                        game.get("awayTeam", {}).get("placeName", {}).get("default", "")
                        + " "
                        + game.get("awayTeam", {}).get("commonName", {}).get("default", "")
                    )
                    ottelu_str = f"{home.strip()} - {away.strip()}"
                    if ottelu_str.strip(" -") and ottelu_str not in match_list:
                        match_list.append(ottelu_str)
    except Exception:
        pass

    if match_list:
        return match_list

    return [f"Ei otteluita päivänä {target_date}"]

# --- SIVUPALKKI: KASSANHALLINTA & EV-LASKURI ---
st.sidebar.header("⚙️ EV & Kelly -Laskuri")

def load_bankroll_from_db(default_val: float = 113.0) -> float:
    try:
        r = requests.get(
            f"{SUPABASE_URL}/rest/v1/bankroll_state?id=eq.main&select=current_bankroll",
            headers=HEADERS,
            timeout=5,
        )
        if r.status_code == 200 and r.json():
            return float(r.json()[0]["current_bankroll"])
    except Exception:
        pass
    return default_val

def save_bankroll_to_db(new_val: float) -> bool:
    try:
        r = requests.patch(
            f"{SUPABASE_URL}/rest/v1/bankroll_state?id=eq.main",
            headers=HEADERS,
            json={"current_bankroll": float(new_val)},
            timeout=5,
        )
        return r.status_code in (200, 204)
    except Exception:
        return False

if "db_bankroll_loaded" not in st.session_state:
    st.session_state["sidebar_current_bankroll_input"] = load_bankroll_from_db(113.0)
    st.session_state["db_bankroll_loaded"] = True

current_bankroll = st.sidebar.number_input(
    "Nykyinen kassa (€)",
    step=1.0,
    format="%.2f",
    key="sidebar_current_bankroll_input",
)

if st.sidebar.button("💾 Tallenna kassa", use_container_width=True):
    if save_bankroll_to_db(current_bankroll):
        st.sidebar.success(f"Kassa {current_bankroll:.2f} € tallennettu!")
    else:
        st.sidebar.error("Kassan tallennus epäonnistui.")

target_bankroll = st.sidebar.number_input(
    "Tavoitesaldo (€)",
    value=150.0,
    step=5.0,
    format="%.2f",
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
    ["NHL", "SM-liiga", "SHL", "Jalkapallo", "Valioliiga", "La Liga", "Bundesliiga"],
    key="sidebar_selected_league_select",
)

if selected_league == "NHL":
    current_match_list = hae_ottelut_paivalle(date_str)
else:
    db_matches = load_matches_from_db(selected_league, date_str)
    current_match_list = db_matches if db_matches else [f"Ei otteluita päivänä {date_str} (Lisää Hallinnoi-välilehdeltä)"]

selected_match = st.sidebar.selectbox(
    "Valitse ottelu listasta",
    current_match_list,
    key="sidebar_selected_match_select",
)

sport = selected_league
match_title = selected_match

st.sidebar.caption(f"📌 Aktiivinen kohde: **{sport}** | **{match_title}**")

st.sidebar.markdown("---")
st.sidebar.subheader("⚽ Mallin xG-arviot (Maaliodottamat)")
col_xg1, col_xg2 = st.sidebar.columns(2)
model_xg_home = col_xg1.number_input("Koti xG", value=2.30, step=0.05, key="sidebar_model_xg_home_input")
model_xg_away = col_xg2.number_input("Vieras xG", value=1.70, step=0.05, key="sidebar_model_xg_away_input")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🎯 Valittu veto & Oma Arvio")

from poisson_laskuri import MAALIRAJAT, laske_kaikki_todennakoisyydet

VASEN_MARKKINAT = [
    "1X2 (Voittaja)",
    "Money Line",
    "Maalit",
    "BTTS (Molemmat tekevät)",
]
MAALI_VAIHTOEHDOT = [
    f"{suunta} {r:.1f} maalia"
    for r in MAALIRAJAT
    for suunta in ("Yli", "Alle")
]

def _synkkaa_oikealle():
  vasen_m = st.session_state.get("vasen_markkina_valinta")
  if vasen_m == "1X2 (Voittaja)":
    st.session_state["p_markkina_tyyppi"] = "1X2"
    merkki = st.session_state.get("vasen_merkki_1x2")
    if merkki in ["Kotivoitto (1)", "Tasapeli (X)", "Vierasvoitto (2)"]:
      st.session_state["p_kohde_1x2"] = merkki
  elif vasen_m == "Money Line":
    st.session_state["p_markkina_tyyppi"] = "Money Line"
    merkki = st.session_state.get("vasen_merkki_ml")
    if merkki in ["Kotivoitto ML (1)", "Vierasvoitto ML (2)"]:
      st.session_state["p_kohde_ml"] = merkki
  elif vasen_m == "Maalit":
    st.session_state["p_markkina_tyyppi"] = "Maalit"
    merkki = st.session_state.get("vasen_merkki_maalit")
    if merkki:
      st.session_state["p_kohde_maalit"] = merkki
      try:
        raja_val = float(str(merkki).split()[1])
        if raja_val in MAALIRAJAT:
          st.session_state["p_maaliraja"] = raja_val
      except (IndexError, ValueError):
        pass
  elif vasen_m == "BTTS (Molemmat tekevät)":
    st.session_state["p_markkina_tyyppi"] = "BTTS"
    merkki = st.session_state.get("vasen_merkki_btts")
    if merkki in ["BTTS Kyllä", "BTTS Ei"]:
      st.session_state["p_kohde_btts"] = merkki


# 1. Markkinan valinta vasemmalle puolelle synkronoituna Poisson-laskurin kanssa
valittu_markkina_vasen = st.sidebar.selectbox(
    "Valitse pelattava markkina",
    VASEN_MARKKINAT,
    key="vasen_markkina_valinta",
    on_change=_synkkaa_oikealle,
)

# 2. Pelattava merkki riippuu valitusta markkinasta
if valittu_markkina_vasen == "1X2 (Voittaja)":
  pelattava_merkki = st.sidebar.selectbox(
      "Pelattava merkki",
      ["Kotivoitto (1)", "Tasapeli (X)", "Vierasvoitto (2)"],
      key="vasen_merkki_1x2",
      on_change=_synkkaa_oikealle,
  )
elif valittu_markkina_vasen == "Money Line":
  pelattava_merkki = st.sidebar.selectbox(
      "Pelattava merkki",
      ["Kotivoitto ML (1)", "Vierasvoitto ML (2)"],
      key="vasen_merkki_ml",
      on_change=_synkkaa_oikealle,
  )
elif valittu_markkina_vasen == "Maalit":
  pelattava_merkki = st.sidebar.selectbox(
      "Pelattava merkki",
      MAALI_VAIHTOEHDOT,
      key="vasen_merkki_maalit",
      on_change=_synkkaa_oikealle,
  )
else:
  pelattava_merkki = st.sidebar.selectbox(
      "Pelattava merkki",
      ["BTTS Kyllä", "BTTS Ei"],
      key="vasen_merkki_btts",
      on_change=_synkkaa_oikealle,
  )
st.sidebar.markdown("---")
st.sidebar.subheader("📊 1X2 Kertoimet & Bookkerin Arvio")
col_o1, col_ox, col_o2 = st.sidebar.columns(3)
odds_1 = col_o1.number_input(
    "1 (Koti)", value=2.08, min_value=1.01, step=0.01, key="sidebar_odds_1_input"
)
odds_x = col_ox.number_input(
    "X (Tasa)", value=3.80, min_value=1.01, step=0.01, key="sidebar_odds_x_input"
)
odds_2 = col_o2.number_input(
    "2 (Vieras)", value=3.45, min_value=1.01, step=0.01, key="sidebar_odds_2_input"
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


# Synkronoidaan vasemman sivupalkin 1/X/2-valinta oikean laskurin kohteeseen
merkki_map = {
    "1 (Kotivoitto)": "Kotivoitto (1)",
    "X (Tasapeli)": "Tasapeli (X)",
    "2 (Vierasvoitto)": "Vierasvoitto (2)",
}
if st.session_state.get("_edellinen_sidebar_merkki") != selection_type:
    st.session_state["p_markkina_tyyppi"] = "1X2"
    st.session_state["p_kohde_1x2"] = merkki_map[selection_type]
    st.session_state["_edellinen_sidebar_merkki"] = selection_type

if "1" in selection_type:
    odds = odds_1
    suggested_p = fair_prob_1
elif "X" in selection_type:
    odds = odds_x
    suggested_p = fair_prob_x
else:
    odds = odds_2
    suggested_p = fair_prob_2

st.session_state["sidebar_sync_odds"] = float(odds)
st.session_state["sidebar_sync_odds_key"] = f"{selection_type}_{round(float(odds), 4)}"
    

# Haetaan Poisson-todennäköisyys (%) suoraan mallista valitulle kohteelle / merkille

tulokset_vasen = laske_kaikki_todennakoisyydet(model_xg_home, model_xg_away)
kohde_nyt = st.session_state.get(
    "calc_kohde", st.session_state.get("p_kohde_1x2", "Kotivoitto (1)")
)
markkina_nyt = st.session_state.get(
    "calc_markkina", st.session_state.get("p_markkina_tyyppi", "1X2")
)


if markkina_nyt in ("1X2", "1X2 (Voittaja)"):
    if "1" in selection_type or "Kotivoitto" in kohde_nyt:
        mallin_todennakoisyys = tulokset_vasen["kv"]
    elif "X" in selection_type or "Tasapeli" in kohde_nyt:
        mallin_todennakoisyys = tulokset_vasen["tp"]
    else:
        mallin_todennakoisyys = tulokset_vasen["vv"]
elif markkina_nyt == "Money Line":
    if "Kotivoitto" in kohde_nyt:
        mallin_todennakoisyys = tulokset_vasen["ml_kv"]
    else:
        mallin_todennakoisyys = tulokset_vasen["ml_vv"]
elif markkina_nyt in ("Maalit", "Yli/Alle maalit"):
    osat = str(kohde_nyt).split()
    suunta_key = "yli" if osat[0].lower() == "yli" else "alle"
    raja_key = f"{float(osat[1]):.1f}"
    mallin_todennakoisyys = tulokset_vasen["maalit"][raja_key][suunta_key]
else:
    if "Kyllä" in kohde_nyt:
        mallin_todennakoisyys = tulokset_vasen["btts_kylla"]
    else:
        mallin_todennakoisyys = tulokset_vasen["btts_ei"]

poisson_p = round(float(mallin_todennakoisyys) * 100.0, 1)

poisson_p = max(1.0, min(99.0, poisson_p))
poisson_str = f"Poisson ({poisson_p:.1f}%)"
fair_str = f"Bookkeri ({suggested_p:.1f}%)"

st.sidebar.markdown(f"**Oma todennäköisyysarvio kohteelle {selection_type} (%)**")

preset_choice = st.sidebar.segmented_control(
    "Valitse %-pika-arvio",
    options=[
        "40%",
        "45%",
        "50%",
        "55%",
        "60%",
        poisson_str,
        fair_str,
        "Muu / Syötä tarkka",
    ],
    default="50%",
    key="sidebar_preset_choice_segmented",
)

# Päivitetään syöttökentän session_state ENNEN number_input-widgettiä
nykyinen_valinta_avain = (
    f"{match_title}_{st.session_state.get('calc_markkina', '')}_"
    f"{st.session_state.get('calc_kohde', selection_type)}"
)

if (
    "sidebar_prob_percent_input" not in st.session_state
    or st.session_state.get("_edellinen_valinta_avain") != nykyinen_valinta_avain
):
    st.session_state["sidebar_prob_percent_input"] = float(poisson_p)
    st.session_state["_edellinen_valinta_avain"] = nykyinen_valinta_avain

preset_values = {
    "40%": 40.0,
    "45%": 45.0,
    "50%": 50.0,
    "55%": 55.0,
    "60%": 60.0,
}

if preset_choice in preset_values:
    prob_percent = preset_values[preset_choice]
elif preset_choice == poisson_str:
    prob_percent = poisson_p
elif preset_choice == fair_str:
    prob_percent = round(suggested_p, 1)
else:
    prob_percent = st.sidebar.number_input(
        "Syötä tarkka %-arvio",
        min_value=1.0,
        max_value=99.0,
        step=0.1,
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
tab1, tab2, tab3 = st.tabs(["📊 Poisson & Laskurit", "📋 Bet Manager & Historia", "✏️ Hallinnoi vetoja & Otteluita"])

# -------------------------------------------------------------------------
# VÄLILEHTI 1: POISSON & LASKURIT
# -------------------------------------------------------------------------
with tab1:
    render_poisson_tab(model_xg_home, model_xg_away)

    st.markdown("---")
    st.subheader("💾 Tallenna valittu veto seurantaan")

    # Haetaan markkinatyyppi suoraan Poisson-laskurin puolelta session statesta
    market_type = st.session_state.get("p_markkina_tyyppi", "1X2")

    # Haetaan myös vastaava kohde suoraan oikeasta valinnasta
    if market_type == "1X2":
        valittu_kohde = st.session_state.get("p_kohde_1x2", "Kotivoitto (1)")
    elif market_type == "Tuplamahdollisuus (1X/X2)":
        valittu_kohde = st.session_state.get("p_kohde_dc", "Kotivoitto tai tasapeli (1X)")
    elif market_type == "Yli/Alle maalit":
        valittu_kohde = st.session_state.get("p_kohde_ou", "Yli 2.5 maalia")
    elif market_type == "BTTS":
        valittu_kohde = st.session_state.get("p_kohde_btts", "BTTS Kyllä")
    else:
        valittu_kohde = st.session_state.get("p_kohde_live", "Live / Muu valinta")

    tulokset_vasen = laske_kaikki_todennakoisyydet(model_xg_home, model_xg_away)

    try:
        if market_type == "1X2":
            if "Kotivoitto" in valittu_kohde:
                mallin_todennakoisyys = tulokset_vasen["kv"]
            elif "Tasapeli" in valittu_kohde:
                mallin_todennakoisyys = tulokset_vasen["tp"]
            else:
                mallin_todennakoisyys = tulokset_vasen["vv"]
        elif market_type == "Tuplamahdollisuus (1X/X2)":
            if "1X" in valittu_kohde or "Kotivoitto" in valittu_kohde:
                mallin_todennakoisyys = tulokset_vasen["kv"] + tulokset_vasen["tp"]
            else:
                mallin_todennakoisyys = tulokset_vasen["tp"] + tulokset_vasen["vv"]
        elif market_type == "Yli/Alle maalit":
            osat = str(valittu_kohde).split()
            suunta_key = "yli" if len(osat) > 0 and osat[0].lower() == "yli" else "alle"
            raja_val = float(osat[1]) if len(osat) > 1 else 2.5
            raja_key = f"{raja_val:.1f}"
            mallin_todennakoisyys = (
                tulokset_vasen["maalit"]
                .get(raja_key, {})
                .get(suunta_key, tulokset_vasen["maalit"]["2.5"]["yli"])
            )
        elif market_type == "BTTS":
            if "Kyllä" in valittu_kohde:
                mallin_todennakoisyys = tulokset_vasen["btts_kylla"]
            else:
                mallin_todennakoisyys = tulokset_vasen["btts_ei"]
        else:
            mallin_todennakoisyys = tulokset_vasen["tp"]
    except Exception:
        mallin_todennakoisyys = tulokset_vasen["kv"]

    # Lasketaan rajakerroin suoraan valitun markkinan todennäköisyydestä
    try:
        if mallin_todennakoisyys and float(mallin_todennakoisyys) > 0:
            prob_val = float(mallin_todennakoisyys)
            prob_frac = prob_val / 100.0 if prob_val > 1.0 else prob_val
            laskettu_rajakerroin = (1.0 / prob_frac) if prob_frac > 0 else fair_odds
        else:
            laskettu_rajakerroin = fair_odds
    except Exception:
        laskettu_rajakerroin = fair_odds

    raja_teksti = (
        f"{laskettu_rajakerroin:.2f}"
        if laskettu_rajakerroin and laskettu_rajakerroin != float("inf")
        else "–"
    )

    bet_type_choice = st.radio(
        "Vedon tyyppi",
        ["Malli", "Fiilis"],
        horizontal=True,
        key="bet_type_choice_tab1",
    )

    is_valid_match = "Ei " not in match_title and " - " in match_title

    col_save1, col_save2 = st.columns([3, 1], vertical_alignment="center")
    with col_save1:
        if is_valid_match:
            st.info(
                f"**Kohde:** {match_title} | **Markkina:** {market_type} | "
                f"**Valinta:** {valittu_kohde} | **Panos:** {actual_stake:.2f} € | "
                f"**Kerroin:** {odds:.2f} | **Rajakerroin:** {raja_teksti}"
            )
        else:
            st.warning(
                "⚠️ Valitulla päivällä ei ole voimassa olevaa ottelua. "
                "Lisää ottelu 'Hallinnoi vetoja & Otteluita' -välilehdeltä."
            )

    with col_save2:
        save_button = st.button(
            "➕ Tallenna veto kantaan",
            type="primary",
            use_container_width=True,
            disabled=not is_valid_match,
            key="save_bet_button_tab1",
        )
    if save_button and is_valid_match:
        if not SUPABASE_KEY:
            st.error("Supabase API-avain puuttuu!")
        else:
            try:
                parts = match_title.split(" - ")
                h_team = parts[0].strip() if len(parts) > 0 else "Koti"
                a_team = parts[1].strip() if len(parts) > 1 else "Vieras"

                full_datetime = datetime.combine(selected_date, datetime.now().time()).isoformat()

                tallennus_markkina = st.session_state.get("calc_markkina", market_type)
                tallennus_kohde = st.session_state.get("calc_kohde", selection_type)
                tallennus_kerroin = float(st.session_state.get("calc_kerroin", odds))
                tallennus_rajakerroin = float(st.session_state.get("calc_rajakerroin", fair_odds))

                payload = {
                    "match_date": full_datetime,
                    "league": sport,
                    "home_team": h_team,
                    "away_team": a_team,
                    "bet_market": tallennus_markkina,
                    "selected_pick": tallennus_kohde,
                    "odds": tallennus_kerroin,
                    "closing_odds": tallennus_kerroin,
                    "stake": float(actual_stake),
                    "model_xg_home": float(model_xg_home),
                    "model_xg_away": float(model_xg_away),
                    "calculated_fair_odds": tallennus_rajakerroin,
                    "status": "PENDING",
                    "bet_type": bet_type_choice,
                }

                url = f"{SUPABASE_URL}/rest/v1/bets"
                response = requests.post(url, headers=HEADERS, json=payload, timeout=5)

                if response.status_code in [200, 201]:
                    st.success(f"Veto ({bet_type_choice}) tallennettu onnistuneesti Supabaseen!")
                    st.session_state.bets = load_bets_from_db()
                    st.rerun()
                else:
                    st.error(f"Tallennus epäonnistui: {response.text}")
            except Exception as e:
                st.error(f"Virhe tallennuksessa: {e}")
# -------------------------------------------------------------------------
# VÄLILEHTI 2: BET MANAGER & HISTORIA
# -------------------------------------------------------------------------
with tab2:
    st.subheader("📋 Bet Manager — Vedonlyöntihistoria, Graafit & Poisto")

    raw_bets = []
    try:
        url = f"{SUPABASE_URL}/rest/v1/bets?select=*&order=id.desc"
        response = requests.get(url, headers=HEADERS, timeout=5)
        if response.status_code == 200:
            raw_bets = response.json()
    except Exception:
        pass

    bet_type_by_id = {
        r.get("id"): (r.get("bet_type") or "Malli")
        for r in raw_bets
        if r.get("id") is not None
    }

    df_bets = load_bets_from_db()

    def _get_bet_type(bet_row: dict) -> str:
        val = (
            bet_row.get("bet_type")
            or bet_row.get("Vedon tyyppi")
            or bet_type_by_id.get(bet_row.get("id"))
            or "Malli"
        )
        return "Fiilis" if str(val).strip().lower() == "fiilis" else "Malli"

    if df_bets:
        total_staked = sum(float(b.get("Panos (€)", 0.0) or 0.0) for b in df_bets)
        total_returned = sum(float(b.get("Paluu (€)", 0.0) or 0.0) for b in df_bets)
        net_profit = total_returned - total_staked
        total_roi = (net_profit / total_staked * 100) if total_staked > 0 else 0.0

        profit_color = "green" if net_profit >= 0 else "red"
        st.caption(
            f"📊 Yhteensä asetettu: **{total_staked:.2f} €** | Palautukset: **{total_returned:.2f} €** | "
            f"Netto: <span style='color:{profit_color};'>**{net_profit:+.2f} €**</span> | "
            f"ROI: **{total_roi:+.1f}%**",
            unsafe_allow_html=True,
        )

        # Erilliset suorituskykymittarit: Malli vs. Fiilis
        def _laske_tyyppi_mittarit(bets_lista, kohde_tyyppi):
            suodatetut = [b for b in bets_lista if _get_bet_type(b) == kohde_tyyppi]
            panokset = sum(float(x.get("Panos (€)", 0.0) or 0.0) for x in suodatetut)
            palautukset = sum(float(x.get("Paluu (€)", 0.0) or 0.0) for x in suodatetut)
            netto = palautukset - panokset
            roi = (netto / panokset * 100) if panokset > 0 else 0.0
            return {
                "maara": len(suodatetut),
                "panokset": panokset,
                "palautukset": palautukset,
                "netto": netto,
                "roi": roi,
            }

        malli_m = _laske_tyyppi_mittarit(df_bets, "Malli")
        fiilis_m = _laske_tyyppi_mittarit(df_bets, "Fiilis")

        st.markdown("#### 🎯 Suorituskyky: Malli vs. Fiilis")
        col_m, col_f = st.columns(2)

        with col_m:
            st.markdown("**🤖 Malli**")
            m1, m2, m3 = st.columns(3)
            m1.metric("Vetoja", f"{malli_m['maara']}")
            m2.metric("Netto", f"{malli_m['netto']:+.2f} €", delta=f"Panos {malli_m['panokset']:.2f} €")
            m3.metric("ROI", f"{malli_m['roi']:+.1f}%")

        with col_f:
            st.markdown("**🔥 Fiilis**")
            f1, f2, f3 = st.columns(3)
            f1.metric("Vetoja", f"{fiilis_m['maara']}")
            f2.metric("Netto", f"{fiilis_m['netto']:+.2f} €", delta=f"Panos {fiilis_m['panokset']:.2f} €")
            f3.metric("ROI", f"{fiilis_m['roi']:+.1f}%")

        st.markdown("---")

        suodatin_tyyppi = st.radio(
            "Näytä vedot (graafi ja historia)",
            ["Kaikki", "Malli", "Fiilis"],
            horizontal=True,
            key="bet_history_type_filter",
        )

        if suodatin_tyyppi == "Kaikki":
            naytettavat_bets = list(df_bets)
        else:
            naytettavat_bets = [b for b in df_bets if _get_bet_type(b) == suodatin_tyyppi]

        # Graafiosuus selkeytettynä (päiväkohtainen kumulatiivinen tuotto)
        try:
            import plotly.express as px
            import pandas as pd

            if naytettavat_bets:
                graph_df = pd.DataFrame(naytettavat_bets)
                if (
                    "Päiväys" in graph_df.columns
                    and "Paluu (€)" in graph_df.columns
                    and "Panos (€)" in graph_df.columns
                ):
                    if "Tila" in graph_df.columns:
                        graph_df = graph_df[graph_df["Tila"] != "Avoin"].copy()

                    graph_df["Päivä"] = pd.to_datetime(graph_df["Päiväys"], errors="coerce").dt.date
                    graph_df = graph_df.dropna(subset=["Päivä"])
                    graph_df["Netto"] = (
                        pd.to_numeric(graph_df["Paluu (€)"], errors="coerce").fillna(0.0)
                        - pd.to_numeric(graph_df["Panos (€)"], errors="coerce").fillna(0.0)
                    )

                    if not graph_df.empty:
                        daily_df = (
                            graph_df.groupby("Päivä", as_index=False)
                            .agg(Päivän_netto=("Netto", "sum"), Vetoja=("Netto", "count"))
                            .sort_values("Päivä")
                        )
                        daily_df["Kumulatiivinen tuotto (€)"] = daily_df["Päivän_netto"].cumsum()
                        daily_df["Kassa (€)"] = (
                            current_bankroll
                            - daily_df["Kumulatiivinen tuotto (€)"].iloc[-1]
                            + daily_df["Kumulatiivinen tuotto (€)"]
                        )

                        fig = px.line(
                            daily_df,
                            x="Päivä",
                            y="Kumulatiivinen tuotto (€)",
                            title=f"📈 Kumulatiivinen tuotto ({suodatin_tyyppi})",
                            markers=True,
                            hover_data={"Päivän_netto": ":.2f", "Kassa (€)": ":.2f", "Vetoja": True},
                        )
                        fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.6)
                        fig.update_traces(line=dict(width=3), marker=dict(size=8))
                        fig.update_layout(
                            xaxis_title="Päiväys",
                            yaxis_title="Tuotto (€)",
                            hovermode="x unified",
                            xaxis=dict(tickformat="%d.%m.%Y"),
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("Ei ratkenneita vetoja valitulla suodattimella graafia varten.")
            else:
                st.info(f"Ei vetoja kategoriassa '{suodatin_tyyppi}'.")
        except Exception as e:
            st.info(f"Graafin lataus ei onnistunut: {e}")
            st.markdown("---")

        with st.expander("🗑️ Poista tai hallinnoi yksittäistä vetoa suoraan tästä"):
            if raw_bets:
                bet_options = {}
                for r in raw_bets:
                    market = r.get("bet_market", "1X2")
                    b_type = _get_bet_type(r)
                    tyyppi_merkki = "🔥" if b_type == "Fiilis" else f"[{b_type}]"
                    label = (
                        f"ID {r['id']} | {tyyppi_merkki} {str(r['match_date'])[:10]} | "
                        f"{r['home_team']} - {r['away_team']} | [{market}] ({r['selected_pick']})"
                    )
                    bet_options[label] = r["id"]

                selected_del_label = st.selectbox(
                    "Valitse poistettava veto",
                    list(bet_options.keys()),
                    key="direct_del_select",
                )
                selected_del_id = bet_options[selected_del_label]

                col_d1, col_d2 = st.columns([2, 1])
                with col_d1:
                    st.write(f"Valittu ID: **{selected_del_id}**")
                with col_d2:
                    if st.button(
                        "🗑️ Vahvista poisto",
                        type="primary",
                        use_container_width=True,
                        key="confirm_delete_button",
                    ):
                        try:
                            del_url = f"{SUPABASE_URL}/rest/v1/bets?id=eq.{selected_del_id}"
                            del_resp = requests.delete(del_url, headers=HEADERS, timeout=5)
                            if del_resp.status_code in [200, 204]:
                                st.success(f"Veto ID {selected_del_id} poistettu!")
                                st.rerun()
                            else:
                                st.error(f"Poisto epäonnistui: {del_resp.text}")
                        except Exception as e:
                            st.error(f"Virhe: {e}")

        for b in naytettavat_bets:
            if _get_bet_type(b) == "Fiilis" and "Valinta" in b and b["Valinta"]:
                if not str(b["Valinta"]).startswith("🔥 "):
                    b["Valinta"] = f"🔥 {b['Valinta']}"
        render_bet_editor(naytettavat_bets, SUPABASE_URL, HEADERS, SUPABASE_KEY)
    else:
        render_bet_editor(df_bets, SUPABASE_URL, HEADERS, SUPABASE_KEY)
# -------------------------------------------------------------------------
# VÄLILEHTI 3: HALLINNOI VETOJA JA LISÄÄ OTTELUITA
# -------------------------------------------------------------------------
with tab3:
    st.subheader("🏒 Lisää uusi ottelu tietokantaan")
    
    default_home = ""
    default_away = ""
    if " - " in match_title and "Ei " not in match_title:
        split_names = match_title.split(" - ")
        if len(split_names) == 2:
            default_home = split_names[0].strip()
            default_away = split_names[1].strip()

    with st.form("add_match_form"):
        col_m_date, col_m_league = st.columns(2)
        new_match_date = col_m_date.date_input("Ottelupäivä", value=selected_date)
        new_match_league = col_m_league.selectbox("Sarja", ["SM-liiga", "SHL", "Valioliiga", "La Liga", "Bundesliiga", "NHL", "Jalkapallo","Muu"])
        col_m_home, col_m_away = st.columns(2)
        new_home_team = col_m_home.text_input("Kotijoukkue", value=default_home)
        new_away_team = col_m_away.text_input("Vierasjoukkue", value=default_away)
        
        #submit_match = st.form_submit_button("➕ Tallenna ottelu kantaan", type="primary", use_container_width=True)
        submit_match = st.form_submit_button(
            "➕ Tallenna ottelu kantaan ➕", 
            type="primary", 
            use_container_width=True, 
            key="save_match_button_unique"
        )
        #submit_match = st.form_submit_button("➕ Tallenna ottelu kantaan", type="primary", use_container_width=True)
        if submit_match:
            if not new_home_team or not new_away_team:
                st.error("❌ Täytä sekä koti- että vierasjoukkueen nimi!")
            else:
                try:
                    match_payload = {
                        "match_date": new_match_date.strftime("%Y-%m-%d"),
                        "league": new_match_league,
                        "home_team": new_home_team.strip(),
                        "away_team": new_away_team.strip()
                    }
                    m_url = f"{SUPABASE_URL}/rest/v1/matches"
                    
                    # Tulostetaan varmuuden vuoksi myös terminaaliin mitä lähetetään
                    print(f"Lähetetään ottelu: {match_payload}")
                    
                    m_resp = requests.post(url=m_url, headers=HEADERS, json=match_payload, timeout=5)
                    
                    if m_resp.status_code in [200, 201]:
                        st.success(f"✅ Ottelu {new_home_team} - {new_away_team} lisätty kantaan!")
                        st.rerun()
                    else:
                        # Tässä näytetään nyt tarkka HTTP-statuskoodi ja Supabasen virheteksti
                        st.error(f"❌ Tallennus epäonnistui (Status {m_resp.status_code}): {m_resp.text}")
                except Exception as e:
                    st.error(f"❌ Yhteysvirhe: {e}")
    st.markdown("---")
    st.subheader("✏️ Vetotietojen statuspäivitys (Supabase)")
    
    if not SUPABASE_KEY:
        st.warning("Supabase API-avain puuttuu.")
    else:
        if raw_bets:
            bet_options = {}
            for r in raw_bets:
                market = r.get('bet_market', '1X2')
                label = f"ID {r['id']} | {str(r['match_date'])[:10]} | {r['home_team']} - {r['away_team']} | [{market}] ({r['selected_pick']})"
                bet_options[label] = r['id']
            
            selected_label = st.selectbox("Valitse vedon ID jota päivitetään", list(bet_options.keys()))
            selected_bet_id = bet_options[selected_label]
            
            selected_row = next(r for r in raw_bets if r['id'] == selected_bet_id)
            st.info(f"**Valittu:** {selected_row['home_team']} – {selected_row['away_team']} | **Markkina:** {selected_row.get('bet_market', '1X2')} | **Kohde:** {selected_row['selected_pick']} | **Kerroin:** {selected_row['odds']} | **Status:** {selected_row['status']}")
            
            new_status = st.selectbox("Uusi status", ["PENDING", "WON", "LOST", "VOID"], key="status_select_tab3")
            if st.button("Päivitä status kantaan", use_container_width=True):
                try:
                    url = f"{SUPABASE_URL}/rest/v1/bets?id=eq.{selected_bet_id}"
                    payload = {"status": new_status}
                    response = requests.patch(url, headers=HEADERS, json=payload, timeout=5)
                    
                    if response.status_code in [200, 204]:
                        st.success(f"Veto ID {selected_bet_id} päivitetty!")
                        st.rerun()
                    else:
                        st.error(f"Virhe: {response.text}")
                except Exception as e:
                    st.error(f"Virhe: {e}")
        else:
            st.info("Ei hallinnoitavia vetoja tietokannassa.")