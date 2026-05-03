#!/usr/bin/env python3
# Veckoplaneraren – macOS Calendar sync + family-aware week overview + adaptive event matching
import sqlite3, json, datetime, os, sys, re, urllib.request, ssl, html

CAL_CACHE = os.path.expanduser("~/Library/Calendars/Calendar Cache")
CD_REF = datetime.datetime(2001, 1, 1, 0, 0, 0)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT = os.path.join(BASE_DIR, '..', 'veckodata.json')

WEEKDAY_SV = {
    'Monday': 'måndag', 'Tuesday': 'tisdag', 'Wednesday': 'onsdag', 'Thursday': 'torsdag',
    'Friday': 'fredag', 'Saturday': 'lördag', 'Sunday': 'söndag'
}

FAMILY_PROFILE = {
    'members': [
        {'name': 'Erik', 'role': 'pappa', 'notes': 'psykolog'},
        {'name': 'Ida', 'role': 'mamma', 'notes': 'mammaledig nu, senare inredningsarkitekt hemifrån'},
        {'name': 'Lage', 'role': 'son', 'born': 2022},
        {'name': 'Elliott', 'role': 'son', 'born': 2025}
    ],
    'home': 'hus i Rimforsa',
    'car': 'Passat GTE 2020',
    'interests': ['loppisar', 'naturupplevelser', 'lekparker', 'barnaktiviteter', 'konst', 'musik'],
    'areas': ['Rimforsa', 'Kisa', 'Linköping'],
    'max_trip_area': 'Linköping eller Kisa med omnejd',
    'projects': [
        'renovera stugan för att sälja eller hyra ut den',
        'bygga trall på baksidan',
        'färdigställa vardagsrummet'
    ]
}

POOL = [
    {'activity': 'åka på loppis i trakten', 'category': 'loppis', 'duration': '1,5 h'},
    {'activity': 'ta en kort familjeutflykt i naturen', 'category': 'natur', 'duration': '2 h'},
    {'activity': 'leta upp en lekpark för en enkel utflykt med Lage', 'category': 'lekpark', 'duration': '1 h'},
    {'activity': 'gå på en barnvänlig aktivitet i närområdet', 'category': 'barnaktivitet', 'duration': '2 h'},
    {'activity': 'titta efter en liten utställning eller konstupplevelse', 'category': 'konst', 'duration': '1,5 h'},
    {'activity': 'hitta någon musikupplevelse i närheten', 'category': 'musik', 'duration': '2 h'},
    {'activity': 'åka till biblioteket eller sagostund', 'category': 'barnaktivitet', 'duration': '1 h'},
    {'activity': 'avsätta ett pass för stugan eller vardagsrummet', 'category': 'hemmaprojekt', 'duration': '2–3 h'},
    {'activity': 'ta ett lugnt pass med planering av trallbygget', 'category': 'hemmaprojekt', 'duration': '1 h'},
    {'activity': 'ta det lugnt hemma och prioritera återhämtning', 'category': 'återhämtning', 'duration': 'flex'}
]

SCRAPE_SOURCES = [
    {
        'name': 'Visit Linköping highlights',
        'kind': 'manual_event_pages',
        'items': [
            {
                'title': 'Vårens Östgötadagar 2026',
                'url': 'https://visitlinkoping.se/evenemang/varens-ostgotadagar-2026/',
                'area': 'Linköping',
                'date_hint': '9-10 maj 2026',
                'tags': ['loppis', 'marknad', 'familj', 'utflykt']
            },
            {
                'title': 'Evenemang för dig & dina barn i Linköping',
                'url': 'https://visitlinkoping.se/evenemang/familj/',
                'area': 'Linköping',
                'date_hint': None,
                'tags': ['familj', 'barnaktivitet']
            }
        ]
    },
    {
        'name': 'loppisar.com Östergötland',
        'kind': 'loppisar_feed',
        'url': 'https://www.loppisar.com/sokning.html?slanID=21&skommunID=alla&srange=framat&srangetime=6&do_search=S%C3%B6k+nu!&do_search=1'
    }
]

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

CATEGORY_KEYWORDS = {
    'loppis': ['loppis', 'marknad', 'bakluck', 'second hand'],
    'musik': ['musik', 'konsert', 'spelning'],
    'konst': ['konst', 'utställ', 'vernissage'],
    'barnaktivitet': ['barn', 'familj', 'sagostund', 'pyssel', 'lek'],
    'natur': ['natur', 'skog', 'trädgård', 'vårroadtrip']
}

GENERIC_TITLE_PATTERNS = [
    r'^övrig\b', r'^alla\b', r'^barn och ungdom$', r'^digital konsert$',
    r'^marknad & loppis$', r'^levande musik från stadens mindre scener$'
]


def cd2dt(ts):
    if not ts:
        return None
    return CD_REF + datetime.timedelta(seconds=ts)


def get_next_monday(base_date=None):
    base = base_date or datetime.datetime.now()
    base = base.replace(hour=0, minute=0, second=0, microsecond=0)
    days_until_monday = (7 - base.weekday()) % 7
    if days_until_monday == 0:
        days_until_monday = 7
    return base + datetime.timedelta(days=days_until_monday)


def get_cal(days=7, start_dt=None):
    if not os.path.exists(CAL_CACHE):
        return None, 'Cache saknas'
    conn = sqlite3.connect(CAL_CACHE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute('SELECT Z_PK,ZTITLE FROM ZNODE WHERE ZISEVENTCONTAINER=1 AND ZTITLE NOT NULL')
    cals = {r['Z_PK']: r['ZTITLE'] for r in cur.fetchall()}
    start_dt = (start_dt or get_next_monday()).replace(hour=0, minute=0, second=0, microsecond=0)
    end_dt = start_dt + datetime.timedelta(days=days)
    scd = (start_dt - CD_REF).total_seconds()
    ecd = (end_dt - CD_REF).total_seconds()
    cur.execute('SELECT ZTITLE,ZSTARTDATE,ZENDDATE,ZISALLDAY,ZCALENDAR FROM ZCALENDARITEM WHERE ZENDDATE>=? AND ZSTARTDATE<=? ORDER BY ZSTARTDATE', (scd, ecd))
    rows = cur.fetchall()
    conn.close()
    skip = {'Svenska helgdagar', 'Födelsedagar', 'Siri hittade i program', 'Hittade på naturligt språk', 'Nilsbot'}
    events = []
    for r in rows:
        cn = cals.get(r['ZCALENDAR'], 'Okänd')
        if cn in skip:
            continue
        s = cd2dt(r['ZSTARTDATE'])
        e = cd2dt(r['ZENDDATE'])
        events.append({
            'title': r['ZTITLE'],
            'start': s.isoformat() if s else None,
            'end': e.isoformat() if e else None,
            'is_all_day': bool(r['ZISALLDAY']),
            'calendar': cn
        })
    return events, None


def fetch_url(url, timeout=10):
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'sv-SE,sv;q=0.9,en-US;q=0.8,en;q=0.7'
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode('utf-8', errors='ignore')
    except Exception:
        with urllib.request.urlopen(req, timeout=timeout, context=SSL_CTX) as resp:
            return resp.read().decode('utf-8', errors='ignore')


def html_to_lines(raw_html):
    raw_html = html.unescape(raw_html)
    text = re.sub(r'<script[\s\S]*?</script>', ' ', raw_html, flags=re.I)
    text = re.sub(r'<style[\s\S]*?</style>', ' ', text, flags=re.I)
    text = re.sub(r'<[^>]+>', '\n', text)
    lines = [re.sub(r'\s+', ' ', line).strip() for line in text.splitlines()]
    return [line for line in lines if line]


def infer_tags(text):
    low = text.lower()
    tags = []
    for tag, keywords in CATEGORY_KEYWORDS.items():
        if any(k in low for k in keywords):
            tags.append(tag)
    return sorted(set(tags))


def is_generic_title(title):
    low = title.strip().lower()
    return any(re.search(pattern, low) for pattern in GENERIC_TITLE_PATTERNS)


def score_event_for_family(event):
    score = 0
    title = event.get('title', '')
    text = ' '.join([title, event.get('location', ''), ' '.join(event.get('tags', [])), event.get('area', '')]).lower()

    for interest in FAMILY_PROFILE['interests']:
        if interest.rstrip('er') in text or interest in text:
            score += 4

    tags = set(event.get('tags', []))
    if 'barnaktivitet' in tags:
        score += 5
    if 'loppis' in tags:
        score += 5
    if 'musik' in tags or 'konst' in tags:
        score += 3
    if 'natur' in tags:
        score += 2

    if any(area.lower() in text for area in ['rimforsa', 'kisa']):
        score += 5
    elif 'linköping' in text:
        score += 3
    elif 'mjölby' in text or 'brok' in text or 'östergötland' in text:
        score += 1

    if event.get('date_hint'):
        score += 3
    if event.get('url'):
        score += 2
    if event.get('source') == 'loppisar.com':
        score += 2
    if is_generic_title(title):
        score -= 8
    if len(title.split()) <= 2:
        score -= 2
    return score


def parse_manual_event_pages(source):
    events = []
    debug = []
    for item in source['items']:
        try:
            content = fetch_url(item['url'])
            lines = html_to_lines(content)
            combined = ' '.join(lines[:80]).lower()
            if 'kunde inte hitta några poster' in combined and not item.get('date_hint'):
                debug.append({'source': source['name'], 'url': item['url'], 'status': 'ok', 'count': 0, 'sample_titles': []})
                continue
            title = item['title'] + (f" ({item['date_hint']})" if item.get('date_hint') else '')
            event = {
                'title': title,
                'source': item.get('source', source['name']),
                'area': item['area'],
                'url': item['url'],
                'date_hint': item.get('date_hint'),
                'location': item['area'],
                'tags': sorted(set(item.get('tags', []) + infer_tags(title + ' ' + ' '.join(lines[:20]))))
            }
            events.append(event)
            debug.append({'source': source['name'], 'url': item['url'], 'status': 'ok', 'count': 1, 'sample_titles': [title]})
        except Exception as e:
            debug.append({'source': source['name'], 'url': item['url'], 'status': 'error', 'error': str(e)})
    return events, debug


def parse_loppisar_feed(source):
    url = source['url']
    try:
        text = fetch_url(url, timeout=12)
    except Exception as e:
        return [], [{'source': source['name'], 'url': url, 'status': 'error', 'error': str(e)}]

    lines = html_to_lines(text)
    current_date = None
    candidates = []
    for i, line in enumerate(lines):
        low = line.lower()
        if low.startswith(('måndagen den', 'tisdagen den', 'onsdagen den', 'torsdagen den', 'fredagen den', 'lördagen den', 'söndagen den')):
            current_date = line.replace(':', '')
            continue
        if '(säsongsloppis)' not in low:
            continue
        context = ' '.join(lines[i:i+4]).lower()
        if not any(place in context for place in ['linköpings kommun', 'kisa', 'kinda kommun', 'rimforsa', 'mjölby kommun', 'brok']):
            continue
        title = re.sub(r'\s*-\s*\d{1,2}:\d{2}-\d{1,2}:\d{2}\s*\(Säsongsloppis\)', '', line, flags=re.I).strip()
        if not title or len(title) < 4:
            continue
        place_line = ''
        for j in range(i+1, min(i+4, len(lines))):
            if lines[j].startswith('Plats:'):
                place_line = lines[j].replace('Plats:', '').strip()
                break
        event = {
            'title': f"{title} – {current_date}" if current_date else title,
            'source': 'loppisar.com',
            'area': 'Östergötland/Linköping-Kisa',
            'url': url,
            'date_hint': current_date,
            'location': place_line,
            'tags': ['loppis']
        }
        candidates.append(event)
        if len(candidates) >= 10:
            break

    return candidates, [{
        'source': source['name'], 'url': url, 'status': 'ok', 'count': len(candidates),
        'sample_titles': [c['title'] for c in candidates[:3]]
    }]


def gather_external_events():
    all_events = []
    scrape_debug = []
    for source in SCRAPE_SOURCES:
        if source['kind'] == 'manual_event_pages':
            events, debug = parse_manual_event_pages(source)
        elif source['kind'] == 'loppisar_feed':
            events, debug = parse_loppisar_feed(source)
        else:
            events, debug = [], [{'source': source['name'], 'status': 'error', 'error': 'unknown source kind'}]
        all_events.extend(events)
        scrape_debug.extend(debug)

    unique = []
    seen = set()
    for event in all_events:
        key = (event.get('title', '').lower(), event.get('source', '').lower())
        if key in seen:
            continue
        seen.add(key)
        event['family_match_score'] = score_event_for_family(event)
        unique.append(event)

    unique.sort(key=lambda e: (e['family_match_score'], 1 if e.get('date_hint') else 0, 1 if e.get('url') else 0), reverse=True)
    return unique, scrape_debug


def classify_load(day_events):
    if not day_events:
        return 'free'
    if len(day_events) >= 2:
        return 'busy'
    title = (day_events[0].get('title') or '').lower()
    if any(word in title for word in ['bvc', 'kalas', 'marknad', 'seminarie', 'ansökan', 'besök']):
        return 'medium'
    return 'light'


def build_reason_from_category(category):
    mapping = {
        'loppis': 'passar era intressen och går att göra som enkel familjeutflykt',
        'natur': 'brukar vara snällt för småbarn och funkar nära Rimforsa',
        'lekpark': 'passar särskilt bra med små barn',
        'barnaktivitet': 'är rimligt för Lage och går ofta att göra utan stor apparat',
        'konst': 'ligger nära era intressen och kan ge en lagom utflykt',
        'musik': 'passar ert intresse för musik om veckan känns lagom luftig',
        'hemmaprojekt': 'hjälper er framåt i stug- eller husprojekten',
        'återhämtning': 'kan vara klokt när veckan redan innehåller en del'
    }
    return mapping.get(category, 'passar familjens vardag just nu')


def choose_suggestions(day, matched_events, used):
    suggestions = []
    load = classify_load(day['events'])
    weekday = day['weekday']

    if load == 'free' and weekday in ('lördag', 'söndag'):
        eventish = [e for e in matched_events if e['title'] not in used and e.get('family_match_score', 0) >= 6 and not is_generic_title(e['title'])]
        for event in eventish[:2]:
            reason = f"faktisk träff från {event['source']}"
            if event.get('location'):
                reason += f", plats: {event['location']}"
            suggestions.append({
                'activity': f"kolla om {event['title']} passar familjen",
                'category': 'lokalt evenemang',
                'duration': 'halvdag',
                'family_fit': 'familjevänligt',
                'reason': reason,
                'source': event['source'],
                'url': event.get('url'),
                'match_score': event.get('family_match_score')
            })
            used.add(event['title'])

    if load in ('free', 'light') and len(suggestions) < 3:
        pool = [p for p in POOL if p['activity'] not in used]
        if weekday in ('måndag', 'tisdag', 'onsdag', 'torsdag'):
            pool.sort(key=lambda x: 0 if x['category'] in ('hemmaprojekt', 'återhämtning', 'barnaktivitet') else 1)
        else:
            pool.sort(key=lambda x: 0 if x['category'] in ('loppis', 'natur', 'lekpark', 'barnaktivitet', 'konst', 'musik') else 1)
        for p in pool[:3-len(suggestions)]:
            suggestions.append({
                'activity': p['activity'],
                'category': p['category'],
                'duration': p['duration'],
                'family_fit': 'familjevänligt',
                'reason': build_reason_from_category(p['category'])
            })
            used.add(p['activity'])

    if load == 'busy':
        suggestions = [{
            'activity': 'prioritera återhämtning och håll resten av dagen enkel',
            'category': 'återhämtning',
            'duration': 'flex',
            'family_fit': 'familjevänligt',
            'reason': 'dagen verkar redan ganska full'
        }]

    return suggestions[:3]


def build_narrative(days_data):
    names = []
    weekend = {'lördag': None, 'söndag': None}
    reflections = []
    for day in days_data:
        if day['has_events']:
            for e in day['events']:
                names.append((day['weekday'], e['title']))
                title_lower = (e['title'] or '').lower()
                if any(x in title_lower for x in ['seminarie', 'ansökan']):
                    reflections.append('Det finns en punkt i veckan som kan må bra av lite lugn kvällen innan, så det kan vara klokt att inte fylla på för mycket just där.')
                if any(x in title_lower for x in ['marknad', 'loppis']):
                    reflections.append('Det ser ut att finnas sociala eller utflyktsbetonade aktiviteter, så det kan vara klokt att lämna lite luft runt omkring för att slippa stress med små barn.')
        if day['weekday'] in weekend:
            weekend[day['weekday']] = day

    first_events = [f"{title} på {wd}" for wd, title in names[:4]]
    if first_events:
        intro = 'Vecka ' + str(get_next_monday().isocalendar()[1]) + ' innehåller några fasta punkter, bland annat ' + ', '.join(first_events[:-1]) + ' och ' + first_events[-1] + '.' if len(first_events) > 1 else f"Vecka {get_next_monday().isocalendar()[1]} ser ganska lugn ut men har ändå en tydlig hållpunkt i form av {first_events[0]}."
    else:
        intro = 'Veckan ser ovanligt luftig ut just nu, med gott om plats för både familjeliv, hemmaprojekt och spontana planer.'

    busy_days = sum(1 for d in days_data if d['has_events'])
    free_days = sum(1 for d in days_data if not d['has_events'])
    middle = []
    if free_days >= 3:
        middle.append('Det finns fortfarande öppna luckor, vilket ger fint utrymme både för en liten utflykt och för att komma framåt med huset eller stugan.')
    if weekend['lördag'] and weekend['lördag']['has_events'] and weekend['söndag'] and not weekend['söndag']['has_events']:
        sat_titles = ', '.join(e['title'] for e in weekend['lördag']['events'][:2])
        middle.append(f'Lördagen har redan saker på gång, som {sat_titles}, medan söndagen ser lugnare ut och kan passa för återhämtning eller något enkelt tillsammans.')

    suggestion_line = ''
    for day in days_data:
        if not day['has_events'] and day['suggestions']:
            acts = [s['activity'] for s in day['suggestions'][:2]]
            suggestion_line = (f"En av de lediga dagarna skulle kunna passa för att {acts[0].lower()} eller {acts[1].lower()}." if len(acts) > 1 else f"En av de lediga dagarna skulle kunna passa för att {acts[0].lower()}.")
            break

    parts = [intro] + middle[:2]
    if suggestion_line:
        parts.append(suggestion_line)
    seen = set()
    for r in reflections:
        if r not in seen:
            parts.append(r)
            seen.add(r)
        if len(seen) >= 2:
            break
    return ' '.join(parts)


def build(days=7):
    start = get_next_monday()
    evs, err = get_cal(days, start)
    if err:
        return {'error': err}

    matched_events, scrape_debug = gather_external_events()
    used = set()
    days_data = []

    for i in range(days):
        day = start + datetime.timedelta(days=i)
        dk = day.strftime('%Y-%m-%d')
        wd = WEEKDAY_SV.get(day.strftime('%A'), day.strftime('%A'))
        de = [e for e in evs if e['start'] and datetime.datetime.fromisoformat(e['start']).strftime('%Y-%m-%d') == dk]
        summary = f"{wd.capitalize()} {dk[-5:]} – ledig"
        if de:
            lines = []
            for e in de:
                ts = ''
                if not e['is_all_day'] and e['start'] and e['end']:
                    s = datetime.datetime.fromisoformat(e['start'])
                    en = datetime.datetime.fromisoformat(e['end'])
                    ts = f" {s.strftime('%H:%M')}–{en.strftime('%H:%M')}"
                ct = f" [{e['calendar']}]" if e['calendar'] != 'Hem' else ''
                lines.append(f"{e['title']}{ts}{ct}")
            summary = f"{wd.capitalize()} {dk[-5:]} – {'; '.join(lines)}"

        suggestions = choose_suggestions({'weekday': wd, 'events': de}, matched_events, used)
        days_data.append({
            'date': dk,
            'weekday': wd,
            'events': de,
            'has_events': len(de) > 0,
            'summary': summary,
            'suggestions': suggestions
        })

    busy = sum(1 for d in days_data if d['has_events'])
    free = days - busy
    return {
        'generated_at': datetime.datetime.now().isoformat(),
        'publish_mode': 'next_calendar_week',
        'week_number': start.isocalendar()[1],
        'week_start': start.strftime('%Y-%m-%d'),
        'week_end': (start + datetime.timedelta(days=days-1)).strftime('%Y-%m-%d'),
        'days_covered': days,
        'busy_days': busy,
        'free_days': free,
        'total_events': len(evs),
        'family_profile': FAMILY_PROFILE,
        'scrape_sources': SCRAPE_SOURCES,
        'local_event_candidates': matched_events[:10],
        'scrape_debug': scrape_debug,
        'scraped_event_count': len(matched_events),
        'week_overview': build_narrative(days_data),
        'days': days_data
    }


if __name__ == '__main__':
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    data = build(days)
    with open(OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(json.dumps({'status': 'ok', 'output': OUTPUT, 'busy': data.get('busy_days'), 'free': data.get('free_days'), 'scraped_event_count': data.get('scraped_event_count')}, ensure_ascii=False))
