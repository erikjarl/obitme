# Kaloriuppskattning per portion – Tillägg till varuövervakaren

## Mål
Lägg till realistisk kaloriuppskattning per portion i varje recept som genereras av varuövervakarens automatiska körningar.

## Krav
- **Realistiska uppskattningar**: Baserat på ingredienser och mängder
- **Spann istället för exakta värden**: T.ex. "450–550 kcal" eller "ca 500 kcal"
- **Ingår i varje cron-körning**: Automatisk beräkning när recept genereras
- **Lagras i JSON-utdata**: Spara som del av receptobjektet
- **Visa i frontend**: Inkludera i renderingen på varuövervakaren.html

## Datastruktur
Lägg till följande fält i varje receptobjekt:

```json
{
  "nutrition_estimates": {
    "calories_per_portion": {
      "estimate_kcal": 500,
      "range_kcal": [450, 550],
      "confidence": "medium",
      "method": "ingredient_sum_estimation"
    },
    "macronutrients": {
      "protein_g": "25–35",
      "carbs_g": "45–60", 
      "fat_g": "15–25"
    }
  }
}
```

## Beräkningsmetodik

### 1. Ingrediensbaserad summering
För varje ingrediens i `recipe.ingredients`:
- Identifiera huvudkomponent (kött, grönsak, spannmål, etc.)
- Uppskatta kaloritäthet baserat på typ:
  - **Kött/fisk**: 150–250 kcal/100g (kycklingfilé ~165 kcal, lax ~200 kcal)
  - **Grönsaker**: 20–50 kcal/100g (tomat ~20 kcal, potatis ~80 kcal)
  - **Spannmål/pasta/ris**: 130–150 kcal/100g torrvara, 350–400 kcal/100g tillagad
  - **Ost**: 300–400 kcal/100g
  - **Olja/fett**: 900 kcal/100g
  - **Mjölkprodukter**: 40–60 kcal/100g (yoghurt), 350–400 kcal/100g (grädde)

### 2. Portionsjustering
- Dela totala kalorier med `recipe.servings` (vanligtvis 4–5 portioner)
- Justera för tillagningsförluster/vinst (vattenavdunstning, fettabsorbtion)

### 3. Spannberäkning
- Ange ±10–15% spann för osäkerhet
- Exempel: 500 kcal ± 50 kcal → "450–550 kcal"

### 4. Konfidensnivåer
- **high**: Alla huvudingredienser har tydliga mängder och kända kalorivärden
- **medium**: Vissa ingredienser uppskattas eller är små mängder
- **low**: Många uppskattningar eller komplexa rätter

## Implementationssteg

### Steg 1: Kaloridatabas (enkel)
Skapa en referensfil med typiska kalorivärden:

```json
{
  "calorie_reference": {
    "kyckling": {"kcal_per_100g": 165, "range": [150, 180]},
    "lax": {"kcal_per_100g": 200, "range": [180, 220]},
    "nötfärs": {"kcal_per_100g": 250, "range": [230, 270]},
    "pasta": {"kcal_per_100g": 130, "range": [120, 140], "note": "torrvara"},
    "ris": {"kcal_per_100g": 130, "range": [125, 135], "note": "torrvara"},
    "tomat": {"kcal_per_100g": 20, "range": [18, 25]},
    "lök": {"kcal_per_100g": 40, "range": [35, 45]},
    "morot": {"kcal_per_100g": 40, "range": [35, 45]},
    "ost": {"kcal_per_100g": 350, "range": [300, 400]},
    "smör": {"kcal_per_100g": 720, "range": [700, 740]},
    "olivolja": {"kcal_per_100g": 900, "range": [880, 920]},
    "rapsolja": {"kcal_per_100g": 900, "range": [880, 920]},
    "yoghurt": {"kcal_per_100g": 50, "range": [40, 60]},
    "grädde": {"kcal_per_100g": 350, "range": [340, 360]}
  }
}
```

### Steg 2: Matchningslogik
För varje ingrediens `item.item`:
- Normalisera namn (lowercase, ta bort märken, förpackningsstorlek)
- Matcha mot kaloridatabas med fuzzy matching
- Om ingen exakt match: klassificera i bred kategori (kött, grönsak, etc.)

### Steg 3: Beräkningsfunktion
```javascript
function estimateCalories(recipe) {
  const ingredients = recipe.ingredients || [];
  let totalKcal = 0;
  let totalRange = [0, 0];
  
  for (const ing of ingredients) {
    const match = findCalorieMatch(ing.item);
    if (match) {
      // Konvertera mängd till gram om nödvändigt
      const grams = convertToGrams(ing.amount, ing.unit);
      const kcal = (grams / 100) * match.kcal_per_100g;
      const rangeMin = (grams / 100) * match.range[0];
      const rangeMax = (grams / 100) * match.range[1];
      
      totalKcal += kcal;
      totalRange[0] += rangeMin;
      totalRange[1] += rangeMax;
    }
  }
  
  // Dela med antal portioner
  const servings = recipe.servings || 4;
  const perPortion = totalKcal / servings;
  const perPortionRange = [totalRange[0] / servings, totalRange[1] / servings];
  
  // Lägg till 10% osäkerhet för tillagning
  const uncertainty = perPortion * 0.1;
  const finalRange = [
    Math.round(perPortionRange[0] - uncertainty),
    Math.round(perPortionRange[1] + uncertainty)
  ];
  
  return {
    estimate_kcal: Math.round(perPortion),
    range_kcal: finalRange,
    confidence: determineConfidence(ingredients),
    method: "ingredient_sum_estimation"
  };
}
```

### Steg 4: Makronäringsuppskattning (valfritt)
Baserat på rätttyp:
- **Köttbaserade rätter**: Högre protein (25–40g), måttligt fett (15–25g)
- **Pastarätter**: Högre kolhydrater (50–70g), måttligt protein (15–25g)
- **Vegetariska**: Balanserat, ofta högre kolhydrater

## Integration med befintlig kod

### I cron-körningen:
1. När recept genereras, kör `estimateCalories(recipe)`
2. Spara resultatet i `recipe.nutrition_estimates`
3. Inkludera i JSON-utdata

### I frontend-rendering (`varu.js`):
```javascript
function renderNutrition(estimates) {
  if (!estimates) return '';
  const { calories_per_portion } = estimates;
  if (!calories_per_portion) return '';
  
  const range = calories_per_portion.range_kcal;
  return `
    <div class="nutrition-card">
      <h5>Näringsuppskattning per portion</h5>
      <p><strong>Kalorier:</strong> ${range[0]}–${range[1]} kcal</p>
      <p class="small-muted">(uppskattning baserad på ingredienser)</p>
    </div>
  `;
}

// Lägg till i renderRecipe:
const nutritionHtml = renderNutrition(recipe.nutrition_estimates);
```

## Testning och validering
- Testa med befintliga recept för rimlighet
- Jämför med liknande recept från matsedelsplanerare
- Justera referensvärden baserat på feedback
- Logga osäkra matchningar för manuell granskning

## Framtida utveckling
1. **Utökad databas**: Lägg till fler ingredienser och märken
2. **Receptklassificering**: Automatisk identifiering av rätttyp för bättre makrouppskattning
3. **Användarjustering**: Möjlighet att justera portionstorlek eller ingrediensbyten
4. **Visualisering**: Diagram eller färgkodning för kalorimål
5. **Hälsomål**: Jämförelse med dagliga kaloribehov (ca 2000–2500 kcal/dag)

## Exempelutdata
```
BBQ pulled pork wraps med färsk coleslaw
Portioner: 4 · Tillagningstid: 20 min
Portionskostnad: 23,08 kr · Kalorier: 450–550 kcal

Näringsuppskattning per portion:
• Kalorier: 450–550 kcal
• Protein: 25–35 g
• Kolhydrater: 45–60 g
• Fett: 15–25 g
```

## Prioritering
1. Implementera grundläggande kaloriberäkning
2. Spara i JSON-utdata
3. Visa i frontend
4. Utöka med makronäring (valfritt)
5. Förbättra matchningsnoggrannhet över tid