import streamlit as st
import requests
from datetime import datetime

st.title("Pamelan tunnit & tarvikkeet")

with st.form("pamela_form", clear_on_submit=True):
    pvm = st.date_input("Päivämäärä", value=datetime.today())
    kohde = st.text_input("Työkohde / Selite")
    tunnit = st.number_input("Työtunnit (h)", min_value=0.0, step=0.5)
    tarvikkeet = st.text_area("Käytetyt tarvikkeet")
    kulut = st.number_input("Tarvikkeiden kulut (€)", min_value=0.0, step=1.0)
    
    submitted = st.form_submit_button("Tallenna tiedot Google Sheetsiin")
    
    if submitted:
        # Korvaa tämä n8n:n Production Webhook URL -osoitteella
        # pamela_webhook_url = "http://localhost:5678/webhook/pamela-tunnit"
        # pamela_webhook_url = "http://localhost:5678/webhook-test/2b6636b3-2653-4963-aa44-07b51f472d0a"
        pamela_webhook_url = "http://localhost:5678/webhook/e99d9047-51fd-4203-8e65-5f888f2f06fc"       
        payload = {
            "pvm": str(pvm),
            "kohde": kohde,
            "tunnit": tunnit,
            "tarvikkeet": tarvikkeet,
            "kulut": kulut
        }
        
        try:
            response = requests.post(pamela_webhook_url, json=payload)
            if response.status_code == 200:
                st.success("Tiedot tallennettu onnistuneesti taulukkoon!")
            else:
                st.error(f"Virhe lähetyksessä: {response.status_code}")
        except Exception as e:
            st.error(f"Yhteysvirhe n8n-järjestelmään: {e}")