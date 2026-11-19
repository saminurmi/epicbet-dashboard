import pandas as pd
import requests
import streamlit as st

STATUS_OPTIONS = ["Avoin", "Voitto 🟢", "Tappio 🔴", "Mitätöity 🟡"]

REVERSE_STATUS_MAP = {
    "Avoin": "PENDING",
    "Voitto 🟢": "WON",
    "Tappio 🔴": "LOST",
    "Mitätöity 🟡": "VOID",
}


def update_bet_status_in_db(
    bet_id: int,
    new_status_fi: str,
    supabase_url: str,
    headers: dict,
    supabase_key: str,
) -> bool:
    """Päivittää yksittäisen vedon tilan Supabaseen REST API:n kautta."""
    if not supabase_key:
        st.error("SUPABASE_KEY puuttuu!")
        return False

    db_status = REVERSE_STATUS_MAP.get(new_status_fi, "PENDING")

    try:
        url = f"{supabase_url}/rest/v1/bets?id=eq.{bet_id}"
        payload = {"status": db_status}
        response = requests.patch(url, headers=headers, json=payload, timeout=5)
        if response.status_code not in [200, 204]:
            st.error(f"Supabase PATCH {response.status_code}: {response.text}")
            return False
        return True
    except Exception as e:
        st.error(f"PATCH-poikkeus: {e}")
        return False


def render_bet_editor(
    df_bets: list[dict] | pd.DataFrame,
    supabase_url: str,
    headers: dict,
    supabase_key: str,
) -> None:
    """Piirtää muokattavan vedonlyöntitaulukon ja tallentaa tilamuutokset Supabaseen."""
    if df_bets is None or (isinstance(df_bets, list) and len(df_bets) == 0):
        st.info("Ei vetoja näytettäväksi.")
        return

    df_editor = pd.DataFrame(df_bets).copy()
    if df_editor.empty:
        st.info("Ei vetoja näytettäväksi.")
        return

    if "Tila" in df_editor.columns:
        df_editor["Tila"] = df_editor["Tila"].where(
            df_editor["Tila"].isin(STATUS_OPTIONS), "Avoin"
        )
    else:
        df_editor["Tila"] = "Avoin"

    disabled_cols = [col for col in df_editor.columns if col != "Tila"]

    column_config = {
        "id": None,
        "Tila": st.column_config.SelectboxColumn(
            "Tila",
            help="Klikkaa solua ja valitse vedon tila valikosta",
            options=STATUS_OPTIONS,
            width="medium",
            required=True,
        ),
    }

    if "Panos (€)" in df_editor.columns:
        column_config["Panos (€)"] = st.column_config.NumberColumn(
            "Panos (€)", format="%.2f €"
        )
    if "Paluu (€)" in df_editor.columns:
        column_config["Paluu (€)"] = st.column_config.NumberColumn(
            "Paluu (€)", format="%.2f €"
        )

    edited_df = st.data_editor(
        df_editor,
        column_config=column_config,
        disabled=disabled_cols,
        hide_index=True,
        width="stretch",
        key="bets_status_editor_v2",
    )

    if st.button("💾 Tallenna tilamuutokset", type="primary", key="save_bet_statuses_btn"):
        muutoksia = 0
        for idx, row in edited_df.iterrows():
            alkuperainen_tila = df_editor.loc[idx, "Tila"]
            uusi_tila = row["Tila"]

            if uusi_tila != alkuperainen_tila:
                bet_id = int(row["id"])
                onnistui = update_bet_status_in_db(
                    bet_id=bet_id,
                    new_status_fi=uusi_tila,
                    supabase_url=supabase_url,
                    headers=headers,
                    supabase_key=supabase_key,
                )
                if onnistui:
                    muutoksia += 1
                else:
                    ottelu_nimi = row["Ottelu"] if "Ottelu" in row else f"ID {bet_id}"
                    st.error(f"Virhe päivitettäessä vetoa ID {bet_id} ({ottelu_nimi})")

        if muutoksia > 0:
            st.success(f"Päivitetty {muutoksia} vedon tila Supabaseen!")
            st.rerun()
        else:
            st.info("Ei tilamuutoksia tallennettavaksi.")