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

function renderVaruPost(post) {
  const recipes = (post.recipes || []).map(recipe => `
    <li>
      <strong>${recipe.name}</strong> – ${recipe.summary}<br />
      Portionskostnad: ${recipe.portion_cost || 'okänd'}
    </li>
  `).join('');

  return `
    <article class="article">
      <div class="meta-row"><span class="badge">${post.date}</span></div>
      <h3>${post.title}</h3>
      <p>${post.summary}</p>
      <p><a href="${post.source}" target="_blank" rel="noopener">Källa</a></p>
      <h4>Recept</h4>
      <ul>${recipes}</ul>
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
