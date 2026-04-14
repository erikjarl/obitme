# Varuövervakare data

Här sparas veckovisa poster för varuövervakaren.

Varje post ska innehålla:
- datum
- titel
- butik/länk
- billiga fynd
- 3 recept
- övriga ingredienspriser
- portionskostnad
- sammanfattning

## Relaterad beständig konfiguration

Följande filer hör nära ihop med varuövervakaren:

- `obitme/purchase-habits.json` – hushållets uppdaterbara Köpvanelista
- `obitme/varu-data/PURCHASE_HABITS_README.md` – dokumentation för hur listan används och byggs ut
- `obitme/varu-data/FUTURE_PROMPT_PURCHASE_MATCHING.md` – expertprompt för implementation av matchning mellan ICA-erbjudanden och köpvanelistan

## Ny planerad veckofunktion

Utöver receptutskicket finns nu även underlag för en separat veckofunktion som:
- läser samma ICA-källor som receptflödet
- matchar erbjudanden mot Köpvanelista
- sammanställer relevanta fynd
- skickar resultatet till samma Discord-destination som receptutskicket
- är tänkt att köras på tisdagar kl. 19:00 Europe/Stockholm
