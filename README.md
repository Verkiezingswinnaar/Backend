# Backend
Python backend voor [VerkiezingsWinnaar.nl](https://verkiezingswinnaar.nl/).
Deze pagina focust vooral op technische details.  
Zie de [Frontend repository](https://github.com/Verkiezingswinnaar/Frontend) voor een algemeen overzicht.

---

## Installatie-instructies
### 1. Frontend
- Clone de Frontend repository: `git clone https://github.com/Verkiezingswinnaar/Frontend.git`
- Open `constants.js` en haal de comment weg bij `export const DATA_URL = "http://localhost:63342/data.jsonl.gz"`
- Open `index.html` in een webbrowser naar keuze.

### 2. Backend
- Clone de Backend repository in een aparte folder: `git clone https://github.com/Verkiezingswinnaar/Backend.git`
- Installeer de ontbrekende Python packages: (requirements.txt volgt later)
- Start een lokale server (optioneel, voor de Frontend-data): `python -m http.server 63342`
- Voer het backend script uit: `python main_reply_elections.py`


### 3. API (optioneel)
Om `main_api.py` te draaien, moeten de variabelen `URL_API` en `URL_API_INDEX` in een `.env` bestand worden gezet.  
Deze URLs worden niet gedeeld in de repository om een DDOS te voorkomen.

---

## Berekeningen

### Prognose Gemeenteraadsverkiezingen
Voor de gemeenteraadsverkiezingen wordt de groei van een partij sinds de vorige verkiezingen als volgt berekend:

$$
\text{GroeiPrognose}_{\text{partij}} = \frac{\text{BinnengekomenStemmen}_{2026,\text{partij}}}{\text{BinnengekomenStemmen}_{2022,\text{partij}}}
$$

Waarbij:  

- $\text{BinnengekomenStemmen}_{2026,\text{partij}}$ het totaal aantal stemmen is dat **tot nu toe** is gerapporteerd door de gemeentes.  
- $\text{BinnengekomenStemmen}_{2022,\text{partij}}$ het totaal aantal stemmen is dat in 2022 in **diezelfde gemeentes** is binnengekomen.  

Gemeentes waarin een partij niet meedeed tijdens deze of de vorige verkiezing, worden overgeslagen.

### Prognose Tweede Kamerverkiezingen (bestaande partijen)
Voor de prognose voor de Tweede Kamerverkiezingen maken we de volgende aanname:

> Deed een partij mee met de vorige verkiezingen? 
> En groeit deze partij met X% in voor de gemeentes waar de resultaten **tot nu toe** van bekend zijn?
> Dan groeit deze partij ook totaal met X%.

Op basis van deze aanname wordt voor alle partijen het volgende berekend:

$$
\text{TotaalStemmen}_{\text{partij},2026} = \text{GroeiPrognose}_{\text{partij}} \cdot \text{TotaalStemmen}_{\text{partij},2022}
$$

Waarbij:  

- $\text{GroeiPrognose}_{\text{partij}}$ is gedefinieerd zoals bij de gemeenteraadsverkiezingen.  
- $\text{TotaalStemmen}_{\text{partij},2022}$ het stemmentotaal is van de vorige verkiezingen.  

Vervolgens wordt een zetelverdeling gegenereerd op basis van $\text{TotaalStemmen}_{\text{partij},2026}$ met de D’Hondt-methode.

### Prognose Tweede Kamerverkiezingen (nieuwe partijen)
Voor nieuwe partijen kunnen we geen groei ten opzichte van de vorige verkiezing definiëren.  
Daarom wordt $ \text{TotaalStemmen}_{\text{partij},2026} $ bepaald op basis van een gewogen gemiddelde van de binnengekomen stemmen en de prognose van de exit polls.  


### Accuraatheid VerkiezingsWinnaar.nl
De bovengenoemde aanpak lijkt zeer accuraat te zijn.  
Bij de Tweede Kamerverkiezingen van 2025 was de grootste afwijking tussen de prognose bij 40% van de binnengekomen resultaten en de daadwerkelijke eindresultaten ongeveer 0,4 procentpunt.  

Deze afwijking ontstond voornamelijk doordat tussentijdse resultaten van een gemeente werden meegenomen als definitieve resultaten.  
Voor de komende Tweede Kamerverkiezing corrigeert VerkiezingsWinnaar.nl hiervoor, waardoor de afwijking kleiner wordt.

---

## Openstaande issues
Momenteel neemt VerkiezingsWinnaar.nl een resultaat van een gemeente pas mee als dit resultaat definitief is.  
Hierdoor worden resultaten van grote gemeentes pas laat meegenomen in $\text{GroeiPrognose}_{\text{partij}}$.

---

## High-level overzicht code
*(Volgt later)*

---

## Verdere plannen
- Documentatie uitbreiden.  
- Refactoring main_api.py
- Replay van de gemeenteraadsverkiezingen van 2026 toevoegen.  
- Tussentijdse resultaten volledig ondersteunen.  
- Zetelschatting maken voor de landelijke verkiezingen, inclusief ondersteuning voor de D’Hondt-restzetelverdeling.  
  - Als er een grote nieuwe partij is, dan mogelijk ook de exit polls meenemen.  
- Support toevoegen voor de Provinciale Staten / Eerste Kamer.