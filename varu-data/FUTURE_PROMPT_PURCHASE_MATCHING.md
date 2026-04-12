# Framtida prompt – ICA erbjudanden matchade mot Köpvanelista

Du är en expert på kodning, scraping, prisverifiering, datamodellering och robust automatisering.

## Uppdrag
Utöka den befintliga varuövervakaren så att den, utöver receptutskicket, varje vecka identifierar vilka ICA-erbjudanden som matchar hushållets Köpvanelista och publicerar en separat sammanställning till samma Discord-destination som receptutskicket använder.

## Befintlig projektkontext
- Projektmapp: `obitme/`
- Direktlänk till varuövervakaren: `https://erikjarl.github.io/obitme/varuovervakare.html`
- Beständig köpvanelista: `obitme/purchase-habits.json`

## Relevanta ICA-länkar som ska ingå
Dessa länkar är uttryckligen godkända och ska betraktas som den relevanta källuppsättningen för denna funktion:

- Kategoriöversikt: `https://handlaprivatkund.ica.se/stores/1004066/categories?source=navigation`
- Butikens grundsida: `https://handlaprivatkund.ica.se/stores/1004066`
- Sökning i butiken: `https://handlaprivatkund.ica.se/stores/1004066/search?q=...`
- Erbjudandesida: `https://www.ica.se/erbjudanden/ica-supermarket-rimforsa-1004066/`

## Mål
Varje tisdag kl. 19:00 Europe/Stockholm ska automationen:
1. hämta veckans aktuella ICA-erbjudanden från samma källor som varuövervakaren redan använder
2. läsa in `purchase-habits.json`
3. matcha erbjudanden mot Köpvanelista
4. skapa ett kort men informativt Discord-meddelande
5. spara ett resultatobjekt i repo för historik och felsökning
6. skicka meddelandet till samma server/kanal som receptutskicket

## Köpvanelista
Använd `obitme/purchase-habits.json` som beständig konfigurations- och datafil.

### Krav på modellen
- behandla listan som ett uppdaterbart objekt, inte som hårdkodad logik
- återanvänd `name`, `aliases`, `enabled`
- designa så att framtida fält som `category`, `preferredBrands`, `matchKeywords`, `notes` och `priority` kan läggas till utan omskrivning av kärnlogiken

## Krav på scraping
- återanvänd samma ICA-länkar och samma bevis-/prisstrategi som den befintliga varuövervakaren
- undersök om stabil data finns i underliggande JSON/API innan bräcklig HTML-scraping används
- extrahera minst:
  - produktnamn
  - kampanjpris
  - ordinarie pris
  - rabatt i kronor om möjligt
  - rabatt i procent om möjligt
  - källa/länk/evidence
- hantera ofullständiga prisfält gracefully

## Krav på matchning
Implementera konservativ matchning i flera steg:
1. exakt matchning
2. normaliserad matchning (casefolding, trim, svensk teckennormalisering där relevant)
3. alias-/keyword-matchning
4. försiktig fuzzy matchning med tydlig tröskel för att undvika falska positiva

Fokus: hellre missa en tveksam träff än att skicka fel vara som matchad.

## Krav på meddelandet
Discord-meddelandet ska innehålla:
- tydlig rubrik eller öppning om att veckans relevanta erbjudanden är klara
- vilka varor som matchade Köpvanelista
- ordinarie pris
- kampanjpris eller rabattupplägg
- rabatt i kronor
- rabatt i procent när säkert beräkningsbart
- gärna länk till varuövervakaren eller ICA-sidan om det passar flödet

### Policy om inga matchningar
Om inga matchningar finns ska automationen ändå skicka ett kort statusmeddelande, till exempel att inga relevanta erbjudanden hittades denna vecka. Den ska alltså inte vara tyst.

## Cron
Lägg till eller förbered en separat cron för detta utskick:
- schema: tisdagar 19:00
- tidszon: Europe/Stockholm
- tydligt namn
- återanvänd samma Discord-destination som receptutskicket
- nuvarande fungerande Discord-destination är kanal-id `1490438999494492415` (`#allmänt`) och ska användas om ingen bättre central konfiguration redan finns

## Lagring / output
Spara resultatet i repo som en egen historikpost, gärna i en separat mapp eller tydligt avgränsad struktur, så att resultat kan granskas i efterhand.

Minimikrav för outputobjekt:
- `date`
- `created_at`
- `title`
- `summary`
- `source_links`
- `matched_items`
- `message_preview`
- `discord_destination`
- `no_matches`

Varje objekt i `matched_items` bör minst innehålla:
- `habit_name`
- `matched_product_name`
- `match_type`
- `ordinary_price`
- `campaign_price`
- `discount_sek`
- `discount_percent`
- `source`
- `evidence`

## Designprinciper
- separera scraping, normalisering, matchning och formattering i olika steg
- håll lösningen testbar
- undvik onödigt många nätverksanrop
- prioritera robusthet och låg underhållskostnad
- återanvänd befintliga mönster i repoformatet
- använd fuzzy matching först efter exakt, normaliserad och alias-baserad matchning
- håll fuzzy matching konservativ för att minska falska positiva
