# VARUOVERVAKARE.md

## Syfte
Styrdokument för hur varuövervakaren ska arbeta över tid.

## Huvudmål
Skapa tydliga, användbara och frontend-kompatibla butiksposter och recept baserade på kampanjvaror.

## Övergripande regler
- Recept ska vara realistiska, användbara och kännas som riktiga måltider.
- Recept för lunch/middag ska vara mättande och innehålla tydlig proteinkälla.
- Frontend-kompatibel och giltig JSON är viktigare än kreativa men sköra speciallösningar.
- Hellre färre korrekta recept än fler tveksamma.
- Publicera aldrig halvtrasig JSON.

## Receptprinciper
- Prioritera kampanjvaror där det är rimligt.
- Komplettera med vanliga basvaror när det behövs.
- Håll recepten kostnadseffektiva.
- Prioritera medelhavsinspirerad och näringsmässigt rimlig mat där det passar.
- Inkludera grönsaker när det är naturligt.
- Ange kort och tydlig kcal/portion.
- Ange gärna uppskattad pointsnivå kortfattat, men aldrig som officiellt WW-värde.

## Dataprinciper
- Håll stabil JSON-struktur kompatibel med nuvarande frontend.
- Prisfält ska vara enkla nummer eller `null`.
- `source`-fält ska vara enkla strängar eller `null`.
- Ingrediensmängder ska ha tydliga enheter.
- Butiksvaror och ingredienslista måste stämma överens logiskt.
- Om data är osäker ska det markeras tydligt eller lämnas som `null` hellre än att hittas på.
- När textfält som `points_estimate` eller `kcal_per_portion` används för visning ska motsvarande normaliserade siffervärden också sparas när möjligt, t.ex. `points_estimate_value` och `kcal_per_portion_value`.
- Meddelanden och presentationer ska i första hand använda normaliserade värdefält; om de saknas används textfältet ordagrant eller fallback `okänt`.

## Publiceringsregler
- Skriv hela målfilen i ett steg när receptpost skapas eller skrivs om.
- Validera alltid JSON innan index uppdateras.
- Uppdatera index först efter att målfilen verifierats.
- Commit och push endast giltiga ändringar.

## Kommunikationsregler
- Discord-sammanfattningar ska vara korta, tydliga och användbara.
- iMessage-utskick ska vara ännu kortare än Discord: bara avsett slutmeddelande, utan AI-resonemang, mellanled eller förklaringar.
- För receptutskick: skriv intresseväckande men mycket kort, helst som en kort sammanhängande menytext snarare än punktlista.
- Tonen får gärna likna en restauranghovmästare som presenterar veckans meny: varm, aptitlig och kort.
- Receptmeddelandet ska ändå innehålla alla publicerade recept.
- För varje recept ska uppskattade kcal, points och portionskostnad anges i parentes direkt efter receptbeskrivningen.
- Dessa värden måste hämtas från faktisk receptdata för just den publicerade körningen, inte hittas på i efterhand.
- Om kcal, points eller portionskostnad saknas i den verkliga datan ska det stå `okänt` i stället för att gissas.
- Meddelandet ska byggas först efter att slutlig publicerad data har lästs in, så att samma data följer med till iMessage-utskicket.
- Lägg till en radbrytning sist och sedan: `Gå in på länken för att hitta recepten i sin helhet: https://erikjarl.github.io/obitme/index.html`.
- Använd index-länken, inte direktlänk till varuovervakaren.html, eftersom index.html är rätt ingång och lösenordsskyddad.
- Formuleringarna ska fokusera på att inspirera till att vilja laga receptet, inte på att förklara processen bakom.
- För köpvanelista/varumatchning: skriv superkort och koncist, bara kärnträffen eller rekommendationen.
- Inkludera gärna ett konkret receptexempel och pris per portion när det ryms utan att bli långt.
- Länka till varuövervakarsidan när relevant, men bara om det inte gör meddelandet rörigt.

## Butiksspecifika riktlinjer
### ICA
- Använd ICA Rimforsa-logiken som huvudmall för strukturen.

### Willys
- Om scraping inte blir stabilt: använd endast tydligt markerade uppskattningar och undvik att fabricera detaljer.
- Kompatibilitet med frontend går före aggressiv datainsamling.

## Ändringspolicy
Om arbetsmetoden ändras permanent ska detta dokument uppdateras, inte bara cron-prompten eller chatten.
