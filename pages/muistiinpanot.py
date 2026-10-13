import streamlit as st

st.title("📝 Tärkeät Muistiinpanot & Tiedot")
st.write(
    "Tänne voit tallentaa tärkeät numerot, hotellien osoitteet ja vakuutustiedot"
    " reissun ajaksi."
)

if "notes_list" not in st.session_state:
  st.session_state.notes_list = [
      {
          "otsikko": "Matkavakuutus",
          "teksti": "Tarkista vakuutusyhtiön hätänumero ja sopimusnumero.",
      },
      {
          "otsikko": "Hotelli Bangkokissa",
          "teksti": "Osoite ja varausvahvistus esille tähän tarvittaessa.",
      },
  ]

# Uuden muistiinpanon lisäys
with st.form("add_note_form"):
  new_title = st.text_input("Otsikko (esim. Hotelli Da Nangissa)")
  new_content = st.text_area(
      "Sisältö (osoite, puhelinnumero, koodit tms.)"
  )
  submitted = st.form_submit_button("Tallenna muistiinpano")

  if submitted and new_title:
    st.session_state.notes_list.append(
        {"otsikko": new_title, "teksti": new_content}
    )
    st.success("Muistiinpano lisätty!")
    st.rerun()

st.markdown("---")

for note in st.session_state.notes_list:
  st.subheader(note["otsikko"])
  st.write(note["teksti"])
  st.markdown("---")