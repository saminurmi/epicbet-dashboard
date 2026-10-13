import streamlit as st

st.title("🧳 Matkan Pakkauslista & Tehtävät")
st.write(
    "Merkitse tavarat sitä mukaa kun pakkaat niitä laukkuun, ja lisää tarvittaessa"
    " uusia kohteita listalle!"
)

# Alustetaan oletuslista session stateen, jos sitä ei vielä ole
if "packing_categories" not in st.session_state:
  st.session_state.packing_categories = {
      "Dokumentit & Rahat": [
          "Passi",
          "Lentoliput & varausvahvistukset",
          "Matkavakuutuskortti",
          "Pankkikortit / luottokortit",
          "Käteistä (euroja / Thaimaan baht / Vietnamin dong)",
          "Ajokortti",
      ],
      "Elektroniikka": [
          "MacBook Pro + laturi",
          "Puhelin (iPhone) + laturi",
          "DJI Mic Mini / äänityslaitteet",
          "Varavirtalähde (Anker MagGo)",
          "Matka-adapteri",
          "Kuulokkeet",
      ],
      "Vaatteet & Kengät": [
          "T-paitoja / shortseja",
          "Pitkähihaisia / housuja (lennoille ja iltoihin)",
          "Alusvaatteet & sukat",
          "Uimahousut",
          "Kengät (lenkkarit + sandaalit)",
          "Aurinkolasit",
          "Päähine (lippis / lierihattu)",
      ],
      "Apteekki & Hygienia": [
          "Henkilökohtaiset lääkkeet",
          "Särkylääkettä (ibuprofeeni / parasetamoli)",
          "Laastareita / rakkolaastareita",
          "Hyttyskarkote",
          "Aurinkorasva",
          "Hygieniatuotteet (hammasharja, Deo jne.)",
      ],
      "Muut varusteet": [
          "Osprey Farpoint 40 (tai muu matkalaukku/reppu)",
          "Pieni päiväreppu",
          "Pyyhe (mikrokuitupyyhe)",
      ],
  }

# --- UUDEN TAVARAN LISÄYS ---
with st.expander("➕ Lisää uusi tavara tai tehtävä listaan", expanded=False):
  with st.form("add_item_form"):
    new_item_name = st.text_input("Tavaran tai tehtävän nimi (esim. Viisumi)")
    selected_category = st.selectbox(
        "Valitse kategoria", list(st.session_state.packing_categories.keys())
    )
    submit_button = st.form_submit_button(label="Lisää listaan")

    if submit_button and new_item_name:
      if new_item_name not in st.session_state.packing_categories[
          selected_category
      ]:
        st.session_state.packing_categories[selected_category].append(
            new_item_name
        )
        st.success(f"Lisätty '{new_item_name}' kategoriaan {selected_category}!")
        st.rerun()
      else:
        st.warning("Tämä tavara löytyy jo kyseisestä kategoriasta.")

st.markdown("---")

# Lasketaan kokonaismäärät
total_items = sum(
    len(items) for items in st.session_state.packing_categories.values()
)
checked_items = 0

# Käydään kategoriat ja tavarat läpi
for category, items in st.session_state.packing_categories.items():
  with st.expander(f"📁 {category} ({len(items)} kpl)", expanded=True):
    for item in items:
      is_checked = st.checkbox(item, key=f"pack_{category}_{item}")
      if is_checked:
        checked_items += 1

st.markdown("---")

# Edistymispalkki
progress = checked_items / total_items if total_items > 0 else 0
st.subheader(f"📊 Pakkaamisen edistyminen: {checked_items} / {total_items}")
st.progress(progress)

if checked_items == total_items and total_items > 0:
  st.success(
      "🎉 Kaikki pakattu! Olet valmis matkaan, ei muuta kuin kohti lentokenttää!"
  )