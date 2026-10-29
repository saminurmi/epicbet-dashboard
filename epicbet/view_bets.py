import psycopg2

DB_HOST = "localhost"
DB_NAME = "vetoseurunta"
DB_USER = "saminurmi"
DB_PASSWORD = ""

def view_bets():
    try:
        connection = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = connection.cursor()

        # Haetaan kaikki vedot tietokannasta
        cursor.execute("SELECT id, match_date, league, home_team, away_team, selected_pick, odds, stake, status FROM bets ORDER BY match_date DESC;")
        bets = cursor.fetchall()

        print("\nTietokantaan tallennetut vedot:")
        print("-" * 80)
        for bet in bets:
            print(f"ID: {bet[0]} | Pvm: {bet[1].strftime('%d.%m.%Y %H:%M')} | {bet[2]}: {bet[3]} - {bet[4]} | Kohde: {bet[5]} | Kerroin: {bet[6]} | Panos: {bet[7]}€ | Status: {bet[8]}")
        print("-" * 80)

    except Exception as error:
        print(f"Virhe vetojen haussa: {error}")

    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'connection' in locals() and connection:
            connection.close()

if __name__ == "__main__":
    view_bets()