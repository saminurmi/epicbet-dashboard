import json
import urllib.request


def hae_kurssit():
    url = "https://open.er-api.com/v6/latest/EUR"
    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            rates = data.get("rates", {})
            vnd_kurssi = rates.get("VND", 27500)
            thb_kurssi = rates.get("THB", 36.5)
            return vnd_kurssi, thb_kurssi
    except Exception:
        print("Verkkoyhteyden hakeminen epäonnistui, käytetään oletuskursseja.")
        return 27500, 36.5


def main():
    print("=== MONIPUOLINEN MATKAVALUUTTALASKURI ===")
    print("Haetaan tuoreet kurssit netistä...")
    vnd_kurssi, thb_kurssi = hae_kurssit()
    print(f"Kurssit: 1 € = {vnd_kurssi:,.0f} VND | {thb_kurssi:.2f} THB")
    print("-------------------------------------------------")

    while True:
        print("\nValitse toiminto:")
        print("1: Eurot (€) -> Dongit & Bahtit")
        print("2: Vietnamin Dongit (VND) -> Eurot (€)")
        print("3: Thaimaan Bahtit (THB) -> Eurot (€)")
        print("q: Poistu ohjelmasta")

        valinta = input("\nValinta (1, 2, 3 tai q): ").strip().lower()

        if valinta in ["q", "exit", "lopeta"]:
            print("\nHeippa! Mukavaa matkaa ja turvallisia ostoksia!")
            break

        if valinta not in ["1", "2", "3"]:
            print("Virheellinen valinta! Syötä 1, 2, 3 tai q.")
            continue

        try:
            syote = input("Syötä summa: ").strip()
            summa = float(syote.replace(",", "."))

            print("\n" + "=" * 38)
            if valinta == "1":
                vnd = summa * vnd_kurssi
                thb = summa * thb_kurssi
                print(f" Eurot:      {summa:,.2f} €".replace(",", " "))
                print(f" Vietnam:    {vnd:,.0f} VND (Dong)".replace(",", " "))
                print(f" Thaimaa:    {thb:,.2f} THB (Baht)".replace(",", " "))

            elif valinta == "2":
                eurot = summa / vnd_kurssi
                print(f" Vietnam:    {summa:,.0f} VND".replace(",", " "))
                print(f" Eurot:      {eurot:,.2f} €".replace(",", " "))

            elif valinta == "3":
                eurot = summa / thb_kurssi
                print(f" Thaimaa:    {summa:,.2f} THB".replace(",", " "))
                print(f" Eurot:      {eurot:,.2f} €".replace(",", " "))

            print("=" * 38)

        except ValueError:
            print("Virhe: Syötä vain numeroita!")


if __name__ == "__main__":
    main()