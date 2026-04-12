# Frontendutvärdering av v4

## Vad som faktiskt gick fel
Problemet i v4 var inte bara innehållet utan främst att frontend inte längre matchade JSON-strukturen.

### Orsak
`varu.js` förväntade sig äldre fältnamn som:
- `picked_offers`
- `recipe.name`
- `recipe.ica_offer_products`
- `estimated_non_ica_costs`
- `recipe.recipe.steps`
- `estimated_total_batch_cost_sek`
- `estimated_cost_per_portion_sek`

Men v4 använder istället bland annat:
- `picked_products`
- `title`
- `description`
- `ica_offer_products_used`
- `method`
- `batch_cost_sek`
- `cost_per_portion_sek`

### Effekt på sidan
Det gjorde att sidan visade:
- `undefined`
- inga priser
- inga tydliga erbjudanden
- inget tillvägagångssätt

## Slutsats
Användaren hade rätt: den senaste versionen såg sämre ut på sidan, även om rådata i JSON egentligen var mer detaljerad.

Nästa krav måste därför vara att frontend klarar både äldre och nyare JSON-format, eller att cronjobbet hålls till ett stabilt schema.
