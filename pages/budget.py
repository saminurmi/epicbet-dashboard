import pandas as pd
import streamlit as st

st.title("💰 Matkabudjetti 2026–2027")

# Oletustiedot sähköposteista ja varauksista
initial_data = [
    {
        "Kategoria": "Lennot",
        "Kuvaus": "Bangkok - Da Nang (VN698)",
        "Hinta (€)": 82.92,
        "Tila": "Maksettu",
    },
    {
        "Kategoria": "Laiva & Kuljetus",
        "Kuvaus": "Turku - Tukholma - Turku (Viking Line)",
        "Hinta (€)": 68.00,
        "Tila": "Maksettu",
    },
    {
        "Kategoria": "Lennot",
        "Kuvaus": "Helsinki - Bangkok",
        "Hinta (€)": 0.00,
        "Tila": "Suunnitelma",
    },
    {
        "Kategoria": "Majoitus",
        "Kuvaus": "Bangkok (1 vk)",
        "Hinta (€)": 0.00,
        "Tila": "Suunnitelma",
    },
    {
        "Kategoria": "Majoitus",
        "Kuvaus": "Da Nang (Joulu-Helmikuu)",
        "Hinta (€)": 0.00,
        "Tila": "Suunnitelma",
    },
]

if "expenses" not in st.session_state:
  st.session_state.expenses = pd.DataFrame(initial_data)

# Kokonaisbudjetin asetus
total_budget = st.sidebar.number_input(
    "Aseta kokonaisbudjetti (€)", value=3500, step=100
)

# Tunnusluvut
spent = st.session_state.expenses[
    st.session_state.expenses["Tila"] == "Maksettu"
]["Hinta (€)"].sum()
allocated = st.session_state.expenses["Hinta (€)"].sum()
remaining = total_budget - spent

col1, col2, col3 = st.columns(3)
col1.metric("Kokonaisbudjetti", f"{total_budget:,.2f} €")
col2.metric("Toteutuneet kulut", f"{spent:,.2f} €")
col3.metric("Jäljellä", f"{remaining:,.2f} €")

st.markdown("---")

# Kulutaulukko
st.subheader("📋 Kuerittely")

edited_df = st.data_editor(
    st.session_state.expenses,
    num_rows="dynamic",
    column_config={
        "Kategoria": st.column_config.SelectboxColumn(
            "Kategoria",
            options=[
                "Lennot",
                "Laiva & Kuljetus",
                "Majoitus",
                "Aktiivisuudet",
                "Viisumit/Vakuutukset",
                "Muut",
            ],
            required=False,  # Poistettu pakollisuus, jotta uusi rivi ei anna punaista virhettä
        ),
        "Hinta (€)": st.column_config.NumberColumn(
            "Hinta (€)", format="%.2f €", min_value=0.0
        ),
        "Tila": st.column_config.SelectboxColumn(
            "Tila",
            options=["Maksettu", "Varattu", "Suunnitelma"],
            required=False,
        ),
    },
    use_container_width=True,
)

# Päivitetään muokkaukset
st.session_state.expenses = edited_df

# Visualisointi
if not edited_df.empty and edited_df["Hinta (€)"].sum() > 0:
  st.subheader("📊 Kulujakauma")
  # Suodatetaan pois tyhjät rivit visualisoinnista
  valid_df = edited_df.dropna(subset=["Kategoria"])
  if not valid_df.empty:
    chart_data = valid_df.groupby("Kategoria")["Hinta (€)"].sum()
    st.bar_chart(chart_data)