import streamlit as st
import numpy as np
from scipy.stats import poisson

def render_poisson_tab(koti_xg, vieras_xg):
    
    st.subheader("🔢 Poisson & Rajakerroin -laskuri")
    st.markdown("Ottelun maaliodottamat (xG) tulevat suoraan valitusta kohteesta. Tarkastele todennäköisyyksiä, rajakertoimia sekä odotusarvoa (EV).")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 1. Ottelun tiedot & Valinnat")
        st.write(f"⚽ Kotijoukkueen xG: **{koti_xg:.2f}**")
        st.write(f"⚽ Vierasjoukkueen xG: **{vieras_xg:.2f}**")
        
        tarjottu_kerroin = st.number_input("Epicbetin tarjoama kerroin", min_value=1.01, max_value=50.0, value=2.10, step=0.01, key="p_kerroin")
        valittu_kohde = st.selectbox("Kohde", ["Kotivoitto (1)", "Tasapeli (X)", "Vierasvoitto (2)"], key="p_kohde")

    def laske_poisson_todennakoisyydet(lam_koti, lam_vieras, max_maalit=10):
        matriisi = np.outer(
            [poisson.pmf(i, lam_koti) for i in range(max_maalit + 1)],
            [poisson.pmf(j, lam_vieras) for j in range(max_maalit + 1)]
        )
        kotivoitto = np.sum(np.tril(matriisi, -1))
        tasapeli = np.sum(np.diag(matriisi))
        vierasvoitto = np.sum(np.triu(matriisi, 1))
        return kotivoitto, tasapeli, vierasvoitto

    kv, tp, vv = laske_poisson_todennakoisyydet(koti_xg, vieras_xg)

    if "Kotivoitto" in valittu_kohde:
        todennakoisyys = kv
    elif "Tasapeli" in valittu_kohde:
        todennakoisyys = tp
    else:
        todennakoisyys = vv

    rajakerroin = 1 / todennakoisyys if todennakoisyys > 0 else 0
    ev_prosentti = (todennakoisyys * tarjottu_kerroin - 1) * 100

    with col2:
        st.markdown("#### 2. Laskennan tulokset")
        st.metric(label="Kotivoiton todennäköisyys", value=f"{kv*100:.1f}%", delta=f"Rajakerroin: {1/kv:.2f}")
        st.metric(label="Tasapelin todennäköisyys", value=f"{tp*100:.1f}%", delta=f"Rajakerroin: {1/tp:.2f}")
        st.metric(label="Vierasvoiton todennäköisyys", value=f"{vv*100:.1f}%", delta=f"Rajakerroin: {1/vv:.2f}")

        st.markdown("---")
        st.write(f"🎯 Valitun kohteen todennäköisyys: **{todennakoisyys*100:.1f}%**")
        st.write(f"🏷️ Laskettu rajakerroin: **{rajakerroin:.2f}**")

        if ev_prosentti > 0:
            st.success(f"🔥 Ylikerroin löytyi! EV: **+{ev_prosentti:.1f}%**")
        else:
            st.error(f"❌ Ei ylikerrointa. EV: **{ev_prosentti:.1f}%**")