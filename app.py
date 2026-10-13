from datetime import date
import streamlit as st

st.set_page_config(
    page_title="Matkakojelauta 2026-2027", page_icon="✈️", layout="wide"
)

import streamlit as st

st.set_page_config(
    page_title="Matkakojelauta",
    page_icon="✈️",
    layout="wide"
)

# Custom CSS -tyylit ulkoasun parantamiseen
st.markdown("""
    <style>
    /* Pääsivun tausta ja fontti */
    .stApp {
        background-color: #0e1117;
        color: #fafafa;
    }
    
    /* Sivupalkin tyylittely */
    [data-testid="stSidebar"] {
        background-color: #161b22;
        border-right: 1px solid #30363d;
    }
    
    /* Korttimaisten elementtien taustat ja reunukset */
    div.metric-container, div.stButton > button {
        border-radius: 8px;
    }
    
    /* Muokataan painikkeita modernimmiksi */
    .stButton>button {
        background-color: #238636;
        color: white;
        border: none;
        font-weight: 600;
        transition: background-color 0.2s ease;
    }
    .stButton>button:hover {
        background-color: #2ea043;
    }
    
    /* Otsikoiden tyylit */
    h1, h2, h3 {
        letter-spacing: -0.5px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("✈️ Matkakojelauta")
st.write("Tervetuloa takaisin! Kojelauta on nyt valmiina matkan suunnitteluun.")
st.title("🌴 Aasian Matkakojelauta 2026–2027")
st.write(
    "Tervetuloa matkanhallintasivustolle! Täältä löydät budjetin, pakkauslistan,"
    " aikataulut ja tärkeät muistiinpanot."
)

# Lasketaan päivät joulukuun 2026 alkuun (esim. 1.12.2026)
target_date = date(2026, 12, 1)
today = date.today()
days_left = (target_date - today).days

col1, col2, col3 = st.columns(3)
with col1:
  st.metric(
      label="Päiviä lähtöön (arvio)",
      value=f"{days_left} pv" if days_left > 0 else "Reissu käynnissä!",
  )
with col2:
  st.metric(label="Kohteet", value="Bangkok & Da Nang")
with col3:
  st.metric(label="Varusteet / Laukku", value="Osprey Farpoint 40")

st.markdown("---")
st.subheader("📌 Navigointi")
st.write(
    "Käytä vasemman reunan valikkoa siirtyäksesi eri osioiden välille:"
    " **Budjetti**, **Pakkauslista**, **Aikataulu** ja **Muistiinpanot**."
)