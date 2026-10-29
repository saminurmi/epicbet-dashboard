import psycopg2
from datetime import datetime

# Tietokannan asetukset
DB_HOST = "localhost"
DB_NAME = "vetoseurunta"
DB_USER = "saminurmi"
DB_PASSWORD = ""

def insert_sample_bet():
    try:
        connection = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = connection.cursor()

        # Testivedon tiedot
        insert_query = """
        INSERT INTO bets (
            match_date, league, home_team, away_team, 
            bet_market, selected_pick, odds, closing_odds, 
            stake, model_xg_home, model_xg_away, calculated_fair_odds, status
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """

        # Esimerkkidata: Liiga-ottelu, kohteena kotivoitto
        bet_data = (
            datetime(2026, 10, 28, 18, 30, 0),  # Ottelupäivä ja aika
            "Liiga",                            # Sarja
            "Kärpät",                           # Kotijoukkue
            "HIFK",                             # Vierasjoukkue
            "1X2",                              # Pelimuoto
            "Kärpät",                           # Valittu kohde
            2.10,                               # Pelattu kerroin
            2.00,                               # Päätöskerroin (CLV)
            20.00,                              # Panos (€)
            2.45,                               # Mallin xG koti
            1.80,                               # Mallin xG vieras
            1.95,                               # Mallin rajakerroin
            "PENDING"                           # Status
        )

        cursor.execute(insert_query, bet_data)
        connection.commit()
        print("Loistavaa! Testiveto lisätty onnistuneesti kantaan.")

    except Exception as error:
        print(f"Virhe vedon lisäyksessä: {error}")

    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'connection' in locals() and connection:
            connection.close()

if __name__ == "__main__":
    insert_sample_bet()