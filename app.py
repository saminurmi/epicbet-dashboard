import streamlit as st

st.markdown("""
    <style>
    /* Taustaväri ja yleisfontti */
    .stApp {
        background-color: #121826;
        color: #E5E7EB;
    }
    
    /* Piilotetaan vain turha valikko ja footer, mutta pidetään yläpalkki näkyvissä */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Sivupalkki selkeämmäksi ja kontrastisemmaksi */
    [data-testid="stSidebar"] {
        background-color: #1A2234;
        border-right: 1px solid #2A3649;
    }
    
    /* Varmistetaan, että sivupalkin tekstit ovat kirkkaita ja luettavia */
    [data-testid="stSidebar"] span, 
    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] div {
        color: #F3F4F6 !important;
    }
    
    /* Mittarikortit / Info-laatikot */
    .metric-card {
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
        transition: transform 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: #00D1B2;
    }
    
    .metric-label {
        font-size: 0.85rem;
        color: #94A3B8;
        font-weight: 500;
        margin-bottom: 6px;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #00D1B2;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    </style>
""", unsafe_allow_html=True)
# Sivun perusasetukset
st.set_page_config(
    page_title="Aasian Matkakojelauta 2026–2027",
    page_icon="🌴",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Tyylikäs mukautettu CSS
st.markdown("""
    <style>
    /* Taustaväri ja yleisfontti */
    
    
    /* Piilotetaan Streamlitin oikea yläkulma (Deploy & Menu) */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Sivupalkin tyyli */
    [data-testid="stSidebar"] {
        background-color: #1B2434;
        border-right: 1px solid #2D3748;
    }
    
    /* Mittarikortit / Info-laatikot */
    .metric-card {
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
        transition: transform 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: #00D1B2;
    }
    
    .metric-label {
        font-size: 0.85rem;
        color: #94A3B8;
        font-weight: 500;
        margin-bottom: 6px;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #00D1B2;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    </style>
""", unsafe_allow_html=True)

# Main Title (siivottu tuplaotsikko pois)
st.title("🌴 Aasian Matkakojelauta 2026–2027")
st.caption("Tervetuloa matkanhallintasivustolle! Täältä löydät budjetin, pakkauslistan, aikataulut ja tärkeät muistiinpanot.")

st.divider()

# Kortit rinnakkain
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
        <div class="metric-card">
            <div class="metric-label">Päiviä lähtöön (arvio)</div>
            <div class="metric-value">49 pv</div>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
        <div class="metric-card">
            <div class="metric-label">Kohteet</div>
            <div class="metric-value">Bangkok & Da Nang</div>
        </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
        <div class="metric-card">
            <div class="metric-label">Varusteet / Laukku</div>
            <div class="metric-value">Osprey Farpoint</div>
        </div>
    """, unsafe_allow_html=True)
