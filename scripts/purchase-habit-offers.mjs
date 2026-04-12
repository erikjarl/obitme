#!/usr/bin/env node
import fs from 'fs/promises';
import path from 'path';
import process from 'process';
import vm from 'vm';

const repoRoot = process.cwd();
const configPath = path.join(repoRoot, 'varu-config.json');
const purchaseHabitsPath = path.join(repoRoot, 'purchase-habits.json');
const historyDir = path.join(repoRoot, 'varu-data', 'purchase-habit-matches');
const historyIndexPath = path.join(historyDir, 'index.json');

const DEFAULT_SOURCE_LINKS = [
  'https://handlaprivatkund.ica.se/stores/1004066/categories?source=navigation',
  'https://handlaprivatkund.ica.se/stores/1004066',
  'https://www.ica.se/erbjudanden/ica-supermarket-rimforsa-1004066/'
];

function normalizeText(value) {
  return String(value ?? '')
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9åäö\s-]/gi, ' ')
    .replace(/[åä]/g, 'a')
    .replace(/[ö]/g, 'o')
    .replace(/\b(och|med|utan|ca|klass|ursprung|extra|ekologisk|eko|the|a|an)\b/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function tokenize(value) {
  return normalizeText(value)
    .split(' ')
    .map(part => part.trim())
    .filter(Boolean);
}

function parseSwedishNumber(value) {
  if (value == null) return null;
  const text = String(value).trim();
  if (!text) return null;
  const cleaned = text
    .replace(/\./g, '')
    .replace(/,/g, '.')
    .replace(/[^0-9.-]+/g, '');
  if (!cleaned) return null;
  const number = Number(cleaned);
  return Number.isFinite(number) ? number : null;
}

function round2(value) {
  return value == null ? null : Math.round(value * 100) / 100;
}

function formatSek(value) {
  if (value == null) return 'okänt';
  return new Intl.NumberFormat('sv-SE', {
    style: 'currency',
    currency: 'SEK',
    maximumFractionDigits: value % 1 === 0 ? 0 : 2
  }).format(value);
}

function formatPercent(value) {
  if (value == null) return null;
  return `${new Intl.NumberFormat('sv-SE', { maximumFractionDigits: 0 }).format(value)} %`;
}

function jaccardScore(aTokens, bTokens) {
  const a = new Set(aTokens);
  const b = new Set(bTokens);
  if (!a.size || !b.size) return 0;
  let intersection = 0;
  for (const token of a) if (b.has(token)) intersection += 1;
  const union = new Set([...a, ...b]).size;
  return union ? intersection / union : 0;
}

function searchUrl(template, query) {
  return template.replace('{query}', encodeURIComponent(query));
}

async function readJson(filePath) {
  return JSON.parse(await fs.readFile(filePath, 'utf8'));
}

async function ensureDir(dir) {
  await fs.mkdir(dir, { recursive: true });
}

async function fetchText(url) {
  const response = await fetch(url, {
    headers: {
      'user-agent': 'Mozilla/5.0 (compatible; obitme-varuovervakare/1.0)',
      'accept-language': 'sv-SE,sv;q=0.9,en;q=0.8'
    }
  });
  if (!response.ok) throw new Error(`HTTP ${response.status} for ${url}`);
  return response.text();
}

function extractInitialData(html) {
  const marker = 'window.__INITIAL_DATA__ = ';
  const start = html.indexOf(marker);
  if (start === -1) throw new Error('Kunde inte hitta window.__INITIAL_DATA__ på ICA-erbjudandesidan');
  const jsonStart = start + marker.length;
  let depth = 0;
  let inString = false;
  let escaped = false;
  let jsonEnd = -1;
  for (let i = jsonStart; i < html.length; i += 1) {
    const ch = html[i];
    if (inString) {
      if (escaped) escaped = false;
      else if (ch === '\\') escaped = true;
      else if (ch === '"') inString = false;
      continue;
    }
    if (ch === '"') inString = true;
    else if (ch === '{') depth += 1;
    else if (ch === '}') {
      depth -= 1;
      if (depth === 0) {
        jsonEnd = i + 1;
        break;
      }
    }
  }
  if (jsonEnd === -1) throw new Error('Kunde inte avgränsa INITIAL_DATA-JSON från ICA-erbjudandesidan');
  const objectLiteral = html.slice(jsonStart, jsonEnd);
  return vm.runInNewContext(`(${objectLiteral})`, Object.create(null), { timeout: 1000 });
}

const DEFAULT_MEALISH_TOKENS = new Set(['gryta', 'ratt', 'ratter', 'portion', 'portioner', 'carbonara', 'korvstroganoff', 'kulpotatis', 'pannkakor', 'spaghetti', 'serveras', 'med']);

function expandOfferItems(weeklyOffers, config) {
  const searchTemplate = config.store?.search_url_template || 'https://handlaprivatkund.ica.se/stores/1004066/search?q={query}';
  const offersUrl = config.store?.offers_url || DEFAULT_SOURCE_LINKS[2];
  const categoryUrl = config.store?.category_url || DEFAULT_SOURCE_LINKS[0];

  const items = [];
  for (const offer of weeklyOffers || []) {
    const mechanicText = offer?.details?.mechanicInfo || '';
    const regularPrice = parseSwedishNumber(offer?.stores?.[0]?.regularPrice);
    const quantity = offer?.parsedMechanics?.quantity || 1;
    const mechanicValue = parseSwedishNumber(offer?.parsedMechanics?.value2);
    const fixedPrice = quantity > 0 && mechanicValue != null ? round2(mechanicValue / quantity) : null;
    const unitSuffix = offer?.parsedMechanics?.value4 || '';
    const benefitType = offer?.parsedMechanics?.benefitType || '';
    const comparisonPrice = offer?.comparisonPrice || null;

    const candidateEntries = [];
    const detailName = [offer?.details?.brand, offer?.details?.name, offer?.details?.packageInformation].filter(Boolean).join(' ').trim();
    const detailNameAlt = [offer?.details?.name, offer?.details?.packageInformation, offer?.details?.brand].filter(Boolean).join(' ').trim();
    const looksAggregate = /,/.test(offer?.details?.name || '');
    if (detailName && !looksAggregate) candidateEntries.push({ name: detailName, isAggregate: false, sourceKind: 'detail' });
    if (detailNameAlt && !looksAggregate) candidateEntries.push({ name: detailNameAlt, isAggregate: false, sourceKind: 'detail' });
    for (const ean of offer?.eans || []) {
      const eanName = [ean?.articleDescription, offer?.details?.packageInformation, offer?.details?.brand].filter(Boolean).join(' ').trim();
      if (eanName) candidateEntries.push({ name: eanName, isAggregate: false, sourceKind: 'ean' });
    }
    const candidateNames = new Map();
    for (const entry of candidateEntries) {
      const key = normalizeText(entry.name);
      if (!key || candidateNames.has(key)) continue;
      candidateNames.set(key, entry);
    }

    const evidenceBase = [
      offer?.details?.name,
      mechanicText,
      offer?.stores?.[0]?.referencePriceText,
      offer?.details?.packageInformation,
      offer?.details?.brand
    ].filter(Boolean).join(' | ');

    for (const { name: candidateName, isAggregate, sourceKind } of candidateNames.values()) {
      const ordinaryPrice = regularPrice;
      const campaignPrice = fixedPrice;
      const discountSek = ordinaryPrice != null && campaignPrice != null ? round2(ordinaryPrice - campaignPrice) : null;
      const discountPercent = ordinaryPrice && discountSek != null && ordinaryPrice > 0
        ? round2((discountSek / ordinaryPrice) * 100)
        : null;
      const sourceQuery = candidateName.split(' ').slice(0, 4).join(' ');
      items.push({
        offer_id: offer?.id,
        parent_offer_id: offer?.parentId,
        product_name: candidateName.trim(),
        display_name: candidateName.trim(),
        brand: offer?.details?.brand || null,
        campaign_label: mechanicText || null,
        campaign_price: campaignPrice,
        ordinary_price: ordinaryPrice,
        discount_sek: discountSek,
        discount_percent: discountPercent,
        package_information: offer?.details?.packageInformation || null,
        comparison_price: comparisonPrice,
        restriction: offer?.restriction || null,
        category: offer?.category?.articleGroupName || null,
        source_kind: sourceKind,
        is_aggregate: isAggregate,
        source: {
          type: 'ica_offers_initial_data',
          url: offersUrl,
          search_url: searchUrl(searchTemplate, sourceQuery || candidateName),
          category_url: categoryUrl,
          evidence: evidenceBase
        },
        raw_offer: {
          id: offer?.id,
          name: offer?.details?.name || null,
          brand: offer?.details?.brand || null,
          packageInformation: offer?.details?.packageInformation || null,
          mechanicInfo: mechanicText,
          regularPrice: offer?.stores?.[0]?.regularPrice || null,
          comparisonPrice: comparisonPrice,
          eans: offer?.eans || []
        }
      });
    }
  }
  return dedupeOffers(items);
}

function dedupeOffers(items) {
  const seen = new Map();
  for (const item of items) {
    const key = `${normalizeText(item.product_name)}|${item.offer_id}`;
    const existing = seen.get(key);
    if (!existing) {
      seen.set(key, item);
      continue;
    }
    const existingScore = (existing.discount_sek || 0) + (existing.discount_percent || 0) / 100;
    const nextScore = (item.discount_sek || 0) + (item.discount_percent || 0) / 100;
    if (nextScore > existingScore) seen.set(key, item);
  }
  return [...seen.values()];
}

function matchHabitToOffer(habit, offer) {
  const habitName = habit?.name || '';
  const aliases = Array.isArray(habit?.aliases) ? habit.aliases : [];
  const matchKeywords = Array.isArray(habit?.matchKeywords) ? habit.matchKeywords : [];
  const preferredBrands = Array.isArray(habit?.preferredBrands) ? habit.preferredBrands : [];
  const excludeKeywords = Array.isArray(habit?.excludeKeywords) ? habit.excludeKeywords : [];

  const offerName = offer.product_name || '';
  const normalizedHabit = normalizeText(habitName);
  const normalizedOffer = normalizeText(offerName);
  const offerTokens = tokenize(offerName);

  if (!normalizedHabit || !normalizedOffer) return null;

  const excluded = excludeKeywords.some(keyword => {
    const normalizedKeyword = normalizeText(keyword);
    return normalizedKeyword && normalizedOffer.includes(normalizedKeyword);
  });
  if (excluded) return null;

  const habitTokens = tokenize(habitName);
  const hasMealishNoise = habitTokens.length === 1 && offerTokens.some(token => DEFAULT_MEALISH_TOKENS.has(token));
  if (hasMealishNoise) return null;

  if (offer.is_aggregate && habitTokens.length === 1) return null;

  if (offerName.trim().toLowerCase() === habitName.trim().toLowerCase()) {
    return { type: 'exact', score: 1.0, evidence: `${habitName} exakt mot ${offerName}` };
  }

  if (normalizedOffer === normalizedHabit) {
    return { type: 'normalized', score: 0.98, evidence: `${habitName} normaliserat mot ${offerName}` };
  }

  const primaryKeywords = [habitName, ...aliases, ...matchKeywords].filter(Boolean);
  for (const keyword of primaryKeywords) {
    const normalizedKeyword = normalizeText(keyword);
    if (!normalizedKeyword) continue;
    const keywordTokens = tokenize(keyword);
    const containsAllKeywordTokens = keywordTokens.length > 0 && keywordTokens.every(token => offerTokens.includes(token));
    if (containsAllKeywordTokens) {
      const preferredBrandOk = preferredBrands.length === 0 || preferredBrands.some(brand => normalizedOffer.includes(normalizeText(brand)));
      if (preferredBrandOk) {
        return { type: keyword === habitName ? 'keyword' : 'alias', score: 0.94, evidence: `${keyword} finns i ${offerName}` };
      }
    }
  }

  const score = jaccardScore(habitTokens, offerTokens);
  const longEnough = habitTokens.length >= 1 && offerTokens.length >= 1;
  const tokenOverlap = habitTokens.filter(token => offerTokens.includes(token));
  if (longEnough && score >= 0.74 && tokenOverlap.length >= Math.min(2, habitTokens.length)) {
    return {
      type: 'fuzzy_conservative',
      score: round2(score),
      evidence: `konservativ fuzzy (${round2(score)}) via gemensamma tokens: ${tokenOverlap.join(', ')}`
    };
  }

  return null;
}

function selectMatches(habits, offers) {
  const matches = [];
  const usedOfferKeys = new Set();

  for (const habit of habits) {
    const candidates = [];
    for (const offer of offers) {
      const match = matchHabitToOffer(habit, offer);
      if (!match) continue;
      candidates.push({ habit, offer, match });
    }

    candidates.sort((a, b) => {
      if (b.match.score !== a.match.score) return b.match.score - a.match.score;
      if ((b.offer.discount_sek || 0) !== (a.offer.discount_sek || 0)) return (b.offer.discount_sek || 0) - (a.offer.discount_sek || 0);
      return (b.offer.discount_percent || 0) - (a.offer.discount_percent || 0);
    });

    const selected = candidates.find(candidate => !usedOfferKeys.has(`${candidate.offer.offer_id}|${normalizeText(candidate.offer.product_name)}`));
    if (!selected) continue;

    const offerKey = `${selected.offer.offer_id}|${normalizeText(selected.offer.product_name)}`;
    usedOfferKeys.add(offerKey);

    matches.push({
      habit_name: selected.habit.name,
      matched_product_name: selected.offer.product_name,
      match_type: selected.match.type,
      ordinary_price: selected.offer.ordinary_price,
      campaign_price: selected.offer.campaign_price,
      campaign_label: selected.offer.campaign_label,
      discount_sek: selected.offer.discount_sek,
      discount_percent: selected.offer.discount_percent,
      source: {
        type: selected.offer.source.type,
        url: selected.offer.source.url,
        search_url: selected.offer.source.search_url,
        category_url: selected.offer.source.category_url
      },
      evidence: `${selected.offer.source.evidence} | Match: ${selected.match.evidence}`,
      category: selected.offer.category,
      restriction: selected.offer.restriction,
      comparison_price: selected.offer.comparison_price,
      raw_offer_id: selected.offer.offer_id
    });
  }

  matches.sort((a, b) => {
    if ((b.discount_sek || 0) !== (a.discount_sek || 0)) return (b.discount_sek || 0) - (a.discount_sek || 0);
    return (b.discount_percent || 0) - (a.discount_percent || 0);
  });

  return matches;
}

function buildDiscordMessage(matches, config) {
  const directLink = config.links?.varuovervakare || 'https://erikjarl.github.io/obitme/varuovervakare.html';
  const offersLink = config.store?.offers_url || DEFAULT_SOURCE_LINKS[2];
  if (!matches.length) {
    return [
      'Veckans relevanta ICA-erbjudanden för Köpvanelistan är klara.',
      'Jag hittade inga tillräckligt säkra matchningar den här veckan.',
      `Kolla gärna hela varuövervakaren: ${directLink}`,
      `ICA-erbjudanden: ${offersLink}`
    ].join(' ');
  }

  const lines = matches.slice(0, 6).map(item => {
    const pricingBits = [];
    if (item.ordinary_price != null) pricingBits.push(`ord. ${formatSek(item.ordinary_price)}`);
    if (item.campaign_price != null) pricingBits.push(item.campaign_label ? `${item.campaign_label}` : `nu ${formatSek(item.campaign_price)}`);
    if (item.discount_sek != null) pricingBits.push(`-${formatSek(item.discount_sek)}`);
    const percent = formatPercent(item.discount_percent);
    if (percent) pricingBits.push(percent);
    return `${item.habit_name}: ${item.matched_product_name} (${pricingBits.join(', ')})`;
  });

  return [
    'Veckans relevanta ICA-erbjudanden för Köpvanelistan är klara.',
    lines.join(' · '),
    `Hela veckorapporten: ${directLink}`,
    `ICA-erbjudanden: ${offersLink}`
  ].join(' ');
}

function buildSummary(matches) {
  if (!matches.length) return 'Inga tillräckligt säkra matchningar mot Köpvanelistan hittades i veckans ICA-erbjudanden.';
  const top = matches.slice(0, 3).map(item => {
    const discount = item.discount_sek != null ? `-${formatSek(item.discount_sek)}` : 'rabatt okänd';
    return `${item.habit_name} → ${item.matched_product_name} (${discount})`;
  });
  return `Matchade ${matches.length} köpvanevaror. Starkaste träffar: ${top.join('; ')}.`;
}

async function updateIndex(entry) {
  let index = [];
  try {
    index = JSON.parse(await fs.readFile(historyIndexPath, 'utf8'));
  } catch (error) {
    if (error.code !== 'ENOENT') throw error;
  }

  const filtered = index.filter(item => item.file !== entry.file);
  filtered.unshift(entry);
  filtered.sort((a, b) => String(b.date || '').localeCompare(String(a.date || '')) || String(b.file).localeCompare(String(a.file)));
  await fs.writeFile(historyIndexPath, `${JSON.stringify(filtered, null, 2)}\n`);
}

async function main() {
  const config = await readJson(configPath);
  const purchaseHabits = await readJson(purchaseHabitsPath);
  const habits = (purchaseHabits.items || []).filter(item => item?.enabled !== false);
  if (!habits.length) throw new Error('purchase-habits.json innehåller inga aktiva poster');

  const offersHtml = await fetchText(config.store?.offers_url || DEFAULT_SOURCE_LINKS[2]);
  const initialData = extractInitialData(offersHtml);
  const weeklyOffers = initialData?.offers?.weeklyOffers || [];
  if (!weeklyOffers.length) throw new Error('ICA-erbjudandesidan innehöll inga weeklyOffers i INITIAL_DATA');

  const expandedOffers = expandOfferItems(weeklyOffers, config);
  const matches = selectMatches(habits, expandedOffers);
  const now = new Date();
  const date = now.toISOString().slice(0, 10);
  const createdAt = now.toISOString();
  const file = `${date}-ica-rimforsa-purchase-habit-matches.json`;
  const messagePreview = buildDiscordMessage(matches, config);
  const result = {
    date,
    created_at: createdAt,
    title: 'Veckans ICA-erbjudanden matchade mot Köpvanelista',
    summary: buildSummary(matches),
    source_links: [
      config.store?.category_url,
      config.store?.store_url,
      config.store?.offers_url
    ].filter(Boolean),
    matched_items: matches,
    message_preview: messagePreview,
    discord_destination: config.discord || null,
    no_matches: matches.length === 0,
    store: config.store,
    matching_method: {
      order: ['exact', 'normalized', 'alias_or_keyword', 'fuzzy_conservative'],
      fuzzy_threshold: 0.74,
      notes: 'Konservativ matchning: hellre missad träff än fel produkt.'
    },
    scraping_method: {
      primary_source: 'ICA erbjudandesida med window.__INITIAL_DATA__',
      supporting_sources: [config.store?.category_url, config.store?.store_url, config.store?.search_url_template].filter(Boolean),
      note: 'Denna körning extraherade stabil JSON från erbjudandesidan. Söklänkar och butikslänkar sparas som stöd/evidence för vidare verifiering.'
    },
    offers_considered: expandedOffers.length
  };

  await ensureDir(historyDir);
  await fs.writeFile(path.join(historyDir, file), `${JSON.stringify(result, null, 2)}\n`);
  await updateIndex({ file, date, title: result.title, summary: result.summary, no_matches: result.no_matches });

  process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
}

main().catch(error => {
  console.error(error);
  process.exit(1);
});
