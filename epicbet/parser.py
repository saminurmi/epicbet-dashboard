import pdfplumber
import pandas as pd

def parse_epicbet_pdf(pdf_path):
    """
    Lukee Epicbetin tilaushistorian PDF-tiedoston ja palauttaa Pandasin DataFrame-taulukon.
    """
    data = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            # Tähän rakennetaan tarkka parsimislogiikka, 
            # kun saadaan ensimmäinen näyte PDF-tiedoston rakenteesta!
            print("Sivun tekstiä ladattu...")
            
    return pd.DataFrame(data)

if __name__ == "__main__":
    print("Parseri valmiustilassa. Odotetaan PDF-tiedostoa...")