async function loadPostsIndex() {
  const response = await fetch('./posts/index.json', { cache: 'no-store' });
  if (!response.ok) throw new Error('Kunde inte läsa postindex');
  return response.json();
}

async function loadPost(slug, date) {
  const response = await fetch(`./posts/${date}-${slug}.json`, { cache: 'no-store' });
  if (!response.ok) throw new Error(`Kunde inte läsa posten ${slug}`);
  return response.json();
}

function renderPostCard(post) {
  return `
    <article class="article">
      <div class="meta-row">
        <span class="badge">${post.date}</span>
        ${post.tags ? post.tags.map(tag => `<span class="tag">${tag}</span>`).join('') : ''}
      </div>
      <h3>${post.title}</h3>
      <p><strong>Kort sammanfattning:</strong> ${post.summary}</p>
      <p>${post.body}</p>
      <p><strong>Klinisk take:</strong> ${post.clinical_take}</p>
      <p>
        ${post.pubmed ? `<a href="${post.pubmed}" target="_blank" rel="noopener">PubMed</a>` : ''}
        ${post.pubmed && post.fulltext ? ' · ' : ''}
        ${post.fulltext ? `<a href="${post.fulltext}" target="_blank" rel="noopener">Fulltext</a>` : ''}
      </p>
    </article>
  `;
}

async function init() {
  const root = document.getElementById('postList');
  try {
    const index = await loadPostsIndex();
    const posts = await Promise.all(index.map(item => loadPost(item.slug, item.date)));
    root.innerHTML = posts.sort((a, b) => b.date.localeCompare(a.date)).map(renderPostCard).join('');
  } catch (error) {
    console.error(error);
    root.innerHTML = '<p>Kunde inte läsa poster just nu.</p>';
  }
}

init();
