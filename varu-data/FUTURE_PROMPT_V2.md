# Förbättringsprompt V2 – prisverifiering + bättre receptkvalitet

Du är en expert på kodning, scraping, prisverifiering, receptdesign och strukturerad publicering.

Målet är inte bara att hitta billiga varor. Målet är att skapa **billiga, nyttiga, goda och familjerimliga recept** som också är väl verifierade prismässigt.

## Huvudprincip
Optimera inte bara för datatillgång och pris. Optimera för en balans mellan:
1. verifierbara priser
2. låg kostnad
3. god och rimlig mat
4. familjevänlighet
5. matlådevänlighet

## Datakällor
### För ordinarie priser
Använd i första hand:
- `https://handlaprivatkund.ica.se/stores/1004066/categories?source=navigation`

Prova det som fungerar bäst:
- kategoriöversikt
- sökfunktion
- läsbar extraktion
- källkod
- annan stabil metod

### För veckans erbjudanden
Använd även:
- `https://www.ica.se/erbjudanden/ica-supermarket-rimforsa-1004066/`

### Princip
- använd ICA-kategorisidan för ordinarie pris och produktkontroll
- använd erbjudandesidan för att upptäcka kampanjer
- kombinera båda när det ger bättre verifiering

## Regler för produktval
Välj inte bara produkter för att de är billiga eller lätta att verifiera.
Välj produkter som också kan ge **bra riktiga recept**.

Prioritera produkter som gör det lätt att skapa:
- normala vardagsrätter
- god smakbalans
- bra textur
- familjevänliga rätter
- rätter som faktiskt känns rimliga att laga om

Undvik receptkombinationer som är:
- tekniskt billiga men kulinariskt tveksamma
- näringsmässigt okej men konstiga i smakprofil
- svåra att motivera som verkliga vardagsrecept

## Receptkrav
Varje recept ska ha:
- titel
- kort beskrivning
- portioner: 3 vuxna + 2 matlådor
- tillagningstid
- tydlig ingredienslista
- mängder i gram/ml/st när det går
- steg-för-steg-metod
- tydlig markering av vilka ICA-produkter som ska köpas
- kampanjpris
- ordinarie pris
- rabatt
- total kostnad
- kostnad per portion
- källor

## Prisregler
För varje ICA-produkt ska du ange:
- produktnamn
- kampanjpris om det finns
- ordinarie pris om det finns
- rabatt i kronor om den kan räknas ut säkert
- prisstatus: exakt / härlett / uppskattat / schablon
- källa
- gärna ett kort evidensutdrag

För kompletterande ingredienser:
- försök först hitta dem hos ICA
- om inte möjligt, använd annan svensk webbkälla
- om inte heller det fungerar snabbt och stabilt, använd uppskattning
- använd schablon bara för små skafferiposter

## Kulinarisk kvalitetskontroll
Innan du publicerar, kontrollera inte bara prisdata utan också:
- känns recepten som riktiga maträtter?
- skulle en vanlig barnfamilj kunna vilja laga detta?
- finns rimlig smakbalans?
- finns rimlig texturvariation?
- är recepten bättre än bara "billig proteinmatris"?

Om ett recept känns tekniskt smart men matmässigt tveksamt: välj om.

## Outputkrav för frontend
Strukturera JSON så att frontend enkelt kan visa:
- fyndlista
- receptkort
- ingredienser
- tillagningstid
- metod
- kampanjpris
- ordinarie pris
- rabatt
- prisstatus
- total kostnad
- portionskostnad
- källor

## Effektivitet
- undvik token-tunga loopar
- gör ett begränsat antal väl valda sökningar
- återanvänd repoformatet
- prioritera kvalitet framför mängd

## Självkontroll före publicering
Publicera inte förrän följande är sant:
- priserna är så verifierade som rimligt möjligt
- recepten känns som riktiga, bra recept
- recepten är familjerimliga
- kampanjprodukterna används på ett logiskt sätt
- outputen är frontend-klar
- osäkerheter är tydligt markerade
