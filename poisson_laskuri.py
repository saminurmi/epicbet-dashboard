import numpy as np
import streamlit as st
from scipy.stats import poisson

MAALIRAJAT = [0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5]


def _synkkaa_vasemmalle():
    markkina = st.session_state.get("p_markkina_tyyppi")
    if markkina == "1X2":
        st.session_state["vasen_markkina_valinta"] = "1X2 (Voittaja)"
        kohde = st.session_state.get("p_kohde_1x2")
        if kohde in ["Kotivoitto (1)", "Tasapeli (X)", "Vierasvoitto (2)"]:
            st.session_state["vasen_merkki_1x2"] = kohde
    elif markkina == "Money Line":
        st.session_state["vasen_markkina_valinta"] = "Money Line"
        kohde = st.session_state.get("p_kohde_ml")
        if kohde in ["Kotivoitto ML (1)", "Vierasvoitto ML (2)"]:
            st.session_state["vasen_merkki_ml"] = kohde
    elif markkina == "Maalit":
        st.session_state["vasen_markkina_valinta"] = "Maalit"
        raja = st.session_state.get("p_maaliraja", 2.5)
        kohde = st.session_state.get("p_kohde_maalit", f"Yli {raja:.1f} maalia")
        suunta = "Alle" if str(kohde).startswith("Alle") else "Yli"
        päivitetty_kohde = f"{suunta} {float(raja):.1f} maalia"
        st.session_state["p_kohde_maalit"] = päivitetty_kohde
        st.session_state["vasen_merkki_maalit"] = päivitetty_kohde
    elif markkina == "BTTS":
        st.session_state["vasen_markkina_valinta"] = "BTTS (Molemmat tekevät)"
        kohde = st.session_state.get("p_kohde_btts")
        if kohde in ["BTTS Kyllä", "BTTS Ei"]:
            st.session_state["vasen_merkki_btts"] = kohde


def render_poisson_tab(koti_xg, vieras_xg):

    st.subheader("🔢 Poisson & Rajakerroin -laskuri")
    st.markdown(
        "Ottelun maaliodottamat (xG) tulevat suoraan valitusta kohteesta. "
        "Tarkastele todennäköisyyksiä, rajakertoimia sekä odotusarvoa (EV)."
    )

    tulokset = laske_kaikki_todennakoisyydet(koti_xg, vieras_xg)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 1. Ottelun tiedot & Valinnat")
        st.write(f"⚽ Kotijoukkueen xG: **{koti_xg:.2f}**")
        st.write(f"⚽ Vierasjoukkueen xG: **{vieras_xg:.2f}**")

        markkina_tyyppi = st.selectbox(
            "Valitse markkina",
            ["1X2", "Money Line", "Maalit", "BTTS", "Live"],
            key="p_markkina_tyyppi",
            on_change=_synkkaa_vasemmalle,
        )

        tarjottu_kerroin = st.number_input(
            "Epicbetin tarjoama kerroin",
            min_value=1.01,
            max_value=50.0,
            value=2.10,
            step=0.01,
            key="p_kerroin",
        )

        valittu_raja = None

        if markkina_tyyppi == "1X2":
            valittu_kohde = st.selectbox(
                "Kohde",
                ["Kotivoitto (1)", "Tasapeli (X)", "Vierasvoitto (2)"],
                key="p_kohde_1x2",
                on_change=_synkkaa_vasemmalle,
            )
        elif markkina_tyyppi == "Money Line":
            valittu_kohde = st.selectbox(
                "Kohde",
                ["Kotivoitto ML (1)", "Vierasvoitto ML (2)"],
                key="p_kohde_ml",
                on_change=_synkkaa_vasemmalle,
            )
        elif markkina_tyyppi == "Maalit":
            valittu_raja = st.selectbox(
                "Maaliraja",
                MAALIRAJAT,
                index=2,  # oletuksena 2.5
                key="p_maaliraja",
                on_change=_synkkaa_vasemmalle,
            )
            valittu_kohde = st.selectbox(
                "Kohde",
                [f"Yli {valittu_raja:.1f} maalia", f"Alle {valittu_raja:.1f} maalia"],
                key="p_kohde_maalit",
                on_change=_synkkaa_vasemmalle,
            )
        elif markkina_tyyppi == "BTTS":
            valittu_kohde = st.selectbox(
                "Kohde",
                ["BTTS Kyllä", "BTTS Ei"],
                key="p_kohde_btts",
                on_change=_synkkaa_vasemmalle,
            )
        else:  # Live
            valittu_kohde = st.selectbox(
                "Kohde",
                ["Live / Muu valinta"],
                key="p_kohde_live",
            )

    # Valitaan tarkasteltava todennäköisyys käyttäjän valinnan mukaan
    if markkina_tyyppi == "1X2":
        if "Kotivoitto" in valittu_kohde:
            todennakoisyys = tulokset["kv"]
        elif "Tasapeli" in valittu_kohde:
            todennakoisyys = tulokset["tp"]
        else:
            todennakoisyys = tulokset["vv"]
    elif markkina_tyyppi == "Money Line":
        if "Kotivoitto" in valittu_kohde:
            todennakoisyys = tulokset["ml_kv"]
        else:
            todennakoisyys = tulokset["ml_vv"]
    elif markkina_tyyppi == "Maalit":
        raja_key = f"{valittu_raja:.1f}"
        if valittu_kohde.startswith("Yli"):
            todennakoisyys = tulokset["maalit"][raja_key]["yli"]
        else:
            todennakoisyys = tulokset["maalit"][raja_key]["alle"]
    elif markkina_tyyppi == "BTTS":
        if "Kyllä" in valittu_kohde:
            todennakoisyys = tulokset["btts_kylla"]
        else:
            todennakoisyys = tulokset["btts_ei"]
    else:  # Live
        todennakoisyys = tulokset["kv"]

    rajakerroin = (1.0 / todennakoisyys) if todennakoisyys > 0 else 0.0
    ev_prosentti = (todennakoisyys * tarjottu_kerroin - 1.0) * 100.0

    with col2:
        st.markdown("#### 2. Laskennan tulokset")

        if markkina_tyyppi == "1X2":
            st.metric(
                label="Kotivoiton todennäköisyys",
                value=f"{tulokset['kv']*100:.1f}%",
                delta=f"Rajakerroin: {1/tulokset['kv']:.2f}" if tulokset["kv"] > 0 else "Rajakerroin: -",
            )
            st.metric(
                label="Tasapelin todennäköisyys",
                value=f"{tulokset['tp']*100:.1f}%",
                delta=f"Rajakerroin: {1/tulokset['tp']:.2f}" if tulokset["tp"] > 0 else "Rajakerroin: -",
            )
            st.metric(
                label="Vierasvoiton todennäköisyys",
                value=f"{tulokset['vv']*100:.1f}%",
                delta=f"Rajakerroin: {1/tulokset['vv']:.2f}" if tulokset["vv"] > 0 else "Rajakerroin: -",
            )
        elif markkina_tyyppi == "Money Line":
            st.metric(
                label="Kotivoitto ML (1) todennäköisyys (sis. JA/RL)",
                value=f"{tulokset['ml_kv']*100:.1f}%",
                delta=f"Rajakerroin: {1/tulokset['ml_kv']:.2f}" if tulokset["ml_kv"] > 0 else "Rajakerroin: -",
            )
            st.metric(
                label="Vierasvoitto ML (2) todennäköisyys (sis. JA/RL)",
                value=f"{tulokset['ml_vv']*100:.1f}%",
                delta=f"Rajakerroin: {1/tulokset['ml_vv']:.2f}" if tulokset["ml_vv"] > 0 else "Rajakerroin: -",
            )
        elif markkina_tyyppi == "Maalit":
            raja_key = f"{valittu_raja:.1f}"
            p_yli = tulokset["maalit"][raja_key]["yli"]
            p_alle = tulokset["maalit"][raja_key]["alle"]

            st.metric(
                label=f"Yli {raja_key} maalia todennäköisyys",
                value=f"{p_yli*100:.1f}%",
                delta=f"Rajakerroin: {1/p_yli:.2f}" if p_yli > 0 else "Rajakerroin: -",
            )
            st.metric(
                label=f"Alle {raja_key} maalia todennäköisyys",
                value=f"{p_alle*100:.1f}%",
                delta=f"Rajakerroin: {1/p_alle:.2f}" if p_alle > 0 else "Rajakerroin: -",
            )

            with st.expander(f"Kaikki maalirajat ({koti_xg + vieras_xg:.2f} yht. xG)"):
                for r in MAALIRAJAT:
                    rk = f"{r:.1f}"
                    py = tulokset["maalit"][rk]["yli"]
                    pa = tulokset["maalit"][rk]["alle"]
                    rk_yli = f"{1/py:.2f}" if py > 0 else "-"
                    rk_alle = f"{1/pa:.2f}" if pa > 0 else "-"
                    st.write(
                        f"**{rk}:** Yli {py*100:.1f}% (rajakerroin {rk_yli}) | "
                        f"Alle {pa*100:.1f}% (rajakerroin {rk_alle})"
                    )
        elif markkina_tyyppi == "BTTS":
            st.metric(
                label="BTTS (Kyllä) todennäköisyys",
                value=f"{tulokset['btts_kylla']*100:.1f}%",
                delta=f"Rajakerroin: {1/tulokset['btts_kylla']:.2f}" if tulokset["btts_kylla"] > 0 else "Rajakerroin: -",
            )
            st.metric(
                label="BTTS (Ei) todennäköisyys",
                value=f"{tulokset['btts_ei']*100:.1f}%",
                delta=f"Rajakerroin: {1/tulokset['btts_ei']:.2f}" if tulokset["btts_ei"] > 0 else "Rajakerroin: -",
            )
        else:  # Live
            st.metric(
                label="Live-kohdemenetelmä (1X2 xG pohjalta)",
                value=f"{tulokset['kv']*100:.1f}%",
                delta=f"Rajakerroin: {1/tulokset['kv']:.2f}" if tulokset["kv"] > 0 else "Rajakerroin: -",
            )

        st.markdown("---")
        st.write(f"🎯 Valitun kohteen todennäköisyys: **{todennakoisyys*100:.1f}%**")
        st.write(f"🏷️ Laskettu rajakerroin: **{rajakerroin:.2f}**")

        if ev_prosentti > 0:
            st.success(f"🔥 Ylikerroin löytyi! EV: **+{ev_prosentti:.1f}%**")
        else:
            st.error(f"❌ Ei ylikerrointa. EV: **{ev_prosentti:.1f}%**")

    # Tallennetaan arvot session_stateen, jotta tallennusboksi osaa lukea ne oikein
    st.session_state["calc_markkina"] = markkina_tyyppi
    st.session_state["calc_kohde"] = valittu_kohde
    st.session_state["calc_kerroin"] = tarjottu_kerroin
    st.session_state["calc_rajakerroin"] = rajakerroin
    st.session_state["calc_todennakoisyys"] = todennakoisyys


# Poisson-matriisin laskenta (Scipy + Numpy)
def laske_kaikki_todennakoisyydet(model_xg_home, model_xg_away, max_maalit=10):
    matriisi = np.outer(
        [poisson.pmf(i, model_xg_home) for i in range(max_maalit + 1)],
        [poisson.pmf(j, model_xg_away) for j in range(max_maalit + 1)],
    )

    # 1X2 todennäköisyydet
    kotivoitto = float(np.sum(np.tril(matriisi, -1)))
    tasapeli = float(np.sum(np.diag(matriisi)))
    vierasvoitto = float(np.sum(np.triu(matriisi, 1)))

    # Money Line (sis. jatkoaika / rankkarit: tasapeli jaetaan tasan)
    ml_kotivoitto = kotivoitto + 0.5 * tasapeli
    ml_vierasvoitto = vierasvoitto + 0.5 * tasapeli

    # Maalimäärät (rajat 0.5 - 6.5) ja BTTS
    maalit_tulokset = {}
    for r in MAALIRAJAT:
        p_yli = 0.0
        p_alle = 0.0
        for h in range(max_maalit + 1):
            for a in range(max_maalit + 1):
                p = float(matriisi[h, a])
                total_goals = h + a
                if total_goals > r:
                    p_yli += p
                else:
                    p_alle += p
        maalit_tulokset[f"{r:.1f}"] = {"yli": p_yli, "alle": p_alle}

    btts_kylla = 0.0
    for h in range(max_maalit + 1):
        for a in range(max_maalit + 1):
            if h > 0 and a > 0:
                btts_kylla += float(matriisi[h, a])

    btts_ei = 1.0 - btts_kylla

    return {
        "kv": kotivoitto,
        "tp": tasapeli,
        "vv": vierasvoitto,
        "ml_kv": ml_kotivoitto,
        "ml_vv": ml_vierasvoitto,
        "over_2.5": maalit_tulokset["2.5"]["yli"],
        "under_2.5": maalit_tulokset["2.5"]["alle"],
        "maalit": maalit_tulokset,
        "btts_kylla": btts_kylla,
        "btts_ei": btts_ei,
    }