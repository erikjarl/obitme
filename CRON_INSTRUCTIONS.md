# Veckoplaneraren – webbkällor och cronlogik

## Mål
När veckoplaneraren körs ska den försöka hämta aktuella evenemang från webben för kommande vecka och använda dem som underlag till förslag.

## Rekommenderade webbkällor
Använd i första hand dessa publika källor om de går att läsa:

1. Visit Linköping
   - https://visitlinkoping.se/evenemang/
   - Bra för marknader, loppisar, musik, scenkonst, större familjeaktiviteter.

2. Gamla Linköping
   - https://www.gamlalinkoping.info/evenemang
   - Bra för marknader, antik/retro, familjedagar och säsongsaktiviteter.

3. Kulturkvarteret
   - https://www.kulturkvarteret.com/kalender/
   - Bra för musik, kultur och vissa familjevänliga program.

## Om källor är svårlästa
- Vissa sajter renderar events via tung JavaScript och kan vara delvis tomma i web_fetch.
- Om en källa inte går att läsa stabilt: använd den bara som svag signal eller hoppa över den.
- Hitta aldrig på specifika eventtitlar om källan inte faktiskt gav dem.

## Tillåten fallback
Om tydliga event inte kan hämtas:
- använd familjens preferenser och veckans kalenderluckor för att föreslå:
  - loppis i Linköpingstrakten
  - naturutflykt nära Rimforsa
  - lekpark / bibliotek / barnaktivitet
  - hemmaprojekt: stugan, trallen, vardagsrummet
  - återhämtning hemma

## Filtrering
Förslag ska filtreras enligt:
- område: Rimforsa, Kisa, Linköping med omnejd
- familj: två vuxna + små barn
- intressen: loppisar, natur, lekparker, barnaktiviteter, konst, musik
- veckobelastning: mycket inbokat = enklare / lugnare förslag

## Regel
Veckoplaneraren ska alltid försöka göra webbsökning/webbhämtning först och bara falla tillbaka till interna förslag om webbkällorna inte ger något användbart.
