const articles = [
  {
    title: 'A Review of Transdiagnostic Mechanisms in Cognitive Behavior Therapy',
    summary: 'En bred översikt över transdiagnostiska mekanismer i KBT, användbar som karta över vilka processer som faktiskt kan driva förbättring i behandling.',
    clinical: 'Bra som basartikel när man vill förstå hur interventioner kan fungera över flera diagnoser.',
    pubmed: 'https://pubmed.ncbi.nlm.nih.gov/38724124/',
    fulltext: 'https://pmc.ncbi.nlm.nih.gov/articles/PMC11090413/'
  },
  {
    title: 'A systematic review and meta-analysis of transdiagnostic cognitive behavioural psychotherapy for emotional disorders',
    summary: 'En meta-analys av transdiagnostisk KBT för emotionella syndrom, relevant för att bedöma effektbredd och generaliserbarhet.',
    clinical: 'Viktig för att förstå när transdiagnostiska upplägg kan vara ett starkt val snarare än diagnosspecifika protokoll.',
    pubmed: '',
    fulltext: 'https://www.nature.com/articles/s41562-023-01787-3'
  },
  {
    title: 'How effective psychological treatments work: mechanisms of change in cognitive behavioural therapy and beyond',
    summary: 'En bredare mekanismöversikt om hur psykologiska behandlingar fungerar, med fokus på mediatorer och förändringsprocesser.',
    clinical: 'Bra komplement när man vill gå bortom frågan om behandling fungerar och istället titta på varför.',
    pubmed: '',
    fulltext: 'https://www.researchgate.net/publication/377186650_How_effective_psychological_treatments_work_mechanisms_of_change_in_cognitive_behavioural_therapy_and_beyond'
  }
];

const list = document.getElementById('articleList');
list.innerHTML = articles.map(article => `
  <article class="article">
    <h3>${article.title}</h3>
    <p><strong>Kort sammanfattning:</strong> ${article.summary}</p>
    <p><strong>Klinisk take:</strong> ${article.clinical}</p>
    <p>
      ${article.pubmed ? `<a href="${article.pubmed}" target="_blank" rel="noopener">PubMed</a>` : ''}
      ${article.pubmed && article.fulltext ? ' · ' : ''}
      ${article.fulltext ? `<a href="${article.fulltext}" target="_blank" rel="noopener">Fulltext</a>` : ''}
    </p>
  </article>
`).join('');
