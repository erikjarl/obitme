# Utvärdering av testkörning v4 – varuövervakare

Datum: 2026-04-12
Fil: `2026-04-12-ica-rimforsa-weekly-offers-v4.json`

## Övergripande bedömning
Den här körningen uppfyllde målen **mycket bättre vad gäller prisverifiering och datakvalitet**, men **inte lika bra vad gäller receptkvalitet och matmässig rimlighet**.

Kort sagt:
- **Tekniskt bättre**
- **Kulinariskt sämre på vissa punkter**

## Vad som uppfylldes bra
### 1. Klart bättre prisverifiering
Det här är den största förbättringen i v4.

Bra saker:
- fler ordinarie priser kommer direkt från ICA
- fler kompletterande ingredienser kommer direkt från ICA
- prisstatus markeras tydligare som exakt eller härlett
- källor är bättre och mer spårbara
- ICA-kategorisidan verkar faktiskt fungera bättre för ordinarie priser

### 2. Bättre frontend-data
JSON-strukturen är mer konsekvent och enklare att visa i frontend.

Bra saker:
- tydliga källfält
- tydliga kostnadsfält
- bättre uppdelning mellan kampanjprodukter och övriga ingredienser
- mindre beroende av lösa uppskattningar

### 3. Mindre schabloner än tidigare
Det är tydligt att den nya källstrategin hjälpte.

## Vad som brister
### 1. Receptkvaliteten föll
Det största problemet i v4 är att recepten inte alltid känns som de bästa verkliga maträtterna.

Exempel:
- tonfisk + broccoli + feta + gurka fungerar okej i pastaform, men inte självklart attraktivt
- bulgurgryta med tonfisk, kikärter, broccoli och feta är ekonomiskt rationell men känns ganska svag som vanligt recept
- modellen verkar ha optimerat mer för datatillgång och pris än för faktisk matlagningskvalitet

### 2. Recepten blev för datadrivna och för lite matdrivna
Jobbet borde optimera både:
- verifierbara priser
- bra mat

I v4 blev balanspunkten förskjuten mot prisjakt.

### 3. Allt som är billigt är inte automatiskt rätt receptval
Det behövs tydligare regler för:
- smakmässig rimlighet
- kökslogik
- familjevänlighet
- lunchlådelämplighet i praktiken

### 4. Vissa kostnadsmodeller är matematiskt rimliga men mänskligt tveksamma
Att härleda halv nätkostnad, styckkostnad eller delmängder är okej tekniskt, men recepten behöver också kännas normala att handla till.

Exempel:
- använda 0,5 kg av ett apelsinnät fungerar i teori, men kan bli konstigt i faktisk inköpslogik om resten inte används tydligt

## Slutsats
v4 är **den bästa tekniska versionen hittills** när det gäller:
- ordinarie prisdata
- ICA-källor
- frontendstruktur
- minskning av schabloner

Men den är **inte den bästa matversionen hittills**.

Nästa version bör därför optimera för:
1. fortsatt stark prisverifiering
2. tydlig källspårbarhet
3. bättre kulinarisk kvalitet
4. mer familjerimliga recept
5. bättre balans mellan prisoptimering och faktisk matglädje

## Rekommendation
Nästa prompt bör uttryckligen säga att modellen inte bara ska välja de billigaste verifierbara produkterna, utan de produkter som ger de **bästa, mest normala, goda och familjerimliga recepten** inom låg kostnad.
