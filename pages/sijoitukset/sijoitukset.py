import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Sijoitukset", page_icon="📈", layout="wide")

st.title("📈 Sijoitussalkun historiallinen kehitys")
st.write(
    "Seuraa salkkusi arvon ja tuottojen kehitystä aikasarjana lataamalla Nordnetin kehitysraportti."
)

uploaded_file = st.file_uploader(
    "Valitse Nordnetin kehitysraportti (CSV)", type=["csv", "xlsx", "xls"]
)


def clean_numeric_series(series):
    """Puhdistaa Nordnetin lukuarvot float-muotoon riippumatta siitä miten ne on muotoiltu."""
    if series is None:
        return None
    if series.dtype == "object" or pd.api.types.is_string_dtype(series):
        cleaned = (
            series.astype(str)
            .str.replace(" ", "", regex=False)
            .str.replace("\xa0", "", regex=False)
            .str.replace(",", ".", regex=False)
        )
        return pd.to_numeric(cleaned, errors="coerce")
    return pd.to_numeric(series, errors="coerce")


if uploaded_file is not None:
    try:
        file_name = uploaded_file.name.lower()

        if file_name.endswith((".xlsx", ".xls")):
            df = pd.read_excel(uploaded_file)
        else:
            for encoding in ["utf-16", "utf-8", "latin1"]:
                try:
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file, sep="\t", encoding=encoding)
                    if len(df.columns) > 1:
                        break
                except Exception:
                    continue

        st.success("Tiedosto ladattu onnistuneesti!")
        df.columns = df.columns.str.strip()

        # Etsitään sarakkeet
        date_col = next((c for c in df.columns if "päivämäärä" in c.lower()), df.columns[0])
        value_col = next(
            (c for c in df.columns if "arvo" in c.lower() and "yhteensä" in c.lower()),
            None,
        )
        profit_eur_col = next(
            (c for c in df.columns if "tuotto" in c.lower() and "eur" in c.lower() and "kertynyt" in c.lower()),
            None,
        ) or next(
            (c for c in df.columns if "tuotto" in c.lower() and "eur" in c.lower()),
            None,
        )
        profit_pct_col = next(
            (c for c in df.columns if "tuotto" in c.lower() and "%" in c.lower() and "kertynyt" in c.lower()),
            None,
        ) or next(
            (c for c in df.columns if "tuotto" in c.lower() and "%" in c.lower()),
            None,
        )
        deposits_col = next(
            (c for c in df.columns if "nettotalletukset" in c.lower()),
            None,
        )

        # Muunnetaan päivämäärä ja numeeriset kentät
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df = df.sort_values(by=date_col).dropna(subset=[date_col])

        if value_col:
            df[value_col] = clean_numeric_series(df[value_col])
        if profit_eur_col:
            df[profit_eur_col] = clean_numeric_series(df[profit_eur_col])
        if profit_pct_col:
            df[profit_pct_col] = clean_numeric_series(df[profit_pct_col])
        if deposits_col:
            df[deposits_col] = clean_numeric_series(df[deposits_col])

        # --- SIVUPALKKI: AIKAVÄLIN RAJAUS ---
        st.sidebar.header("⚙️ Suodattimet")
        min_date = df[date_col].min().date()
        max_date = df[date_col].max().date()

        selected_dates = st.sidebar.date_input(
            "Valitse aikaväli",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
        )

        if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
            start_date, end_date = selected_dates
            mask = (df[date_col].dt.date >= start_date) & (df[date_col].dt.date <= end_date)
            df_filtered = df.loc[mask].copy()
        else:
            df_filtered = df.copy()

        # --- LASKETAAN MAX DRAWDOWN (Korkein huippu vs paha tippuma) ---
        if value_col and not df_filtered.empty:
            df_filtered["Peak"] = df_filtered[value_col].cummax()
            df_filtered["Drawdown_EUR"] = df_filtered[value_col] - df_filtered["Peak"]
            df_filtered["Drawdown_PCT"] = (df_filtered["Drawdown_EUR"] / df_filtered["Peak"]) * 100
            max_dd_eur = df_filtered["Drawdown_EUR"].min()
            max_dd_pct = df_filtered["Drawdown_PCT"].min()
        else:
            max_dd_eur, max_dd_pct = 0.0, 0.0

        # --- 1. TUNNUSLUVUT ---
        st.subheader("📊 Salkun tunnusluvut valitulla aikavälillä")

        if value_col and not df_filtered.empty:
            latest_row = df_filtered.iloc[-1]
            latest_val = latest_row[value_col]
            latest_profit_eur = (
                latest_row[profit_eur_col] if profit_eur_col and pd.notna(latest_row[profit_eur_col]) else 0.0
            )
            latest_profit_pct = (
                latest_row[profit_pct_col] if profit_pct_col and pd.notna(latest_row[profit_pct_col]) else 0.0
            )

            first_row = df_filtered.iloc[0]
            start_val = first_row[value_col] if value_col else latest_val
            change_eur = latest_val - start_val

            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Salkun arvo nyt", f"{latest_val:,.2f} €".replace(",", " "))
            c2.metric(
                "Muutos kaudella",
                f"{change_eur:,.2f} €".replace(",", " "),
                delta=f"{change_eur:,.2f} €".replace(",", " "),
            )
            c3.metric(
                "Kertynyt tuotto (€)",
                f"{latest_profit_eur:,.2f} €".replace(",", " "),
                delta=f"{latest_profit_eur:,.2f} €".replace(",", " "),
            )
            c4.metric(
                "Kertynyt tuotto (%)",
                f"{latest_profit_pct:.2f} %",
                delta=f"{latest_profit_pct:.2f} %",
            )
            c5.metric(
                "Max Drawdown (suurin pudotus)",
                f"{max_dd_pct:.2f} %",
                delta=f"{max_dd_eur:,.2f} €".replace(",", " "),
                delta_color="inverse",
            )
            st.divider()

        # --- 2. PLOTLY AIKASARJAKAAVIOT ---
        st.subheader("📈 Kehitysajanjakso")

        if value_col:
            fig_value = go.Figure()
            fig_value.add_trace(
                go.Scatter(
                    x=df_filtered[date_col],
                    y=df_filtered[value_col],
                    mode="lines",
                    name="Salkun arvo",
                    line=dict(width=2, color="#00CC96"),
                )
            )

            # Lisätään nettotalletukset kaavioon jos sarake löytyy
            if deposits_col and df_filtered[deposits_col].notna().any():
                fig_value.add_trace(
                    go.Scatter(
                        x=df_filtered[date_col],
                        y=df_filtered[deposits_col],
                        mode="lines",
                        name="Nettotalletukset",
                        line=dict(width=1.5, color="#AB63FA", dash="dash"),
                    )
                )

            fig_value.update_layout(
                title="Salkun kokonaisarvo ja nettotalletukset",
                xaxis_title="Päivämäärä",
                yaxis_title="Arvo (€)",
                hovermode="x unified",
            )
            st.plotly_chart(fig_value, use_container_width=True)

        if profit_eur_col:
            fig_profit = px.line(
                df_filtered,
                x=date_col,
                y=profit_eur_col,
                title="Kertynyt tuotto (€) aikajanalla",
                labels={profit_eur_col: "Tuotto (€)", date_col: "Päivämäärä"},
            )
            fig_profit.update_traces(line=dict(width=2, color="#636EFA"))
            st.plotly_chart(fig_profit, use_container_width=True)

        st.divider()

        # --- 3. DATATAULUKKO ---
        st.subheader("📋 Historiataulukko")
        st.dataframe(df_filtered, use_container_width=True)

        with st.expander("Katso sarakkeet ja raakadata"):
            st.write("Sarakkeet:", df.columns.tolist())
            st.dataframe(df)

    except Exception as e:
        st.error(f"Virhe tiedoston lukemisessa tai käsittelyssä: {e}")
        st.info(
            "Varmista, että latasit Nordnetistä oikean kehitysraportin CSV:na."
        )
else:
    st.info("💡 **Vinkki:** Pudota Nordnetin salkun kehitysraportti tähän tai valitse aikaväli sivupalkista.")