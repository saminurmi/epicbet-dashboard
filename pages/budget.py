import os
import pandas as pd
import streamlit as st

# Tiedosto, johon budjetti tallennetaan pysyvästi
CSV_FILE = "budjetti_data.csv"

# Ladataan data tiedostosta tai luodaan oletukset, jos tiedostoa ei vielä ole
if "df_budget" not in st.session_state:
  if os.path.exists(CSV_FILE):
    st.session_state.df_budget = pd.read_csv(CSV_FILE)
  else:
    st.session_state.df_budget = pd.DataFrame({
        "Kategoria": [
            "Lennot",
            "Laiva & Kuljetus",
            "Lennot",
            "Majoitus",
            "Majoitus",
        ],
        "Kuvaus": [
            "Bangkok - Da Nang (VN698)",
            "Turku - Tukholma - Turku (Viking Line)",
            "Tukholma - Bangkok",
            "Bangkok (1 vk)",
            "Da Nang (Joulu-Helmikuu)",
        ],
        "Hinta (€)": [82.92, 68.00, 680.00, 0.00, 0.00],
        "Tila": ["Maksettu", "Maksettu", "Suunnitelma", "Suunnitelma", "Suunnitelma"],
    })

st.title("💰 Matkabudjetti 2026–2027")

# Muokattava taulukko (num_rows="dynamic" mahdollistaa rivien lisäämisen ja poistamisen)
edited_df = st.data_editor(
    st.session_state.df_budget, num_rows="dynamic", key="budget_table"
)

# Tallennuspainike, jolla muutokset kirjoitetaan CSV-tiedostoon
if st.button("Tallenna muutokset levylle"):
  st.session_state.df_budget = edited_df
  edited_df.to_csv(CSV_FILE, index=False)
  st.success("Budjetti tallennettu onnistuneesti!")