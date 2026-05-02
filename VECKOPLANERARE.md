# VECKOPLANERARE.md

## Arbetsregler

- Veckoplaneraren är inte klar bara för att `veckodata.json` skapats lokalt.
- En lyckad körning ska verifiera hela kedjan:
  1. kalenderdata genererad
  2. extern skrapning försökt på angivna källor
  3. endast verkligt plausibla eventtitlar får användas
  4. `veckodata.json` publicerad till GitHub Pages om den ändrats
  5. den publika filen ska gå att läsa efter push

## Kvalitetsregel för skrapade event

- Använd inte generiska kategorier, rubriktexter eller tom-state-meddelanden som event.
- Exempel på sådant som ska filtreras bort:
  - "Festivaler"
  - "Alla Musikgenrer"
  - "Teater och underhållning"
  - malltext som `{{ event.title }}`
  - "Inga event kunde hittas"
- Om en källa inte ger verkliga event med rimlig titel ska den räknas som misslyckad eller 0 användbara träffar.
- Hellre 0 skrapade event än låtsasträffar.

## Transparens i output

- `veckodata.json` ska innehålla `scrape_debug` med källa, status och antal träffar.
- `scraped_event_count` ska visa hur många verifierade webbevent som faktiskt användes som kandidater.
- Om skrapning misslyckas ska veckoplaneraren fortfarande fungera med kalenderdata, men det ska vara tydligt att webbundretlag saknades eller var tunt.
