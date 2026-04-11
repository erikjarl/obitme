# Utvärdering av testkörning – varuövervakare

Datum: 2026-04-11
Fil: `2026-04-11-ica-rimforsa-weekly-offers-v2.json`

## Övergripande bedömning
Testkörningen uppfyllde målen **delvis till stor del**, men inte helt perfekt.

## Vad som uppfylldes bra
- 3 recept skapades
- recepten är på svenska
- de är skrivna i relativt konventionellt receptformat
- portionsstorlek är tydlig: 3 vuxna + 2 matlådor
- tillagningstid finns angiven
- steg-för-steg-metod finns
- kampanjprodukter från ICA pekas ut tydligt
- kampanjpris, ordinarie pris och rabatt framgår för flera ICA-produkter
- portionskostnad och total kostnad räknades ut
- posten publicerades i repot och index uppdaterades

## Vad som brister eller bör förbättras
### 1. Källhänvisningarna till ICA är för grova
Det står ofta bara att källan är ICA:s erbjudandesida, men inte exakt hur informationen hittades per produkt.

**Bör förbättras till:**
- tydlig källhänvisning per produkt
- helst exakt produktsida eller tydlig produktreferens från ICA
- markera om ordinarie pris är exakt eller härlett

### 2. Några mängdangivelser är inte helt optimala
Flera ingredienser anges i burkar/förpackningar snarare än strikt gram.

**Bör förbättras till:**
- så långt möjligt gram/ml/st för varje ingrediens
- även om produkten köps i förpackning bör receptmängd anges i gram

### 3. Kompletterande prisuppgifter är fortfarande ofta schabloner
Det är tydligt markerat, vilket är bra, men målet var att i större utsträckning hitta andra priser på de varor som saknas.

**Bör förbättras till:**
- fler faktiska prisreferenser från svenska matbutiker
- färre generella uppskattningar
- tydligare markering när något är verkligt pris vs schablon

### 4. Recepten är bra men skulle kunna bli ännu mer "kokbokstydliga"
De är fullt användbara, men kan förbättras ytterligare i struktur.

**Bör förbättras till:**
- separat ingredienslista först
- därefter metod
- gärna total tillagningstid + aktiv arbetstid
- tydlig rubricering

### 5. Frontend-presenteringen är ännu inte lika rik som innehållet i JSON-filen
Postfilen innehåller mycket bra data, men hemsidan visar ännu inte hela detaljnivån fullt ut.

**Bör förbättras till:**
- visa ICA-produkt, kampanjpris, ordinarie pris, rabatt
- visa ingredienslista tydligt
- visa portionskostnad mer framträdande
- visa källor i gränssnittet

## Slutsats
Körningen var funktionell och användbar, men nästa version bör fokusera på bättre prisverifiering, striktare receptformat och bättre frontendåtergivning.
