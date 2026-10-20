import streamlit as st
import requests

st.title("Asiakaspalvelun tikettijärjestelmä & AI")

# 1. Kentät syötteille sivun alussa
customer_email = st.text_input("Asiakkaan sähköpostiosoite", value="kaarina.levanen@gmail.com")
customer_issue = st.text_area("Kirjoita asiakkaan viesti tähän:", value="Hei, tuotteeni ei saapunut perille.")

# 2. Analysointi-painike
if st.button("Analysoi tiketti tekoälyllä"):
    # Tähän tulee analyysilogiikkasi (tai mallituloksesi)
    st.session_state["result"] = {
        "ticket_id": "TICKET-001",
        "customer_issue": customer_issue,
        "draft_reply": "Hei! Kiitos yhteydenotostasi. Olemme vastaanottaneet asian ja palaamme asiaan pian."
    }

# 3. Näytetään tulokset ja lähetysnappi vain, jos analyysi on tehty
if "result" in st.session_state:
    st.success("Analyysi valmis!")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📋 Tiketin tiedot")
        st.json(st.session_state["result"])
        
    with col2:
        st.subheader("✉️ Ehdotettu vastausluonnos")
        edited_reply = st.text_area("Muokkaa vastausta tarvittaessa:", value=st.session_state["result"]["draft_reply"])
        
        # Hyväksy & Lähetä -painike
        if st.button("Hyväksy ja lähetä asiakkaalle", key="send_email_btn"):
            with st.spinner("Lähetetään n8n-järjestelmään..."):
                try:
                    # Aiempi (testitila, vaatii n8n-napin painamisen):
                    # webhook_url = "http://localhost:5678/webhook-test/2b6636b3-2653-4963-aa44-07b51f472d0a"

                    # Uusi (suora tuotanto-osoite, toimii heti ilman n8n-naputtelua):#webhook_url = "http://localhost:5678/webhook-test/2b6636b3-2653-4963-aa44-07b51f472d0a"
                    webhook_url = "http://localhost:5678/webhook/2b6636b3-2653-4963-aa44-07b51f472d0a"
                    payload = {
                        "ticket_id": st.session_state["result"]["ticket_id"],
                        "customer_issue": st.session_state["result"]["customer_issue"],
                        "draft_reply": edited_reply,
                        "customer_email": customer_email
                    }
                    
                    response = requests.post(webhook_url, json=payload, timeout=5)
                    
                    if response.status_code == 200:
                        st.balloons()
                        st.success("Tiedot lähetetty onnistuneesti n8n-järjestelmään!")
                    else:
                        st.warning(f"Viesti meni läpi, mutta n8n palautti koodin: {response.status_code}")
                        
                except Exception as e:
                    st.error(f"Virhe käsittelyssä: {e}")