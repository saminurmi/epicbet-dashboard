from datetime import date, datetime
import json
import os
import plotly.express as px
import pandas as pd
import requests
import streamlit as st
from poisson_laskuri import render_poisson_tab

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


# --- AUTOMAATTINEN NHL-OTTELUIDEN HAKU ---
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
                    match_list.append(f"{home.strip()} - {away.strip()}")
            if match_list:
                return list(set(match_list))
    except Exception:
        pass

    return [f"Ei NHL-otteluita päivänä {target_date}"]


# --- SIVUPALKKI: KASSANHALLINTA & EV-LASKURI ---
st.sidebar.header("⚙️ EV & Kelly -Laskuri")

current_bankroll = st.sidebar.number_input(
    "Nykyinen kassa (€)",
    value=56.27,
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
    render_poisson_tab()
    
    st.markdown("---")
    st.subheader("💾 Tallenna valittu veto seurantaan")
    
    is_valid_match = "Ei " not in match_title and " - " in match_title
    
    col_save1, col_save2 = st.columns([2, 1])
    with col_save1:
        if is_valid_match:
            st.info(f"**Kohde:** {match_title} | **Valinta:** {selection_type} | **Panos:** {actual_stake:.2f} € | **Kerroin:** {odds:.2f} | **Rajakerroin:** {fair_odds:.2f}")
        else:
            st.warning("⚠️ Valitulla päivällä ei ole voimassa olevaa ottelua. Lisää ottelu 'Hallinnoi vetoja & Otteluita' -välilehdeltä.")
    
    with col_save2:
        save_button = st.button("➕ Tallenna veto kantaan", type="primary", use_container_width=True, disabled=not is_valid_match)
        
    if save_button and is_valid_match:
        if not SUPABASE_KEY:
            st.error("Supabase API-avain puuttuu!")
        else:
            try:
                parts = match_title.split(" - ")
                h_team = parts[0] if len(parts) > 0 else "Koti"
                a_team = parts[1] if len(parts) > 1 else "Vieras"
                
                full_datetime = datetime.combine(selected_date, datetime.now().time()).isoformat()
                
                payload = {
                    "match_date": full_datetime,
                    "league": sport,
                    "home_team": h_team,
                    "away_team": a_team,
                    "bet_market": "1X2",
                    "selected_pick": selection_type,
                    "odds": float(odds),
                    "closing_odds": float(odds),
                    "stake": float(actual_stake),
                    "model_xg_home": float(model_xg_home),
                    "model_xg_away": float(model_xg_away),
                    "calculated_fair_odds": float(fair_odds),
                    "status": "PENDING"
                }
                
                url = f"{SUPABASE_URL}/rest/v1/bets"
                response = requests.post(url, headers=HEADERS, json=payload, timeout=5)
                
                if response.status_code in [200, 201]:
                    st.success("Veto tallennettu onnistuneesti Supabaseen!")
                    st.session_state.bets = load_bets_from_db()
                else:
                    st.error(f"Tallennus epäonnistui: {response.text}")
            except Exception as e:
                st.error(f"Virhe tallennuksessa: {e}")

# -------------------------------------------------------------------------
# VÄLILEHTI 2: BET MANAGER & HISTORIA (Nyt myös suora poisto!)
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
        
        # Suora poisto-osio heti taulukon yläpuolelle
        with st.expander("🗑️ Poista tai hallinnoi yksittäistä vetoa suoraan tästä"):
            if raw_bets:
                bet_options = {}
                for r in raw_bets:
                    label = f"ID {r['id']} | {str(r['match_date'])[:10]} | {r['home_team']} - {r['away_team']} ({r['selected_pick']})"
                    bet_options[label] = r['id']
                
                selected_del_label = st.selectbox("Valitse poistettava veto", list(bet_options.keys()), key="direct_del_select")
                selected_del_id = bet_options[selected_del_label]
                
                col_d1, col_d2 = st.columns([2, 1])
                with col_d1:
                    st.write(f"Valittu ID: **{selected_del_id}**")
                with col_d2:
                    if st.button("🗑️ Vahvista poisto", type="primary", use_container_width=True):
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

        st.dataframe(pd.DataFrame(df_bets), use_container_width=True)

        # Kassan kehitysgraafi
        st.markdown("### 📈 Kassan kehitys")
        try:
            chart_df = pd.DataFrame(df_bets).sort_values("id")
            chart_df["Netto"] = chart_df["Paluu (€)"] - chart_df["Panos (€)"]
            chart_df["Kumulatiivinen tulos"] = chart_df["Netto"].cumsum()
            chart_df["Kassa"] = current_bankroll + chart_df["Kumulatiivinen tulos"] - chart_df["Netto"].iloc[-1] if not chart_df.empty else current_bankroll

            fig = px.line(
                chart_df,
                x="Päiväys",
                y="Kassa",
                markers=True,
                title="Kassan kehitys vetojen mukaan",
                labels={"Kassa": "Kassa (€)", "Päiväys": "Ajankohta"}
            )
            fig.update_layout(template="plotly_dark", margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig, use_container_width=True)
        except Exception:
            st.info("Ei vielä tarpeeksi dataa graafin piirtämiseen.")
    else:
        st.info("Ei vetoja tietokannassa.")

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
        new_match_league = col_m_league.selectbox("Sarja", ["SM-liiga", "Valioliiga", "NHL", "Muu"])
        
        col_m_home, col_m_away = st.columns(2)
        new_home_team = col_m_home.text_input("Kotijoukkue", value=default_home)
        new_away_team = col_m_away.text_input("Vierasjoukkue", value=default_away)
        
        submit_match = st.form_submit_button("➕ Tallenna ottelu kantaan", type="primary", use_container_width=True)
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
                    m_resp = requests.post(m_url, headers=HEADERS, json=match_payload, timeout=5)
                    if m_resp.status_code in [200, 201]:
                        st.success(f"✅ Ottelu {new_home_team} - {new_away_team} lisätty kantaan!")
                        st.rerun()
                    else:
                        st.error(f"❌ Tallennus epäonnistui: {m_resp.text}")
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
                label = f"ID {r['id']} | {str(r['match_date'])[:10]} | {r['home_team']} - {r['away_team']} ({r['selected_pick']})"
                bet_options[label] = r['id']
            
            selected_label = st.selectbox("Valitse vedon ID jota päivitetään", list(bet_options.keys()))
            selected_bet_id = bet_options[selected_label]
            
            selected_row = next(r for r in raw_bets if r['id'] == selected_bet_id)
            st.info(f"**Valittu:** {selected_row['home_team']} – {selected_row['away_team']} | **Kohde:** {selected_row['selected_pick']} | **Kerroin:** {selected_row['odds']} | **Status:** {selected_row['status']}")
            
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