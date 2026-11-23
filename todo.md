# epicbet-dashboard – Kehityslista (TODO)

Päivitetty: 20.11.2026
Kassa: 113,00 € (pieniä sinkkuja, painotus +EV-kohteissa)

## 1. Money Line (ML) -markkina ja automaattinen rajakerroin
- [ ] Lisää **Money Line (ML)** omaksi vaihtoehdoksi markkinavalikkoon (`1X2`, `Money Line`, `Maalit`).
- [ ] Kun `Money Line` on valittuna, rajaa kohdevalikko vain vaihtoehtoihin **Kotivoitto ML (1)** ja **Vierasvoitto ML (2)** (piilota tai estä `Tasapeli (X)`).
- [ ] Laske jatkoajan ja rankkarit huomioiva ML-todennäköisyys ja rajakerroin suoraan Poisson-matriisista.
- [ ] Varmista, että Supabasen tallennukseen menee siististi markkina (`Money Line`), kohde ja ML-rajakerroin.

## 2. Dixon-Coles-korjaus / tasapelitodennäköisyys
- [ ] Korjaa perus-Poissonin taipumusta aliarvioida matalia maalimääriä ja varsinaisen peliajan tasapelejä jääkiekossa (Liiga & NHL).
- [ ] Lisää Dixon-Coles-tyyppinen korjaus tai kalibroitu tasapelitodennäköisyys, jotta `X`-todennäköisyys ja rajakerroin vastaavat paremmin todellista tasapelitasoa.

## 3. Maalimäärävedot (Total Goals)
- [ ] Lisää laskenta yli/alle-kokonaismaaleille suoraan maalimatriisista.
- [ ] Tue ainakin rajoja **3.5**, **4.5**, **5.5** ja **6.5** (sekä tarvittaessa push-linjat).
- [ ] Näytä todennäköisyys, rajakerroin ja `+EV`-laskenta myös maalimarkkinoille.

## 4. UI-tilan ja valintojen synkkaus
- [ ] Estä tilanteet, joissa vasemman sivupalkin todennäköisyysarvio / pika-arvio ja keskikentän markkina tai kohde jäävät eri tahtiin.
- [ ] Nollaa tai päivitä riippuvat valinnat automaattisesti, kun käyttäjä vaihtaa ottelun, markkinan tai kohteen.
- [ ] Pidä rajakerroin, `EV %` ja Kelly-suositus aina samassa tilassa ruudun eri osissa.