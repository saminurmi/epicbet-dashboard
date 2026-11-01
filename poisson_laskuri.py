import numpy as np
import streamlit as st
from scipy.stats import poisson


def render_poisson_tab(koti_xg, vieras_xg):

  st.subheader("🔢 Poisson & Rajakerroin -laskuri")
  st.markdown(
      "Ottelun maaliodottamat (xG) tulevat suoraan valitusta kohteesta."
      " Tarkastele todennäköisyyksiä, rajakertoimia sekä odotusarvoa (EV)."
  )

  col1, col2 = st.columns(2)

  with col1:
    st.markdown("#### 1. Ottelun tiedot & Valinnat")
    st.write(f"⚽ Kotijoukkueen xG: **{koti_xg:.2f}**")
    st.write(f"⚽ Vierasjoukkueen xG: **{vieras_xg:.2f}**")

    # Markkinan valinta (1X2 tai maalimäärät / BTTS)
    markkina_tyyppi = st.selectbox(
        "Valitse markkina",
        ["1X2 (Voittaja)", "Yli/Alle 2.5 maalia", "BTTS (Molemmat tekevät)"],
        key="p_markkina_tyyppi",
    )

    tarjottu_kerroin = st.number_input(
        "Epicbetin tarjoama kerroin",
        min_value=1.01,
        max_value=50.0,
        value=2.10,
        step=0.01,
        key="p_kerroin",
    )

    # Kohdevalinta riippuu siitä, mitä markkinaa tarkastellaan
    if markkina_tyyppi == "1X2 (Voittaja)":
      valittu_kohde = st.selectbox(
          "Kohde",
          ["Kotivoitto (1)", "Tasapeli (X)", "Vierasvoitto (2)"],
          key="p_kohde_1x2",
      )
    elif markkina_tyyppi == "Yli/Alle 2.5 maalia":
      valittu_kohde = st.selectbox(
          "Kohde", ["Yli 2.5 maalia", "Alle 2.5 maalia"], key="p_kohde_ou"
      )
    else:
      valittu_kohde = st.selectbox(
          "Kohde", ["BTTS Kyllä", "BTTS Ei"], key="p_kohde_btts"
      )

  tulokset = laske_kaikki_todennakoisyydet(koti_xg, vieras_xg)

  # Valitaan tarkasteltava todennäköisyys käyttäjän valinnan mukaan
  if markkina_tyyppi == "1X2 (Voittaja)":
    if "Kotivoitto" in valittu_kohde:
      todennakoisyys = tulokset["kv"]
    elif "Tasapeli" in valittu_kohde:
      todennakoisyys = tulokset["tp"]
    else:
      todennakoisyys = tulokset["vv"]
  elif markkina_tyyppi == "Yli/Alle 2.5 maalia":
    if "Yli" in valittu_kohde:
      todennakoisyys = tulokset["over_2.5"]
    else:
      todennakoisyys = tulokset["under_2.5"]
  else:
    if "Kyllä" in valittu_kohde:
      todennakoisyys = tulokset["btts_kylla"]
    else:
      todennakoisyys = tulokset["btts_ei"]

  rajakerroin = 1 / todennakoisyys if todennakoisyys > 0 else 0
  ev_prosentti = (todennakoisyys * tarjottu_kerroin - 1) * 100

  with col2:
    st.markdown("#### 2. Laskennan tulokset")

    if markkina_tyyppi == "1X2 (Voittaja)":
      st.metric(
          label="Kotivoiton todennäköisyys",
          value=f"{tulokset['kv']*100:.1f}%",
          delta=f"Rajakerroin: {1/tulokset['kv']:.2f}",
      )
      st.metric(
          label="Tasapelin todennäköisyys",
          value=f"{tulokset['tp']*100:.1f}%",
          delta=f"Rajakerroin: {1/tulokset['tp']:.2f}",
      )
      st.metric(
          label="Vierasvoiton todennäköisyys",
          value=f"{tulokset['vv']*100:.1f}%",
          delta=f"Rajakerroin: {1/tulokset['vv']:.2f}",
      )
    elif markkina_tyyppi == "Yli/Alle 2.5 maalia":
      st.metric(
          label="Yli 2.5 maalia todennäköisyys",
          value=f"{tulokset['over_2.5']*100:.1f}%",
          delta=f"Rajakerroin: {1/tulokset['over_2.5']:.2f}",
      )
      st.metric(
          label="Alle 2.5 maalia todennäköisyys",
          value=f"{tulokset['under_2.5']*100:.1f}%",
          delta=f"Rajakerroin: {1/tulokset['under_2.5']:.2f}",
      )
    else:
      st.metric(
          label="BTTS (Kyllä) todennäköisyys",
          value=f"{tulokset['btts_kylla']*100:.1f}%",
          delta=f"Rajakerroin: {1/tulokset['btts_kylla']:.2f}",
      )
      st.metric(
          label="BTTS (Ei) todennäköisyys",
          value=f"{tulokset['btts_ei']*100:.1f}%",
          delta=f"Rajakerroin: {1/tulokset['btts_ei']:.2f}",
      )

    st.markdown("---")
    st.write(f"🎯 Valitun kohteen todennäköisyys: **{todennakoisyys*100:.1f}%**")
    st.write(f"🏷️ Laskettu rajakerroin: **{rajakerroin:.2f}**")

    if ev_prosentti > 0:
      st.success(f"🔥 Ylikerroin löytyi! EV: **+{ev_prosentti:.1f}%**")
    else:
      st.error(f"❌ Ei ylikerrointa. EV: **{ev_prosentti:.1f}%**")


# Poisson-matriisin laskenta (Scipy + Numpy)
def laske_kaikki_todennakoisyydet(model_xg_home, model_xg_away, max_maalit=10):
  matriisi = np.outer(
      [poisson.pmf(i, model_xg_home) for i in range(max_maalit + 1)],
      [poisson.pmf(j, model_xg_away) for j in range(max_maalit + 1)],
  )

  # 1X2 todennäköisyydet
  kotivoitto = np.sum(np.tril(matriisi, -1))
  tasapeli = np.sum(np.diag(matriisi))
  vierasvoitto = np.sum(np.triu(matriisi, 1))

  # Maalimäärät ja BTTS
  over_25 = 0.0
  under_25 = 0.0
  btts_kylla = 0.0

  for h in range(max_maalit + 1):
    for a in range(max_maalit + 1):
      p = matriisi[h, a]
      total_goals = h + a

      if total_goals > 2.5:
        over_25 += p
      else:
        under_25 += p

      if h > 0 and a > 0:
        btts_kylla += p

  btts_ei = 1.0 - btts_kylla

  return {
      "kv": kotivoitto,
      "tp": tasapeli,
      "vv": vierasvoitto,
      "over_2.5": over_25,
      "under_2.5": under_25,
      "btts_kylla": btts_kylla,
      "btts_ei": btts_ei,
  }