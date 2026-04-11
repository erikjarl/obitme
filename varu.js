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
  return new Intl.NumberFormat('sv-SE', { style: 'currency', currency: 'SEK', maximumFractionDigits: 0 }).format(value);
}

function renderOfferList(post) {
  const offers = post.offer_review?.picked_offers || [];
  if (!offers.length) return '<p>Inga tydliga erbjudanden listade.</p>';
  return `
    <div class="detail-grid">
      ${offers.map(offer => `
        <div class="detail-card">
          <h5>${offer.product}</h5>
          <p><strong>Kampanj:</strong> ${formatSek(offer.campaign_price_sek)}</p>
          <p><strong>Ordinarie:</strong> ${formatSek(offer.ordinary_price_sek)}</p>
          <p><strong>Rabatt:</strong> ${formatSek(offer.discount_sek)}</p>
          <p class="small-muted">${offer.source || ''}</p>
        </div>
      `).join('')}
    </div>
  `;
}

function renderRecipe(recipe) {
  const offerProducts = (recipe.ica_offer_products || []).map(item => `
    <li><strong>${item.product}</strong> – kampanj ${formatSek(item.campaign_price_sek)}, ordinarie ${formatSek(item.ordinary_price_sek)}, rabatt ${formatSek(item.discount_sek)}<br /><span class="small-muted">${item.source_reference || ''}</span></li>
  `).join('');

  const ingredients = (recipe.ingredients || []).map(item => `<li>${item.item}: ${item.amount}</li>`).join('');
  const extraCosts = (recipe.estimated_non_ica_costs || []).map(item => `<li>${item.item}: ${formatSek(item.cost_sek)} <span class="small-muted">(${item.estimated ? 'uppskattat' : 'exakt'}${item.source ? `, ${item.source}` : ''})</span></li>`).join('');
  const steps = (recipe.recipe?.steps || []).map(step => `<li>${step}</li>`).join('');

  return `
    <section class="recipe-card">
      <h4>${recipe.name}</h4>
      <p>${recipe.summary || ''}</p>
      <div class="meta-row">
        <span class="badge">${recipe.servings || ''}</span>
        <span class="badge">Tillagningstid: ${recipe.cook_time || 'okänd'}</span>
        <span class="badge">Portionskostnad: ${formatSek(recipe.estimated_cost_per_portion_sek)}</span>
        <span class="badge">Totalkostnad: ${formatSek(recipe.estimated_total_batch_cost_sek)}</span>
      </div>
      <h5>ICA-produkter i receptet</h5>
      <ul>${offerProducts}</ul>
      <h5>Ingredienser</h5>
      <ul>${ingredients}</ul>
      <h5>Kompletterande ingredienspriser</h5>
      <ul>${extraCosts}</ul>
      <h5>Tillvägagångssätt</h5>
      <ol>${steps}</ol>
    </section>
  `;
}

function renderVaruPost(post) {
  const recipes = (post.recipes || []).map(renderRecipe).join('');

  return `
    <article class="article">
      <div class="meta-row"><span class="badge">${post.date}</span><span class="badge">${post.store || ''}</span></div>
      <h3>${post.title}</h3>
      <p>${post.summary}</p>
      <p>
        ${post.primary_store_url ? `<a href="${post.primary_store_url}" target="_blank" rel="noopener">ICA butik</a>` : ''}
        ${post.offer_source_url ? ` · <a href="${post.offer_source_url}" target="_blank" rel="noopener">ICA erbjudanden</a>` : ''}
      </p>
      ${post.source_note ? `<p class="small-muted">${post.source_note}</p>` : ''}
      <h4>Veckans erbjudanden som användes</h4>
      ${renderOfferList(post)}
      <h4>Recept</h4>
      ${recipes}
    </article>
  `;
}

async function initVaru() {
  const root = document.getElementById('varuPostList');
  if (!root) return;
  try {
    const index = await loadVaruIndex();
    const posts = await Promise.all(index.map(item => loadVaruPost(item.file)));
    root.innerHTML = posts.sort((a, b) => b.date.localeCompare(a.date)).map(renderVaruPost).join('');
  } catch (error) {
    console.error(error);
    root.innerHTML = '<p>Inga veckorapporter publicerade ännu.</p>';
  }
}

initVaru();
