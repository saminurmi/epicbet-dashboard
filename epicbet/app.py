import streamlit as st
import pandas as pd
import plotly.express as px
import psycopg2
from datetime import datetime

# Asetetaan sivun leveys
st.set_page_config(page_title="Epicbet – Pelikassa & EV seuranta", layout="wide")

# --- TIETOKANTAYHTEYS JA APUFUNKTIOT ---
def get_db_connection():
    return psycopg2.connect(
        host="db.icywiagkvqlplfyrkuhq.supabase.co",
        database="postgres",
        user="postgres",
        password="WLpulelShZbg6BdL",
        port=5432
    )

def get_bets_from_db():
    try:
        connection = get_db_connection()
        query = "SELECT * FROM bets ORDER BY id ASC;"
        df = pd.read_sql(query, connection)
        connection.close()
        return df
    except Exception as e:
        st.error(f"Virhe tietokannan luvussa: {e}")
        return pd.DataFrame()

# --- SIVUPALKKI: KASSANHALLINTA & EV-LASKURI ---
st.sidebar.header("⚙️ EV & Kelly -Laskuri")
current_bankroll = st.sidebar.number_input("Nykyinen kassa (€)", value=53.45, step=1.0)
target_bankroll = st.sidebar.number_input("Tavoitesaldo (€)", value=60.00, step=1.0)

# --- PÄÄOTSIKKO ---
st.title("🎲 Epicbet — Pelikassan & EV:n seuranta")

# Haetaan tiedot tietokannasta kerralla
df_bets = get_bets_from_db()

# --- LUODAAN VÄLILEHDET ---
tab1, tab2, tab3 = st.tabs(["📈 Kassa & Graafit", "➕ Lisää veto", "✏️ Hallinnoi vetoja"])

# -------------------------------------------------------------------------
# VÄLILEHTI 1: KASSA & GRAAFIT
# -------------------------------------------------------------------------
with tab1:
    st.subheader("📈 Kassan kehitys ja trendit")

    if not df_bets.empty:
        total_bets = len(df_bets)
        total_stakes = df_bets['stake'].sum() if 'stake' in df_bets.columns else 0.0
        avg_odds = df_bets['odds'].mean() if 'odds' in df_bets.columns else 0.0

        col1, col2, col3 = st.columns(3)
        col1.metric("Vetoja yhteensä", total_bets)
        col2.metric("Panokset yhteensä", f"{total_stakes:.2f} €")
        col3.metric("Keskimääräinen kerroin", f"{avg_odds:.2f}")

        st.markdown("---")

        if 'match_date' in df_bets.columns:
            df_charts = df_bets.sort_values('match_date').reset_index(drop=True)
            
            starting_bankroll = 50.0
            bankroll_history = [starting_bankroll]
            current_b = starting_bankroll
            
            for index, row in df_charts.iterrows():
                status = row.get('status', 'PENDING')
                stake = row.get('stake', 0.0)
                odds = row.get('odds', 0.0)
                
                if status == 'WON':
                    current_b += (stake * odds) - stake
                elif status == 'LOST':
                    current_b -= stake
                
                bankroll_history.append(current_b)
            
            chart_data = pd.DataFrame({
                'Index': range(len(bankroll_history)),
                'Kassa (€)': bankroll_history
            })
            
            fig = px.line(
                chart_data, 
                x='Index', 
                y='Kassa (€)', 
                markers=True,
                title="Kassan kehitys vetojen mukaan"
            )
            
            fig.update_layout(
                xaxis_title="Vedot kronologisesti (Aloitus = 0)",
                yaxis_title="Kassa (€)",
                template="plotly_dark"
            )
            
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("📋 Kannasta lasketut vedot")
        st.dataframe(df_bets, use_container_width=True)
    else:
        st.info("Ei vetoja tietokannassa vielä.")

# -------------------------------------------------------------------------
# VÄLILEHTI 2: LISÄÄ VETO
# -------------------------------------------------------------------------
with tab2:
    st.subheader("➕ Lisää uusi veto tietokantaan")

    with st.form("bet_form"):
        col_f1, col_f2 = st.columns(2)
        
        with col_f1:
            match_date = st.date_input("Ottelupäivä", value=datetime.today())
            match