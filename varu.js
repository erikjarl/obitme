async function loadVaruIndex() {
  const response = await fetch('./varu-data/index.json', { cache: 'no-store' });
  if (!response.ok) throw new Error('Kunde inte läsa varuindex');
  return response.json();
}

async function loadVaruPost(file) {
  const response = await fetch(`./varu-data/${file}`, { cache: 'no-store' });
  if (!response.ok) throw new Error(`Kunde inte läsa ${file}`);
  return response.json();
}

function formatSek(value) {
  if (value === undefined || value === null || value === '') return 'okänt';
  
  // If value is an object, try to extract numeric value
  if (typeof value === 'object' && value !== null) {
    // Handle nested objects like campaign_price: { amount_sek: 91.58, ... }
    if ('amount_sek' in value) {
      value = value.amount_sek;
    } else if ('display' in value) {
      // Try to extract number from display string
      const match = String(value.display).match(/[\d.,]+/);
      if (match) value = parseFloat(match[0].replace(',', '.'));
      else return 'okänt';
    } else {
      // Unknown object, try to convert to string and extract number
      const str = JSON.stringify(value);
      const match = str.match(/[\d.,]+/);
      if (match) value = parseFloat(match[0].replace(',', '.'));
      else return 'okänt';
    }
  }
  
  // Ensure it's a number
  const num = Number(value);
  if (isNaN(num)) return 'okänt';
  
  return new Intl.NumberFormat('sv-SE', { 
    style: 'currency', 
    currency: 'SEK', 
    maximumFractionDigits: num % 1 === 0 ? 0 : 2 
  }).format(num);
}

function extractPrice(value) {
  if (value === undefined || value === null) return null;
  
  if (typeof value === 'object' && value !== null) {
    // Handle nested objects
    if ('amount_sek' in value) {
      return value.amount_sek;
    } else if ('display' in value) {
      // Try to extract number from display
      const match = String(value.display).match(/[\d.,]+/);
      if (match) return parseFloat(match[0].replace(',', '.'));
      return null;
    } else {
      // Unknown object, try to find any numeric property
      for (const key in value) {
        if (typeof value[key] === 'number') return value[key];
      }
      return null;
    }
  }
  
  // Direct number or string
  const num = Number(value);
  return isNaN(num) ? null : num;
}

function escapeHtml(value) {
  return String(value ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function formatAmount(amount, unit) {
  if (amount === undefined || amount === null || amount === '') return '';
  if (!unit) return String(amount);
  const normalizedUnit = String(unit).trim().toLowerCase();
  const unitMap = {
    g: 'gram',
    gram: 'gram',
    ml: 'ml',
    l: 'liter',
    dl: 'dl',
    cl: 'cl',
    st: 'st',
    tsk: 'tsk',
    msk: 'msk',
    kruka: 'kruka',
    klyfta: 'klyfta',
    klyftor: 'klyftor',
    portion: 'portion'
  };
  const displayUnit = unitMap[normalizedUnit] || unit;
  return `${amount} ${displayUnit}`;
}

function extractCaloriesText(recipe) {
  const text = [recipe.nutrition_profile, recipe.nutrition_estimates?.calories_per_portion?.display]
    .filter(Boolean)
    .join(' ');
  const rangeMatch = text.match(/(ca\s*)?(\d{3,4})\s*[–-]\s*(\d{3,4})\s*kcal/i);
  if (rangeMatch) return `${rangeMatch[2]}–${rangeMatch[3]} kcal`;
  const singleMatch = text.match(/ca\s*(\d{3,4})\s*kcal/i) || text.match(/(\d{3,4})\s*kcal/i);
  if (singleMatch) return `ca ${singleMatch[1]} kcal`;
  return '';
}

function estimateIngredientPoints(item) {
  const name = String(item?.item || '').toLowerCase();
  const cost = Number(item?.line_cost_sek || 0);
  const amount = Number(item?.amount || 0);
  const unit = String(item?.unit || '').toLowerCase();

  const zeroishFoods = ['gurka', 'tomat', 'tomater', 'rädis', 'lök', 'vitlök', 'citron', 'zucchini', 'paprika', 'salladsärtor', 'sockerärtor', 'örter'];
  const leanProteinFoods = ['kycklingfilé', 'kyckling', 'ägg', 'kikärter', 'vita bönor', 'linser', 'potatis'];
  const higherPointFoods = ['olivolja', 'rapsolja', 'smör', 'fetaost', 'ost', 'lax', 'gräddfil', 'avokado', 'pasta'];

  if (zeroishFoods.some(x => name.includes(x))) return 0;
  if (leanProteinFoods.some(x => name.includes(x))) {
    if (name.includes('ägg')) return Math.max(0, Math.round(amount * 0.5));
    if (unit === 'g' || unit === 'gram') return Math.max(0, Math.round(amount / 250));
    return Math.max(0, Math.round(cost / 12));
  }
  if (higherPointFoods.some(x => name.includes(x))) {
    if (name.includes('olivolja') || name.includes('rapsolja') || name.includes('smör')) {
      if (unit === 'msk') return Math.max(1, Math.round(amount * 2));
      if (unit === 'ml') return Math.max(1, Math.round(amount / 7));
      return Math.max(1, Math.round(cost / 3));
    }
    if (name.includes('ost') || name.includes('fetaost')) {
      if (unit === 'g' || unit === 'gram') return Math.max(1, Math.round(amount / 35));
    }
    if (name.includes('avokado')) return Math.max(1, Math.round(amount));
    if (name.includes('pasta')) {
      if (unit === 'g' || unit === 'gram') return Math.max(1, Math.round(amount / 55));
    }
    if (name.includes('lax')) {
      if (unit === 'g' || unit === 'gram') return Math.max(1, Math.round(amount / 80));
    }
    return Math.max(1, Math.round(cost / 8));
  }

  if (cost <= 1) return 0;
  return Math.max(0, Math.round(cost / 10));
}

function estimateRecipePoints(recipe) {
  const ingredients = Array.isArray(recipe?.ingredients) ? recipe.ingredients : [];
  const servings = Number(recipe?.servings || 4) || 4;
  const total = ingredients.reduce((sum, item) => sum + estimateIngredientPoints(item), 0);
  const perPortion = Math.max(0, Math.round((total / servings) * 10) / 10);
  const uncertainty = ingredients.length >= 8 ? 'medel' : 'hög';
  return {
    total,
    perPortion,
    uncertainty,
    note: 'uppskattning'
  };
}

function recipeStoreLabel(post) {
  const name = getStoreName(post).toLowerCase();
  if (name.includes('ica') || name.includes('willys')) return 'Butiksvaror att köpa';
  return 'Varor att köpa';
}

function getStoreName(post) {
  if (typeof post.store === 'string') return post.store;
  return post.store?.name || '';
}

function isValidUrl(value) {
  if (!value || typeof value !== 'string') return false;
  try {
    new URL(value);
    return true;
  } catch {
    return false;
  }
}

function getPrimaryStoreUrl(post) {
  const candidate = post.primary_store_url || post.store?.primary_store_url || post.store?.store_url || '';
  return isValidUrl(candidate) ? candidate : '';
}

function getOfferUrl(post) {
  const candidate = post.offer_source_url || post.store?.offers_url || '';
  return isValidUrl(candidate) ? candidate : '';
}

function normalizeOffer(offer) {
  // Helper to extract numeric value from price field
  const extractNumeric = (field) => {
    if (field === undefined || field === null) return null;
    if (typeof field === 'number') return field;
    if (typeof field === 'object' && field !== null) {
      if ('amount_sek' in field) return field.amount_sek;
      if ('display' in field) {
        const match = String(field.display).match(/[\d.,]+/);
        if (match) return parseFloat(match[0].replace(',', '.'));
      }
      // Try to find any numeric property
      for (const key in field) {
        if (typeof field[key] === 'number') return field[key];
      }
    }
    return null;
  };
  
  // Try multiple possible fields for campaign price
  let campaign = extractNumeric(offer.campaign_price_sek);
  if (campaign === null) campaign = extractNumeric(offer.campaign_price);
  if (campaign === null) campaign = extractNumeric(offer.derived_campaign_batch_cost_sek);
  if (campaign === null) campaign = extractNumeric(offer.normalized_campaign_price_per_piece_sek);
  
  // Try multiple possible fields for ordinary price
  let ordinary = extractNumeric(offer.ordinary_price_sek);
  if (ordinary === null) ordinary = extractNumeric(offer.ordinary_price);
  
  // Extract discount
  const discount = extractNumeric(offer.discount_sek);
  
  // Get campaign label
  let campaignLabel = '';
  if (typeof offer.campaign_price === 'object' && offer.campaign_price !== null && offer.campaign_price.display) {
    campaignLabel = offer.campaign_price.display;
  } else if (offer.campaign_format) {
    campaignLabel = offer.campaign_format;
  } else if (offer.price_basis) {
    campaignLabel = offer.price_basis;
  }
  
  // Get source
  let source = '';
  if (typeof offer.source === 'string') {
    source = offer.source;
  } else if (offer.source?.evidence) {
    source = offer.source.evidence;
  } else if (offer.source_reference) {
    source = offer.source_reference;
  }
  
  return {
    product: offer.product || offer.product_name || 'Produkt',
    campaign,
    campaignLabel,
    ordinary,
    discount,
    source
  };
}

function renderOfferList(post) {
  const rawOffers = post.offer_review?.picked_offers || post.offer_review?.picked_products || post.fyndlista || [];
  const offers = rawOffers.map(normalizeOffer);
  if (!offers.length) return '<p>Inga tydliga erbjudanden listade.</p>';
  return `
    <ul>
      ${offers.map(offer => `
        <li>
          <strong>${escapeHtml(offer.product)}</strong>: ${formatSek(offer.campaign)}
          ${offer.ordinary !== null ? ` <span class="small-muted">(ord. ${formatSek(offer.ordinary)})</span>` : ''}
          ${offer.discount !== null ? ` <span class="small-muted">· spar ${formatSek(offer.discount)}</span>` : ''}
        </li>
      `).join('')}
    </ul>
  `;
}

function renderRecipe(recipe) {
  const title = recipe.name || recipe.title || 'Recept';
  const summary = recipe.summary || recipe.description || '';
  const servings = recipe.servings_label || recipe.servings || '';
  const portionCost = recipe.estimated_cost_per_portion_sek ?? recipe.cost_per_portion_sek ?? recipe.costs?.cost_per_portion_sek;
  const totalCost = recipe.estimated_total_batch_cost_sek ?? recipe.batch_cost_sek ?? recipe.costs?.campaign_total_sek;
  const offerProductsRaw = recipe.ica_offer_products || recipe.ica_offer_products_used || recipe.ica_products_to_buy || [];
  const offerProducts = offerProductsRaw.map(item => {
    const campaign = extractPrice(item.campaign_price_sek ?? item.campaign_price);
    const ordinary = extractPrice(item.ordinary_price_sek ?? item.ordinary_price);
    const discount = item.discount_sek ?? item.discount_reference_sek;
    
    let sourceStr = item.source_reference || '';
    if (!sourceStr && item.source) {
      if (typeof item.source === 'string') {
        sourceStr = item.source;
      } else if (typeof item.source === 'object' && item.source !== null) {
        if (item.source.evidence) {
          sourceStr = item.source.evidence;
        } else if (item.source.type) {
          sourceStr = item.source.type;
        } else if (item.source.url) {
          if (isValidUrl(item.source.url)) {
            const url = new URL(item.source.url);
            sourceStr = url.hostname;
          } else {
            sourceStr = String(item.source.url);
          }
        }
      }
    }
    
    const name = item.product || item.product_name || 'Produkt';
    const evidence = item.evidence ? ` · ${item.evidence}` : '';
    return `<li><strong>${escapeHtml(name)}</strong><br />Kampanj: ${formatSek(campaign)} · Ordinarie: ${formatSek(ordinary)} · Rabatt: ${formatSek(discount)}<br /><span class="small-muted">${escapeHtml(sourceStr)}${escapeHtml(evidence)}</span></li>`;
  }).join('');

  const ingredientsRaw = recipe.ingredients || [];
  const ingredients = ingredientsRaw.map(item => {
    const priceBits = [];
    if (item.line_cost_sek !== undefined) priceBits.push(`kostnad ${formatSek(item.line_cost_sek)}`);
    const ingredientPoints = estimateIngredientPoints(item);
    priceBits.push(`ca ${ingredientPoints} p`);
    if (item.price_status) priceBits.push(item.price_status);
    
    if (item.source) {
      let sourceStr = '';
      if (typeof item.source === 'string') {
        sourceStr = item.source;
      } else if (typeof item.source === 'object' && item.source !== null) {
        if (item.source.evidence) {
          sourceStr = item.source.evidence;
        } else if (item.source.type) {
          sourceStr = item.source.type;
          if (item.source.url && isValidUrl(item.source.url)) {
            const url = new URL(item.source.url);
            sourceStr += ` (${url.hostname})`;
          }
        } else if (item.source.url) {
          if (isValidUrl(item.source.url)) {
            const url = new URL(item.source.url);
            sourceStr = url.hostname;
          } else {
            sourceStr = String(item.source.url);
          }
        }
      }
      if (sourceStr) priceBits.push(sourceStr);
    }
    
    return `<li>${escapeHtml(item.item)}: ${escapeHtml(formatAmount(item.amount, item.unit))}${priceBits.length ? ` <span class="small-muted">(${escapeHtml(priceBits.join(' · '))})</span>` : ''}</li>`;
  }).join('');

  const extraCostsRaw = recipe.estimated_non_ica_costs || ingredientsRaw.filter(item => !item.campaign_price && item.ordinary_price == null ? item.price_status === 'schablon' : false);
  const extraCosts = extraCostsRaw.map(item => {
    let sourceStr = '';
    if (item.source) {
      if (typeof item.source === 'string') {
        sourceStr = item.source;
      } else if (typeof item.source === 'object' && item.source !== null) {
        if (item.source.evidence) {
          sourceStr = item.source.evidence;
        } else if (item.source.type) {
          sourceStr = item.source.type;
        } else if (item.source.url) {
          if (isValidUrl(item.source.url)) {
            const url = new URL(item.source.url);
            sourceStr = url.hostname;
          } else {
            sourceStr = String(item.source.url);
          }
        }
      }
    }
    return `<li>${escapeHtml(item.item)}: ${formatSek(item.cost_sek ?? item.line_cost_sek)} <span class="small-muted">(${escapeHtml(item.price_status || (item.estimated ? 'uppskattat' : 'exakt'))}${sourceStr ? `, ${escapeHtml(sourceStr)}` : ''})</span></li>`;
  }).join('');

  const stepsRaw = recipe.recipe?.steps || recipe.method || [];
  const steps = Array.isArray(stepsRaw) ? stepsRaw.map(step => `<li>${escapeHtml(step)}</li>`).join('') : `<li>${escapeHtml(stepsRaw)}</li>`;
  const caloriesText = extractCaloriesText(recipe);
  const pointsEstimate = estimateRecipePoints(recipe);

  return `
    <section class="recipe-card">
      <h4>${escapeHtml(title)}</h4>
      <p>${escapeHtml(summary)}</p>
      <div class="meta-row">
        <span class="badge">${escapeHtml(servings)}</span>
        <span class="badge">Tillagningstid: ${escapeHtml(recipe.cook_time || 'okänd')}</span>
        <span class="badge">Portionskostnad: ${formatSek(portionCost)}</span>
        ${caloriesText ? `<span class="badge">Kalorier: ${escapeHtml(caloriesText)}/portion</span>` : ''}
        <span class="badge">Points: ca ${escapeHtml(pointsEstimate.perPortion)} p/portion</span>
        <span class="badge">Totalt ca ${escapeHtml(pointsEstimate.total)} p</span>
        <span class="badge">Osäkerhet: ${escapeHtml(pointsEstimate.uncertainty)}</span>
        <span class="badge">Totalkostnad: ${formatSek(totalCost)}</span>
      </div>
      <h5>Butiksvaror att köpa</h5>
      ${offerProducts ? `<ul>${offerProducts}</ul>` : '<p>Inga butiksvaror listade.</p>'}
      <h5>Ingredienser</h5>
      <ul>${ingredients}</ul>
      <h5>Kompletterande ingredienspriser</h5>
      ${extraCosts ? `<ul>${extraCosts}</ul>` : '<p>Kompletterande kostnader ingår redan i receptet.</p>'}
      <h5>Tillvägagångssätt</h5>
      ${steps ? `<ol>${steps}</ol>` : '<p>Inget tillvägagångssätt listat.</p>'}
    </section>
  `;
}

function renderVaruPost(post) {
  const recipes = (post.recipes || []).map(renderRecipe).join('');
  const primaryStoreUrl = getPrimaryStoreUrl(post);
  const offerUrl = getOfferUrl(post);

  return `
    <article class="article">
      <div class="meta-row"><span class="badge">${escapeHtml(post.date)}</span><span class="badge">${escapeHtml(getStoreName(post))}</span></div>
      <h3>${escapeHtml(post.title)}</h3>
      <p>${escapeHtml(post.summary)}</p>
      <p>
        ${primaryStoreUrl ? `<a href="${primaryStoreUrl}" target="_blank" rel="noopener">Butik</a>` : ''}
        ${offerUrl ? ` · <a href="${offerUrl}" target="_blank" rel="noopener">Erbjudanden</a>` : ''}
      </p>
      ${post.source_note ? `<p class="small-muted">${escapeHtml(post.source_note)}</p>` : ''}
      <h4>Veckans erbjudanden som användes</h4>
      ${renderOfferList(post)}
      <h4>Recept</h4>
      ${recipes}
    </article>
  `;
}

function renderPostErrorCard(file, error) {
  return `
    <article class="article">
      <h3>Kunde inte visa ${escapeHtml(file)}</h3>
      <p class="small-muted">${escapeHtml(error?.message || String(error))}</p>
    </article>
  `;
}

async function initVaru() {
  const root = document.getElementById('varuPostList');
  if (!root) return;
  try {
    const index = await loadVaruIndex();
    if (!Array.isArray(index) || index.length === 0) {
      root.innerHTML = '<p>Inga veckorapporter publicerade ännu.</p>';
      return;
    }

    const ordered = [...index].sort((a, b) => String(b.date || '').localeCompare(String(a.date || '')));
    const rendered = [];

    for (const item of ordered) {
      try {
        const post = await loadVaruPost(item.file);
        rendered.push(renderVaruPost(post));
      } catch (error) {
        console.error('Fel vid rendering av post', item.file, error);
        rendered.push(renderPostErrorCard(item.file, error));
      }
    }

    root.innerHTML = rendered.join('') || '<p>Inga veckorapporter publicerade ännu.</p>';
  } catch (error) {
    console.error(error);
    root.innerHTML = '<p>Kunde inte läsa veckorapporter just nu.</p>';
  }
}

initVaru();
