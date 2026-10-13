import streamlit as st

st.title("📅 Matkaohjelma & Aikataulu")
st.write(
    "Tässä on alustava aikataulu ja tärkeimmät etapit joulukuun Thaimaan- ja"
    " Vietnamin-reissulle."
)

# Aikataulun tapahtumat
timeline_events = [
    {
        "pvm": "Joulukuu 2026",
        "otsikko": "Lähtö Suomesta kohti Thaimaata",
        "kuvaus": (
            "Matka alkaa! Lentomatka Bangkongiin, jossa ensimmäiset yöt ja"
            " totuttelu uusiin maisemiin."
        ),
    },
    {
        "pvm": "Joulukuu 2026 / Tammikuu 2027",
        "otsikko": "Bangkok",
        "kuvaus": (
            "Kaupunkitunnelmaa, hyvää ruokaa ja siirtyminen sopivan"
            " aikataulun mukaan eteenpäin."
        ),
    },
    {
        "pvm": "Tammi–Helmikuu 2027",
        "otsikko": "Siirtyminen Da Nangiin, Vietnam",
        "kuvaus": (
            "Lento (esim. Bangkok ➔ Da Nang, varattuna!) ja asettuminen"
            " pidemmäksi majoitusjaksoksi Da Nangiin."
        ),
    },
    {
        "pvm": "Kevät 2027",
        "otsikko": "Paluu Suomeen",
        "kuvaus": (
            "Paluu Turkuun, arkeen ja keväisiin kuvioihin (tai tarvittaessa"
            " lisäsuunnitelmat)."
        ),
    },
]

for i, event in enumerate(timeline_events, 1):
  with st.expander(f"📍 Vaihe {i}: {event['otsikko']} ({event['pvm']})"):
    st.write(event["kuvaus"])

st.markdown("---")
st.info(
    "💡 Voit muokata tai lisätä tarkempia päiviä koodin kautta sitä mukaa kun"
    " hotellit ja lennot lyödään lukkoon!"
)