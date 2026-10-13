import json
import urllib.request
import streamlit as st


# Haetaan reaaliaikaiset kurssit
def hae_kurssit():
  url = "https://open.er-api.com/v6/latest/EUR"
  try:
    with urllib.request.urlopen(url) as response:
      data = json.loads(response.read().decode())
      rates = data.get("rates", {})
      return rates.get("VND", 27500), rates.get("THB", 36.5)
  except Exception:
    return 27500, 36.5


# Sivuston otsikko
st.title("💱 Matkavaluuttalaskuri")
st.write("Reaaliaikainen verkkosovellus reissubudjetin hallintaan.")

# Haetaan kurssit taustalla
vnd_kurssi, thb_kurssi = hae_kurssit()

# Sivupalkkiin kurssitiedot
st.sidebar.header("Kurssitiedot")
st.sidebar.text(f"1 € = {vnd_kurssi:,.0f} VND")
st.sidebar.text(f"1 € = {thb_kurssi:.2f} THB")

# Valikko muunnostavalle
muunnos_tapa = st.selectbox(
    "Valitse muunnossuunta:",
    [
        "Eurot (€) -> Dongit & Bahtit",
        "Vietnamin Dongit (VND) -> Eurot (€)",
        "Thaimaan Bahtit (THB) -> Eurot (€)",
    ],
)

# Syöttökenttä summalle
summa = st.number_input(
    "Syötä summa:", min_value=0.0, value=10.0, step=100.0, format="%.2f"
)

# Laskenta ja tulostus näytölle
if muunnos_tapa == "Eurot (€) -> Dongit & Bahtit":
  vnd = summa * vnd_kurssi
  thb = summa * thb_kurssi
  st.success(f"**{summa:,.2f} €** on yhteensä:")
  st.markdown(f"- **{vnd:,.0f} VND** (Dong)")
  st.markdown(f"- **{thb:,.2f} THB** (Baht)")

elif muunnos_tapa == "Vietnamin Dongit (VND) -> Eurot (€)":
  eurot = summa / vnd_kurssi
  st.success(f"**{summa:,.0f} VND** on yhteensä:")
  st.markdown(f"- **{eurot:,.2f} €**")

else:
  eurot = summa / thb_kurssi
  st.success(f"**{summa:,.2f} THB** on yhteensä:")
  st.markdown(f"- **{eurot:,.2f} €**")