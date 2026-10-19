# Backend
Python backend voor [VerkiezingsWinnaar.nl](https://verkiezingswinnaar.nl/).
Deze pagina focust vooral op technische details.  
Zie de [Frontend repository](https://github.com/Verkiezingswinnaar/Frontend) voor een algemeen overzicht.

## Installatie-instructies
### 1. Frontend
- Clone de Frontend repository: `git clone https://github.com/Verkiezingswinnaar/Frontend.git`
- Stel `VITE_ELECTION_DATA_BASE_URL` in op de openbare R2-bucket-root; lokaal is dat `/election-assets/`.
- Start de frontend met `pnpm dev`.

### 2. Backend
- Clone de Backend repository in een aparte folder: `git clone https://github.com/Verkiezingswinnaar/Backend.git`
- Installeer [uv](https://docs.astral.sh/uv/) en voer in de backendmap `uv sync` uit om Python en de dependencies uit `pyproject.toml` te installeren.
- Start een lokale server via PowerShell: `uv run python -m http.server 63343`
- Start de API-verwerking met `uv run python main_api.py`.


## Verkiezingsbestanden

`active-elections.json` bevat alleen de actieve `current`- en `previous`-ID's.
De volledige uitslagen staan per verkiezing in `results-{ID}.json`; de live
feed wordt `data-{current-ID}.jsonl.gz`. Bij een nieuwe verkiezing wijzig je de
twee ID's en voeg je het resultatenbestand toe. Zet provider-URL's in `.env`
als `URL_API_{ID}` en `URL_API_INDEX_{ID}`. Naam, label en type (municipal,
provincial, national of other) staan bij de resultaten.

### 3. API (optioneel)
Om `main_api.py` te draaien, moeten `URL_API_{ID}` en `URL_API_INDEX_{ID}` in `.env` worden gezet, voor de current election ID.
Deze URLs worden niet gedeeld in de repository om een DDOS te voorkomen.

### 4. Cloudflare R2 (publiceren)
De Standard-bucket `verkiezingswinnaar` bevat de publieke `active-elections.json`,
resultatenbestanden en per-verkiezing feeds. De frontend haalt de actieve IDs op
en leest `data-{current-ID}.jsonl.gz` en `results-{previous-ID}.json` uit R2.
De backend publiceert bestanden via de upload-Worker in [`upload-worker/`](upload-worker/README.md).
Configureer dezelfde willekeurige geheime waarde als Worker-secret `FEED_WRITE_TOKEN`
en als `CLOUDFLARE_R2_WRITE_TOKEN` in `.env`. Dit is geen Cloudflare API-token.

```dotenv
CLOUDFLARE_R2_UPLOAD_BASE_URL=https://verkiezingswinnaar-r2-upload.verkiezingswinnaar-feed.workers.dev
CLOUDFLARE_R2_WRITE_TOKEN=...
RUN_R2_INTEGRATION=1 # alleen wanneer je de live uploadtest bewust draait
```

De publieke URL is een Cloudflare-managed `r2.dev`-adres. Cloudflare geeft aan dat deze URL bedoeld is voor niet-productieverkeer en variabele rate limits heeft. Voor productie kun je later een eigen domein toevoegen aan Cloudflare en als R2 custom domain koppelen.

De upload-Worker accepteert geauthenticeerde `PUT`-requests voor verkiezingsinstellingen, per-verkiezing resultaten en feeds, en een apart replay-testobject. Cloudflare Workers Free heeft daarnaast een accountbrede limiet van 100.000 Worker-requests per dag. Rechtstreekse frontend-reads uit R2 tellen niet als requests naar deze Worker, maar tellen wel mee voor R2-reads. De R2 Standard-vrije bundel omvat 10 GB-maand opslag, 1 miljoen Class A- en 10 miljoen Class B-operaties per maand; internet-egress is gratis. Zie [R2-public buckets](https://developers.cloudflare.com/r2/buckets/public-buckets/), [R2-prijzen](https://developers.cloudflare.com/r2/pricing/) en [Workers-limieten](https://developers.cloudflare.com/workers/platform/limits/).

`VITE_ELECTION_DATA_BASE_URL` points to the public R2 bucket root; locally it is `/election-assets/`.

### Frontend-test replay

Gebruik `uv run python main_replay_elections_test.py local` om een bestand uit `testdata/` te replayen. Standaard gebruikt het script `GR2026-03-17.jsonl`, schrijft naar `data-TK2025.jsonl.gz` en wacht vier seconden tussen snapshots. Start ook `uv run python -m http.server 63343` vanuit deze map; Vite proxy't instellingen, resultaten en feed.

Voor een R2-test: configureer `CLOUDFLARE_R2_TEST_UPLOAD_URL` met een HTTPS-Worker-URL die eindigt op `/data-test.jsonl.gz` en configureer `CLOUDFLARE_R2_WRITE_TOKEN`. Start daarna `uv run python main_replay_elections_test.py r2`. Deze modus schrijft alleen de aparte testobject-key. Gebruik voor de frontend een testbucket met bijbehorende actieve instellingen en resultaten als `VITE_ELECTION_DATA_BASE_URL`.

Een opt-in integratietest `tests/test_r2_public_feed.py` uploadt de feed van het actieve election ID via de upload-Worker en haalt die op via de openbare R2-URL. Configureer de `CLOUDFLARE_R2_*`-waarden en `RUN_R2_INTEGRATION=1` in `.env` om de test bewust uit te voeren. De test overschrijft de actieve publieke feed.

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
Daarom wordt $\text{TotaalStemmen}_{\text{partij},2026}$ bepaald op basis van een gewogen gemiddelde van de binnengekomen stemmen en de prognose van de exit polls.  


### Accuraatheid VerkiezingsWinnaar.nl
De bovengenoemde aanpak lijkt zeer accuraat te zijn.  
Bij de Tweede Kamerverkiezingen van 2025 was de grootste afwijking tussen de prognose bij 40% van de binnengekomen resultaten en de daadwerkelijke eindresultaten ongeveer 0,4 procentpunt.  

Deze afwijking ontstond voornamelijk doordat tussentijdse resultaten van een gemeente werden meegenomen als definitieve resultaten.  
Voor de komende Tweede Kamerverkiezing corrigeert VerkiezingsWinnaar.nl hiervoor, waardoor de afwijking kleiner wordt.

## Openstaande issues
Momenteel neemt VerkiezingsWinnaar.nl een resultaat van een gemeente pas mee als dit resultaat definitief is.  
Hierdoor worden resultaten van grote gemeentes pas laat meegenomen in $\text{GroeiPrognose}_{\text{partij}}$.

## High-level overzicht code

- `main_api.py` haalt uitslagen voor partijen en gemeenten op, berekent per partij de totalen en maakt een snapshot. Nieuwe snapshots worden lokaal opgeslagen als JSON/JSONL, gecomprimeerd en naar Cloudflare R2 geüpload.
- `snapshot.py` berekent prognoses en serialiseert de hoofdstructuur van een snapshot.
- `party_snapshot.py` bevat de cijfers en serialisatie per partij.
- `party.py`, `party_constants.py` en `config.py` bevatten partijgegevens, historische stemmen, drempelwaarden en configuratie uit de omgeving.
- `file.py` verzorgt lokale bestanden, gzip-compressie en Cloudflare R2-upload.
- `main_replay_elections.py` verwerkt opgeslagen JSONL-resultaten opnieuw. De mappen `replay/` en `testdata/` bevatten respectievelijk bewaarde verkiezingsdata en synthetische ontwikkeldata.
- `main_api.py` is de huidige route voor het ophalen van uitslagen.

Voor AI-assistenten en bijdragers staan de projectafspraken, rekenregels en veilige ontwikkelworkflow in [`AGENTS.md`](AGENTS.md).

## Verdere plannen
- Documentatie uitbreiden.  
- Refactoring main_api.py
- Replay van de gemeenteraadsverkiezingen van 2026 toevoegen.  
- Tussentijdse resultaten van gemeentes volledig ondersteunen.  
- Zetelschatting maken voor de landelijke verkiezingen, inclusief ondersteuning voor de D’Hondt-restzetelverdeling.  
  - Als er een grote nieuwe partij is, dan ook de exit polls meenemen.  
- Support toevoegen voor de Provinciale Staten / Eerste Kamer.
