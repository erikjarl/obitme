# Förbättringsprompt för framtida varuövervakare-körningar

Du är en expert på kodning, scraping och strukturerad publicering av recept- och prisinnehåll.

## Uppdrag
Skapa en veckopost för varuövervakaren baserat på ICA Supermarket Rimforsas aktuella erbjudanden.

## Mål
1. Hitta verkliga billiga erbjudanden från ICA Supermarket Rimforsa.
2. Skapa 3 billiga, nyttiga recept på svenska.
3. Recepten ska vara dimensionerade för 3 vuxna + 2 matlådor.
4. Räkna ut total kostnad och kostnad per portion.
5. Publicera resultatet i repoformat så att hemsidan kan visa det tydligt.

## Prioriteringsordning
1. Datakvalitet
2. Tydlig receptstruktur
3. Tydliga prisbevis
4. Bra frontend-data
5. Effektiv körning utan token-tunga loopar

## Viktiga förbättringar att genomföra
### A. Bättre scraping av ICA-data
- Försök först använda ICA:s butikslänk: `https://handlaprivatkund.ica.se/stores/1004066`
- Om den inte går att läsa stabilt, använd `https://www.ica.se/erbjudanden/ica-supermarket-rimforsa-1004066/`
- För varje ICA-produkt ska du försöka få fram:
  - produktnamn
  - kampanjpris
  - ordinarie pris
  - rabatt i kronor
  - tydlig källreferens
- Om ordinarie pris inte går att fastställa säkert: skriv tydligt att det är oklart eller härlett
- Gissa inte aggressivt

### B. Recepten måste se ut som riktiga recept
För varje recept ska det finnas:
- titel
- kort beskrivning
- portioner
- total tillagningstid
- ingredienslista
- varje ingrediens med tydlig mängd i gram/ml/st
- steg-för-steg-metod
- tydligt markerade ICA-erbjudanden som används

### C. Bättre prisunderlag för kompletterande ingredienser
- För ingredienser som inte köps på kampanj hos ICA: hitta i första hand faktiska svenska webbpriser
- Ange källa för dessa priser
- Markera tydligt när ett pris är:
  - exakt
  - uppskattat
  - schablon
- Minimera användning av schabloner när riktiga priser går att hitta utan onödig loopning

### D. Outputformat för frontend
Spara varje veckopost så att frontend lätt kan visa:
- fyndlista
- kampanjpris
- ordinarie pris
- rabatt
- receptkort
- ingredienser
- metod
- portionskostnad
- total kostnad
- källor

### E. Frontendvänlig struktur
Varje receptobjekt bör innehålla fält för:
- `name`
- `summary`
- `servings`
- `cook_time`
- `ica_offer_products`
- `ingredients`
- `estimated_non_ica_costs`
- `estimated_total_batch_cost_sek`
- `estimated_cost_per_portion_sek`
- `recipe.steps`
- `sources`

## Viktigt om effektivitet
- Undvik token-tunga loopar
- Gör en effektiv, begränsad scrapingpass
- Återanvänd befintlig repo-struktur
- Läs inte om gamla poster i onödan
- Uppdatera bara det som behövs

## Kvalitetskontroll före publicering
Innan du sparar posten, kontrollera:
- Har varje recept tydlig portionsstorlek?
- Har varje ingrediens tydlig mängd?
- Har ICA-produkterna kampanjpris och källa?
- Är ordinarie pris tydligt eller tydligt osäkert?
- Är portionskostnaden uträknad?
- Är outputen lätt att visa på webben?

Om svaret är nej på någon av dessa: förbättra först, publicera sedan.
