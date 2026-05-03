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

## Långsiktig urvalsmodell

- Nya skrapkällor ska normaliseras till samma eventformat: `title`, `source`, `area`, `url`, `date_hint`, `location`, `tags`.
- Urvalet ska inte hårdkodas per enskild sida längre än nödvändigt; källor får gärna vara olika, men matchningen mot familjen ska vara gemensam.
- Varje event ska få en `family_match_score` baserat på familjens intressen, geografi, barnvänlighet, tydlighet och konkret datum/info.
- Specifika event med tydlig titel, datum och länk ska prioriteras över generiska kategorisidor.
- Generiska rubriker och samlingsetiketter ska få så låg poäng eller filtreras bort så att de inte vinner över riktiga event.
- Veckans förslag ska i första hand använda de högst rankade verkliga eventen, och först därefter fylla ut med generiska familjeförslag om webbundretlag saknas.
