# Veckoplaneraren – webbkällor och cronlogik

## Mål
När veckoplaneraren körs ska den försöka hämta aktuella evenemang från webben för kommande vecka och använda dem som underlag till förslag.

## Rekommenderade webbkällor
Använd i första hand dessa publika källor om de går att läsa:

1. Visit Linköping
   - https://visitlinkoping.se/evenemang/
   - Bra för marknader, loppisar, musik, scenkonst, större familjeaktiviteter.

2. Kinda Turism – Evenemang i Kinda
   - https://evenemang.kindaturism.se/
   - Mycket relevant för Kisa, Rimforsa och övriga Kindaområdet.
   - Sidan går att nå och läsa, men eventlistan verkar delvis JS-renderad. Använd därför som stark lokal signal och använd konkreta event bara när de faktiskt går att extrahera.

3. Gamla Linköping
   - https://www.gamlalinkoping.info/evenemang
   - Bra för marknader, antik/retro, familjedagar och säsongsaktiviteter.

4. Kulturkvarteret
   - https://www.kulturkvarteret.com/kalender/
   - Bra för musik, kultur och vissa familjevänliga program.

## Extra loppis-sökning
Veckoplaneraren ska dessutom försöka hitta loppisar, bakluckeloppisar, loppmarknader och liknande evenemang i området kring:
- Rimforsa
- Kisa
- Linköping
- närliggande orter som Åtvidaberg, Mjölby, Mantorp, Vikingstad, Bestorp, Brokind och Malmslätt

### Regler för loppis-sökningen
- Använd bara offentligt tillgänglig information.
- Logga inte in på Facebook.
- Försök inte kringgå inloggning, captcha eller tekniska spärrar.
- Om ett Facebook-event inte kan läsas utan inloggning: hoppa över det eller använd endast det som syns publikt.
- Prioritera öppna källor: kommuners evenemangskalendrar, lokala föreningar, marknadssidor, Eventbrite/Billetto samt publika Facebook-event.
- Spara alltid käll-länk när en träff används.

### Sökfraser att använda som vägledning
- "loppis Linköping helgen"
- "bakluckeloppis Linköping"
- "loppmarknad Linköping"
- "loppis Rimforsa"
- "loppis Kisa"
- "loppis Åtvidaberg"
- "loppis Mjölby"
- "loppis Östergötland helgen"
- "site.com/events loppis Linköping"
- "site.com/events loppis Östergötland"
- "bakluckeloppis Östergötland"

### Extrahera helst dessa fält
- titel
- datum
- tid
- plats
- kommun
- arrangör
- kort_beskrivning
- källa_url
- säkerhet (hög/medel/låg)

### Filtrera bort
- permanenta second hand-butiker utan specifikt event
- gamla event
- event utan datum
- dubbletter

### Sortering
- kommande datum först
- närmast Rimforsa/Kisa/Linköping först
- högst säkerhet först

### Om inga säkra loppisar hittas
- skriv att inga säkra aktuella loppisar hittades
- lista eventuella osäkra träffar separat
- använd sedan bara de träffar som faktiskt är tillräckligt relevanta för veckoplaneraren

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

## iMessage-format
När veckoplaneraren skickar iMessage ska texten vara extra kort och mobilvänlig:
- max ungefär 350 tecken före länken
- nämn bara 2-3 viktigaste hållpunkterna
- nämn högst 1-2 förslag
- välj bort överflödiga detaljer, klockslag och upprepningar om texten blir lång
- skriv hellre en elegant sammanfattning än en full genomgång
- avsluta alltid med två radbrytningar och sedan exakt:
  `Gå in på Veckoplaneraren här: https://erikjarl.github.io/obitme/index.html`
