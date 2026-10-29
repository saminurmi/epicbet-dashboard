import psycopg2

# Macin paikalliset asetukset
DB_HOST = "localhost"
DB_NAME = "vetoseurunta"
DB_USER = "saminurmi"  # Käytetään Macin omaa käyttäjääsi
DB_PASSWORD = ""      # Tyhjä salasana

def create_table():
    try:
        # Yhdistetään 'vetoseurunta'-tietokantaan
        connection = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = connection.cursor()

        # SQL-lauseke bets-taululle
        create_table_query = """
        CREATE TABLE IF NOT EXISTS bets (
            id SERIAL PRIMARY KEY,
            match_date TIMESTAMP WITH TIME ZONE NOT NULL,
            league VARCHAR(50) NOT NULL,
            home_team VARCHAR(100) NOT NULL,
            away_team VARCHAR(100) NOT NULL,
            bet_market VARCHAR(100) NOT NULL,
            selected_pick VARCHAR(100) NOT NULL,
            odds NUMERIC(5, 2) NOT NULL,
            closing_odds NUMERIC(5, 2),
            stake NUMERIC(6, 2) NOT NULL,
            model_xg_home NUMERIC(4, 2),
            model_xg_away NUMERIC(4, 2),
            calculated_fair_odds NUMERIC(5, 2),
            status VARCHAR(20) DEFAULT 'PENDING',
            profit_loss NUMERIC(6, 2),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        """

        cursor.execute(create_table_query)
        connection.commit()
        print("Loistavaa! Tietokantataulu 'bets' luotu onnistuneesti kantaan 'vetoseurunta'!")

    except Exception as error:
        print(f"Virhe tietokannan käsittelyssä: {error}")
    
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'connection' in locals() and connection:
            connection.close()

if __name__ == "__main__":
    create_table()