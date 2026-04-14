# Köpvanelista / purchase-habits.json

Denna fil är projektets beständiga data för hushållets återkommande köpbehov.

## Fil
- `obitme/purchase-habits.json`

## Syfte
Listan används för att matcha veckans ICA-erbjudanden mot sådant hushållet ofta köper.

## Struktur
Exempel:

```json
{
  "name": "Köpvanelista",
  "version": 1,
  "updatedAt": "2026-04-12T15:38:00+02:00",
  "items": [
    { "name": "Pasta", "aliases": [], "enabled": true }
  ]
}
```

## Regler
- Lägg nya återkommande behov i `items`
- Sätt `enabled: false` om en vara ska pausas utan att raderas
- Lägg till `aliases` när ICA brukar skriva produkten på annat sätt
- Filen ska betraktas som konfiguration/data, inte som hårdkodad logik

## Framtida utbyggnad
Objekten kan senare utökas med fält som:
- `category`
- `preferredBrands`
- `matchKeywords`
- `notes`
- `priority`

## Relevanta ICA-källor för funktionen
Följande länkar ska användas som projektets godkända ICA-källor för erbjudande- och produktmatchning:

- `https://handlaprivatkund.ica.se/stores/1004066/categories?source=navigation`
- `https://handlaprivatkund.ica.se/stores/1004066`
- `https://handlaprivatkund.ica.se/stores/1004066/search?q=...`
- `https://www.ica.se/erbjudanden/ica-supermarket-rimforsa-1004066/`

## Matchningsprincip
När erbjudanden matchas bör logiken arbeta i flera steg:
1. exakt namnmatchning
2. normaliserad strängmatchning
3. alias-/keyword-matchning
4. försiktig fuzzy matchning
