import streamlit as st

# Sivuston asetukset
st.set_page_config(
    page_title="Samin Matkakojelauta", page_icon="✈️", layout="wide"
)

st.title("✈️ Matkakojelauta: Aasia (Joulukuu 2026)")
st.write(
    "TripIt-tiedoista poimitut lennot, hotellit ja siirtymät yhdessä"
    " paikassa."
)

# Ylätason nostot
col1, col2, col3 = st.columns(3)
col1.metric("Kohde", "Bangkok & Da Nang", "6. joulu – 8. joulu 2026")
col2.metric("Matkatila", "Valmiina reissuun", "Osprey Farpoint 40l")
col3.metric("Valuutta", "THB & VND / EUR", "Reaaliajassa")

st.divider()

# Välilehdet
tab1, tab2, tab3 = st.tabs(
    ["🏨 Majoitukset & Siirtymät", "✈️ Lentotiedot", "🎒 Muistilista & Vinkit"]
)

with tab1:
  st.header("Hotellit ja lentokenttäsiirtymät")

  # Bangkok
  with st.expander("🇹🇭 Bangkok: Queensland Hotel (4.12. – 6.12.2026)", expanded=True):
    st.markdown("### Queensland Hotel")
    st.write(
        "**Osoite:** QG4Q+MFJ, Thanon Phaya Thai, Ratchathewi, Bangkok 10400,"
        " Thailand"
    )
    st.write("**Varausnumero / Vahvistus:** `6578768087` (Booking.com)")
    st.write("**Puhelin:** 02 080 7777")
    st.markdown(
        "**Verkkosivut:**"
        " [Queensland"
        " Hotel](https://www.queenslandhotelbangkok.com/)"
    )

    st.info("🚗 **Miten lentokentältä pääsee (Suvarnabhumi BKK):**")
    st.markdown(
        "- **Taksi:** Virallinen taksi saapumisaulan ulkopuolelta (Public"
        " Taxi). Matka kestää noin 30–45 min ruuhkasta riippuen. Varaa käteistä"
        " mukaan tullimaksuja ja kyytiä varten."
    )
    st.markdown(
        "- **Juna:** Airport Rail Link -juna city-linjalla Makkasaniin, josta"
        " loppumatka taksilla tai MRT:llä."
    )

  # Da Nang
  with st.expander("🇻🇳 Da Nang: Elites Hotel (6.12. – 8.12.2026+)"):
    st.markdown("### Elites Hotel")
    st.write("**Osoite:** 187 Hồ Nghinh, An Hải, Đà Nẵng 550000, Vietnam")
    st.write("**Puhelin:** +84 777 971 278")
    st.markdown(
        "**Verkkosivut:** [Elites Hotel](https://eliteshoteldanang.com/)"
    )

    st.info("🚗 **Miten lentokentältä pääsee (Da Nang DAD):**")
    st.markdown(
        "- **Sijainti:** Da Nangin lentokentältä on ranta-alueelle hyvin lyhyt"
        " matka – taksimatka kestää vain noin 10–15 minuuttia."
    )
    st.markdown(
        "- **Grab-sovellus:** Käytä puhelimessa **Grab**-sovellusta (Kaakkois-Aasian"
        " vastine Uberille). Hinta on kiinteä ja näkyy suoraan sovelluksessa,"
        " eikä hinnoista tarvitse neuvotella."
    )

with tab2:
  st.header("Lentotiedot")

  st.markdown("### 🛫 Menolento: ARN ➔ BKK")
  st.write("**Päivämäärä:** Torstai, 3. joulukuuta 2026")
  st.write("**Lento:** ARN (Tukholma) klo 10:30 ➔ BKK (Bangkok) klo 04:00 (+1pv)")
  st.write("**Lentonumero:** NO 193 | **Vahvistus:** `XZ934B`")
  st.write("**Kesto:** 11h 30min (Nonstop) | **Kone:** Boeing 787-9")
  st.write("**Hinta:** €412.49 (Varattu 2.7.2026)")

  st.divider()

  st.markdown("### 🛫 Jatkolento: BKK ➔ DAD")
  st.write("**Päivämäärä:** Sunnuntai, 6. joulukuuta 2026")
  st.write("**Lähtö:** Bangkok (BKK) klo 12:15")
  st.write("**Saapuminen:** Da Nang (DAD) klo 13:55")
  st.write(
      "**Kesto:** 1h 40min | **Välityspalvelu:** Flightnetwork"
  )

with tab3:
  st.header("Tärkeät muistettavat ja vinkit")
  st.checkbox("Passin voimassaolo tarkistettu")
  st.checkbox("Matkavakuutus voimassa")
  st.checkbox("Osprey Farpoint 40l pakattu")
  st.checkbox("Hotellien varausvahvistukset mukana")

  st.divider()

  st.subheader("💰 Parhaat rahanvaihtopaikat (Paras kurssi)")

  st.success("🇹🇭 **Bangkok (THB):**")
  st.markdown(
      "- Etsi **SuperRich** (vihreä tai oranssi). Tarjoavat kaupungin parhaat"
      " kurssit."
  )
  st.markdown(
      "- **Kentällä:** Suvarnabhumin kentän alimmassa kerroksessa (B-taso, junan"
      " vieressä) on SuperRichin luukku, josta saa paremman kurssin kuin"
      " yleisistä vaihtopisteistä."
  )

  st.success("🇻🇳 **Da Nang (VND):**")
  st.markdown(
      "- Parhaat kurssit saa paikallisista **kultaliikkeistä** (esim. Han Marketin"
      " ympärillä Nguyen Thai Hoc -kadulla, kuten *Hùng Bống*)."
  )
  st.markdown(
      "- Ota mukaan **siistejä, sileitä isoja euroseteleitä** (50 € / 100 €),"
      " niistä saa paremman kurssin ilman pankkikuluja."
  )