from datetime import datetime
import json
import os
import plotly.express as px
from pypdf import PdfReader
import requests
import streamlit as st

st.set_page_config(page_title="Epicbet Dashboard", layout="wide")

st.title("🎲 Epicbet — Pelikassan & EV:n seuranta")

# --- TIEDOSTOPOHJAINEN TALLENNUS (JSON) ---
BETS_FILE = "bets.json"

DEFAULT_BETS = [
    {
        "Päiväys": "2026-10-20 08:59",
        "Sarja": "SM-liiga",
        "Ottelu": "TPS - Ilves",
        "Valinta": "1 (Kotivoitto)",
        "Kerroin": 2.42,
        "Raja": "2.00",
        "Arvio %": "50.0%",
        "EV %": "+21.0%",
        "Panos (€)": 1.66,
        "Tila": "Avoin",
        "Paluu (€)": 0.0,
    },
    {
        "Päiväys": "2026-10-20 08:59",
        "Sarja": "SM-liiga",
        "Ottelu": "SaiPa - Kärpät",
        "Valinta": "1 (Kotivoitto)",
        "Kerroin": 2.02,
        "Raja": "2.00",
        "Arvio %": "50.0%",
        "EV %": "+1.0%",
        "Panos (€)": 0.11,
        "Tila": "Avoin",
        "Paluu (€)": 0.0,
    },
    {
        "Päiväys": "2026-10-20 08:59",
        "Sarja": "SM-liiga",
        "Ottelu": "HPK-Pelicans",
        "Valinta": "1 (Kotivoitto)",
        "Kerroin": 2.70,
        "Raja": "2.00",
        "Arvio %": "50.0%",
        "EV %": "+35.0%",
        "Panos (€)": 1.00,
        "Tila": "Avoin",
        "Paluu (€)": 0.0,
    },
    {
        "Päiväys": "2026-10-20 08:59",
        "Sarja": "SM-liiga",
        "Ottelu": "Kookoo-Tappara",
        "Valinta": "1 (Kotivoitto)",
        "Kerroin": 4.40,
        "Raja": "2.00",
        "Arvio %": "50.0%",
        "EV %": "+120.0%",
        "Panos (€)": 1.00,
        "Tila": "Avoin",
        "Paluu (€)": 0.0,
    },
    {
        "Päiväys": "2026-10-20 08:59",
        "Sarja": "SM-liiga",
        "Ottelu": "Sport-Jukurit",
        "Valinta": "2 (Vierasvoitto)",
        "Kerroin": 2.83,
        "Raja": "2.00",
        "Arvio %": "50.0%",
        "EV %": "+41.5%",
        "Panos (€)": 2.00,
        "Tila": "Avoin",
        "Paluu (€)": 0.0,
    },
    {
        "Päiväys": "2026-10-20 08:59",
        "Sarja": "SM-liiga",
        "Ottelu": "Lukko-Hifk",
        "Valinta": "1 (Kotivoitto)",
        "Kerroin": 1.70,
        "Raja": "2.00",
        "Arvio %": "50.0%",
        "EV %": "-15.0%",
        "Panos (€)": 1.00,
        "Tila": "Avoin",
        "Paluu (€)": 0.0,
    },
]


def load_bets_from_file():
  if os.path.exists(BETS_FILE):
    try:
      with open(BETS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        if data:
          return data
    except Exception:
      pass
  return DEFAULT_BETS


def save_bets_to_file(bets_list):
  try:
    with open(BETS_FILE, "w", encoding="utf-8") as f:
      json.dump(bets_list, f, ensure_ascii=False, indent=4)
  except Exception as e:
    st.error(f"Virhe tallennuksessa: {e}")


if "bets" not in st.session_state:
  st.session_state.bets = load_bets_from_file()


# --- AUTOMAATTINEN NHL-OTTELUIDEN HAKU ---
@st.cache_data(ttl=3600)
def fetch_nhl_matches():
  try:
    url = "https://api-web.nhle.com/v1/schedule/now"
    response = requests.get(url, timeout=5)
    if response.status_code == 200:
      data = response.json()
      match_list = []
      for game_week in data.get("gameWeek", []):
        for game in game_week.get("games", []):
          away = (
              game.get("awayTeam", {}).get("placeName", {}).get("default", "")
              + " "
              + game.get("awayTeam", {}).get("commonName", {}).get(
                  "default", ""
              )
          )
          home = (
              game.get("homeTeam", {}).get("placeName", {}).get("default", "")
              + " "
              + game.get("homeTeam", {}).get("commonName", {}).get(
                  "default", ""
              )
          )
          match_list.append(f"{away.strip()} - {home.strip()}")
      if match_list:
        return match_list
  except Exception:
    pass

  return [
      "Philadelphia Flyers - Colorado Avalanche",
      "NY Rangers - Anaheim Ducks",
      "Toronto Maple Leafs - San Jose Sharks",
  ]


# --- SIVUPALKKI: KASSANHALLINTA & EV-LASKURI ---
st.sidebar.header("⚙️ EV & Kelly -Laskuri")

current_bankroll = st.sidebar.number_input(
    "Nykyinen kassa (€)", value=44.90, step=1.0
)
target_bankroll = st.sidebar.number_input(
    "Tavoitesaldo (€)", value=60.0, step=1.0
)

st.sidebar.markdown("---")
st.sidebar.subheader("🏀 Päivän ottelut & Kohde")

selected_league = st.sidebar.selectbox(
    "Valitse sarja / liiga", ["NHL", "SM-liiga", "Valioliiga"]
)

if selected_league == "NHL":
  current_match_list = fetch_nhl_matches()
elif selected_league == "SM-liiga":
  current_match_list = [
      "TPS - Ilves",
      "SaiPa - Kärpät",
      "HPK - Pelicans",
      "KooKoo - Tappara",
      "Sport - Jukurit",
      "Lukko - HIFK",
  ]
else:
  current_match_list = [
      "Tottenham - Coventry City",
      "Manchester City - Arsenal",
      "Liverpool - Chelsea",
      "Aston Villa - Newcastle",
  ]

selected_match = st.sidebar.selectbox(
    "Valitse ottelu listasta", current_match_list
)

sport = st.sidebar.text_input("Laji / Sarja", value=selected_league)
match_title = st.sidebar.text_input("Ottelu / Kohde", value=selected_match)

st.sidebar.markdown("---")
st.sidebar.subheader("📊 1X2 Kertoimet & Bookkerin Arvio")

col_o1, col_ox, col_o2 = st.sidebar.columns(3)
odds_1 = col_o1.number_input("1 (Koti)", value=2.20, min_value=1.01, step=0.01)
odds_x = col_ox.number_input("X (Tasa)", value=4.33, min_value=1.01, step=0.01)
odds_2 = col_o2.number_input("2 (Vieras)", value=2.75, min_value=1.01, step=0.01)

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
    "Pelattava merkki", ["1 (Kotivoitto)", "X (Tasapeli)", "2 (Vierasvoitto)"]
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
      "Syötä tarkka %-arvio", value=50.0, min_value=1.0, max_value=99.0, step=0.5
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
)

ev = (est_prob * odds) - 1.0
b = odds - 1.0
kelly_full = ((est_prob * odds - 1.0) / b) if b > 0 else 0
suggested_stake_pct = max(0.0, kelly_full * kelly_fraction_choice)
suggested_stake_eur = current_bankroll * suggested_stake_pct
default_stake = max(0.10, suggested_stake_eur) if ev > 0 else 1.00

actual_stake = st.sidebar.number_input(
    "Asetettava panos (€)",
    value=float(round(default_stake, 2)),
    min_value=0.10,
    step=0.10,
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

if st.sidebar.button("➕ Tallenna veto seurantaan"):
  new_bet = {
      "Päiväys": datetime.now().strftime("%Y-%m-%d %H:%M"),
      "Sarja": sport,
      "Ottelu": match_title,
      "Valinta": selection_type,
      "Kerroin": odds,
      "Raja": f"{fair_odds:.2f}",
      "Arvio %": f"{prob_percent:.1f}%",
      "EV %": f"{ev*100:+.1f}%",
      "Panos (€)": actual_stake,
      "Tila": "Avoin",
      "Paluu (€)": 0.0,
  }
  st.session_state.bets.append(new_bet)
  save_bets_to_file(st.session_state.bets)
  st.sidebar.success("Veto tallennettu pysyvästi!")

# --- PÄÄSIVU: KASSAN KEHITYS & TILASTOT ---
col1, col2, col3 = st.columns(3)
col1.metric("Nykyinen kassa", f"{current_bankroll:.2f} €")
col2.metric(
    "Tavoite",
    f"{target_bankroll:.2f} €",
    f"-{target_bankroll - current_bankroll:.2f} €",
)
col3.metric("Edistyminen", f"{(current_bankroll / target_bankroll)*100:.1f}%")

st.markdown("---")

# --- AVOIMET & TALLENNETUT VEDOT MANAGERINTI ---
st.subheader("📋 Bet Manager — Vedonlyöntihistoria & Hallinta")

if st.session_state.bets:
  total_staked = sum(b.get("Panos (€)", 0.0) for b in st.session_state.bets)
  total_returned = sum(b.get("Paluu (€)", 0.0) for b in st.session_state.bets)
  net_profit = total_returned - total_staked

  st.caption(
      f"📊 Yhteensä asetettu: **{total_staked:.2f} €** | Palautukset:"
      f" **{total_returned:.2f} €** | Netto:"
      f" **{net_profit:+.2f} €**"
  )

  st.markdown("---")

  # Otsikkorivi
  h1, h2, h3, h4, h5, h6, h7 = st.columns([1.5, 2, 1.2, 0.8, 1.2, 1.0, 0.5])
  h1.write("**Sarja & Aika**")
  h2.write("**Ottelu & Valinta**")
  h3.write("**Kerroin / EV**")
  h4.write("**Panos**")
  h5.write("**Tila**")
  h6.write("**Paluu (€)**")
  h7.write("")

  for idx, bet in enumerate(st.session_state.bets):
    c1, c2, c3, c4, c5, c6, c7 = st.columns([1.5, 2, 1.2, 0.8, 1.2, 1.0, 0.5])

    date_str = bet.get("Päiväys", "")
    c1.write(f"**{bet['Sarja']}**\n\n`{date_str}`")
    c2.write(f"{bet['Ottelu']}\n\n👉 *{bet['Valinta']}*")
    c3.write(f"@{bet['Kerroin']} | EV: {bet['EV %']}")
    c4.write(f"**{bet['Panos (€)']} €**")

    status_options = ["Avoin", "Voitto 🟢", "Tappio 🔴", "Mitätöity 🟡"]
    current_status = bet.get("Tila", "Avoin")
    status_idx = (
        status_options.index(current_status)
        if current_status in status_options
        else 0
    )

    new_status = c5.selectbox(
        "Tila",
        status_options,
        index=status_idx,
        key=f"status_{idx}",
        label_visibility="collapsed",
    )

    default_return = bet.get("Paluu (€)", 0.0)
    if new_status == "Voitto 🟢" and default_return == 0.0:
      default_return = round(bet["Panos (€)"] * bet["Kerroin"], 2)
    elif new_status in ["Tappio 🔴", "Avoin"] and current_status != new_status:
      default_return = 0.0
    elif new_status == "Mitätöity 🟡":
      default_return = float(bet["Panos (€)"])

    new_return = c6.number_input(
        "Paluu",
        value=float(default_return),
        step=0.5,
        key=f"return_{idx}",
        label_visibility="collapsed",
    )

    if new_status != bet.get("Tila") or new_return != bet.get("Paluu (€)"):
      st.session_state.bets[idx]["Tila"] = new_status
      st.session_state.bets[idx]["Paluu (€)"] = new_return
      save_bets_to_file(st.session_state.bets)
      st.rerun()

    if c7.button("🗑️", key=f"del_{idx}", help="Poista tämä veto"):
      st.session_state.bets.pop(idx)
      save_bets_to_file(st.session_state.bets)
      st.rerun()

  st.markdown("---")
  if st.button("⚠️ Tyhjennä koko vetohistoria"):
    st.session_state.bets = []
    save_bets_to_file([])
    st.rerun()

else:
  st.info(
      "Ei vielä tallennettuja vetoja. Voit kirjata uuden vedon vasemmasta"
      " sivupalkista!"
  )

st.markdown("---")

# --- PDF-HISTORIA TIEDOSTON LATAUS & PARSERI ---
st.subheader("📄 Tuo Epicbetin historiatietoja (PDF)")
uploaded_file = st.file_uploader(
    "Lataa Epicbet-tapahtumahistoria (PDF)", type=["pdf"]
)

if uploaded_file is not None:
  try:
    reader = PdfReader(uploaded_file)
    full_text = ""
    for page in reader.pages:
      full_text += page.extract_text() or ""

    st.success("✅ PDF ladattu ja teksti luettu onnistuneesti!")

    with st.expander("🔍 Näytä PDF:stä luettu raakateksti (Kehittäjänäkymä)"):
      st.text(full_text[:2000])

  except Exception as e:
    st.error(f"Virhe PDF-tiedoston lukemisessa: {e}")

st.markdown("---")

# --- TODENNÄKÖISYYSARVION APURI ---
st.subheader("📊 Kerroin- ja Todennäköisyyslaskuri")
st.write(
    "Syötä alta mikä tahansa kerroin, niin näet suoraan, millaisen"
    " todennäköisyyden bookkeri sille vaatii (implisiittinen todennäköisyys)."
)

col_a, col_b = st.columns(2)

with col_a:
  test_odds = st.number_input(
      "Testattava kerroin", value=1.73, min_value=1.01, step=0.01, key="test_odds"
  )
  implied_probability = (1 / test_odds) * 100
  st.info(f"🔍 Bookkerin vaatima todennäköisyys: **{implied_probability:.1f}%**")

with col_b:
  st.write("**Miten tätä käytetään?**")
  st.markdown("""
    * Jos oma arviosi kohteesta on **suurempi** kuin yllä näkyvä prosentti → kyseessä on ylikerroin (+EV).
    * Jos arviosi on **pienempi** → kohde on alikerroin (-EV), jota matematiikan mukaan ei kannata pelata.
    """)