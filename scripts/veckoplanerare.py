#!/usr/bin/env python3
# Veckoplaneraren – macOS Calendar sync + family-aware week overview + suggestions
import sqlite3, json, datetime, os, sys, random, re, urllib.request, urllib.error

CAL_CACHE = os.path.expanduser("~/Library/Calendars/Calendar Cache")
CD_REF = datetime.datetime(2001, 1, 1, 0, 0, 0)
OUTPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'veckodata.json')

WEEKDAY_SV = {'Monday':'måndag','Tuesday':'tisdag','Wednesday':'onsdag','Thursday':'torsdag','Friday':'fredag','Saturday':'lördag','Sunday':'söndag'}

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
    {'activity': 'åka på loppis i trakten', 'category': 'loppis', 'duration': '1,5 h', 'fit': ['familj', 'utflykt']},
    {'activity': 'ta en kort familjeutflykt i naturen', 'category': 'natur', 'duration': '2 h', 'fit': ['familj', 'ute']},
    {'activity': 'leta upp en lekpark för en enkel utflykt med Lage', 'category': 'lekpark', 'duration': '1 h', 'fit': ['småbarn', 'nära']},
    {'activity': 'gå på en barnvänlig aktivitet i närområdet', 'category': 'barnaktivitet', 'duration': '2 h', 'fit': ['familj', 'småbarn']},
    {'activity': 'titta efter en liten utställning eller konstupplevelse', 'category': 'konst', 'duration': '1,5 h', 'fit': ['utflykt']},
    {'activity': 'hitta någon musikupplevelse i närheten', 'category': 'musik', 'duration': '2 h', 'fit': ['utflykt']},
    {'activity': 'ta en promenad i skogen nära Rimforsa', 'category': 'natur', 'duration': '45 min', 'fit': ['nära', 'återhämtning']},
    {'activity': 'åka till biblioteket eller sagostund', 'category': 'barnaktivitet', 'duration': '1 h', 'fit': ['småbarn', 'nära']},
    {'activity': 'ha en lugn familjedag hemma med brädspel och fika', 'category': 'hemma', 'duration': '2 h', 'fit': ['återhämtning', 'familj']},
    {'activity': 'testa ett nytt recept tillsammans hemma', 'category': 'mat', 'duration': '1 h', 'fit': ['hemma', 'familj']},
    {'activity': 'avsätta ett pass för stugan eller vardagsrummet', 'category': 'hemmaprojekt', 'duration': '2–3 h', 'fit': ['praktiskt', 'hemma']},
    {'activity': 'ta ett lugnt pass med planering av trallbygget', 'category': 'hemmaprojekt', 'duration': '1 h', 'fit': ['praktiskt', 'hemma']},
    {'activity': 'åka till simhallen om energin finns', 'category': 'aktivitet', 'duration': '1,5 h', 'fit': ['familj']},
    {'activity': 'ta det lugnt hemma och prioritera återhämtning', 'category': 'återhämtning', 'duration': 'flex', 'fit': ['återhämtning', 'hemma']}
]

LOCAL_EVENT_SOURCES = [
    {'name': 'Visit Linköping', 'url': 'https://visitlinkoping.se/evenemang/', 'area': 'Linköping'},
    {'name': 'Visit Kinda', 'url': 'https://www.visitkinda.se/evenemang', 'area': 'Kinda/Rimforsa/Kisa'}
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
    cur.execute('SELECT Z_PK,ZTITLE,ZSTARTDATE,ZENDDATE,ZISALLDAY,ZCALENDAR,ZNOTES FROM ZCALENDARITEM WHERE ZENDDATE>=? AND ZSTARTDATE<=? ORDER BY ZSTARTDATE', (scd, ecd))
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


def fetch_url(url, timeout=8):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode('utf-8', errors='ignore')


def parse_visitlinkoping_candidates(html):
    text = re.sub(r'<script[\s\S]*?</script>', ' ', html, flags=re.I)
    text = re.sub(r'<style[\s\S]*?</style>', ' ', text, flags=re.I)
    text = re.sub(r'<[^>]+>', '\n', text)
    lines = [re.sub(r'\s+', ' ', line).strip() for line in text.splitlines()]
    lines = [line for line in lines if 6 <= len(line) <= 80]

    keywords = ('loppis', 'utställning', 'konsert', 'marknad', 'familjedag', 'barnteater', 'teater', 'musik', 'festival')
    banned = ('kunde inte hitta', 'försök med', 'evenemang i linköping', 'upptäck linköping', 'stora evenemang', 'fascinerande', 'spännande scenkonst', 'guidade turer', 'magiska konserter')

    candidates = []
    seen = set()
    for line in lines:
        low = line.lower()
        if any(b in low for b in banned):
            continue
        if any(k in low for k in keywords):
            cleaned = line.strip(' ,-')
            if cleaned and cleaned.lower() not in seen:
                seen.add(cleaned.lower())
                candidates.append({'title': cleaned, 'source': 'Visit Linköping', 'area': 'Linköping'})
        if len(candidates) >= 6:
            break
    return candidates[:6]


def get_local_event_candidates():
    candidates = []
    try:
        html = fetch_url('https://visitlinkoping.se/evenemang/')
        candidates.extend(parse_visitlinkoping_candidates(html))
    except Exception:
        pass

    fallback = [
        {'title': 'lokal loppis eller marknad i Linköpingstrakten', 'source': 'fallback', 'area': 'Linköping'},
        {'title': 'barnvänlig aktivitet eller familjedag i Kinda', 'source': 'fallback', 'area': 'Kinda/Rimforsa'},
        {'title': 'mindre konstutställning eller musikarrangemang i Linköping', 'source': 'fallback', 'area': 'Linköping'}
    ]

    seen = set()
    final = []
    for item in candidates + fallback:
        key = item['title'].lower()
        if key not in seen:
            seen.add(key)
            final.append(item)
    return final[:6]


def classify_load(day_events):
    if not day_events:
        return 'free'
    if len(day_events) >= 2:
        return 'busy'
    title = (day_events[0].get('title') or '').lower()
    if any(word in title for word in ['bvc', 'kalas', 'marknad', 'seminarie', 'ansökan', 'besök']):
        return 'medium'
    return 'light'


def choose_suggestions(day, local_candidates, used):
    suggestions = []
    load = classify_load(day['events'])
    weekday = day['weekday']

    if load == 'free' and weekday in ('lördag', 'söndag'):
        eventish = [c for c in local_candidates if c['title'] not in used]
        for c in eventish[:2]:
            suggestions.append({
                'activity': f"kolla om {c['title']} passar familjen",
                'category': 'lokalt evenemang',
                'duration': 'halvdag',
                'family_fit': 'familjevänligt',
                'reason': f"nära {c['area']} och i linje med era intressen"
            })
            used.add(c['title'])

    if load in ('free', 'light'):
        pool = [p for p in POOL if p['activity'] not in used]
        # Prioritera hemmaprojekt på vardagar, utflykt på helg
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


def build_reason_from_category(category):
    mapping = {
        'loppis': 'passar era intressen och går att göra som enkel familjeutflykt',
        'natur': 'brukar vara snällt för småbarn och funkar nära Rimforsa',
        'lekpark': 'passar särskilt bra med små barn',
        'barnaktivitet': 'är rimligt för Lage och går ofta att göra utan stor apparat',
        'konst': 'ligger nära era intressen och kan ge en lagom utflykt',
        'musik': 'passar ert intresse för musik om veckan känns lagom luftig',
        'hemmaprojekt': 'hjälper er framåt i stug- eller husprojekten',
        'återhämtning': 'kan vara klokt när veckan redan innehåller en del',
        'mat': 'är lätt att få till hemma med små barn',
        'hemma': 'kan ge en enklare dag utan extra logistik'
    }
    return mapping.get(category, 'passar familjens vardag just nu')


def build_narrative(days_data):
    names = []
    weekend = {'lördag': None, 'söndag': None}
    reflections = []

    for day in days_data:
        if day['has_events']:
            for e in day['events']:
                names.append((day['weekday'], e['title']))
                title_lower = (e['title'] or '').lower()
                if 'prov' in title_lower or 'seminarie' in title_lower or 'ansökan' in title_lower:
                    reflections.append('Det finns en punkt i veckan som kan må bra av lite lugn kvällen innan, så det kan vara klokt att inte fylla på för mycket just där.')
                if 'kalas' in title_lower or 'marknad' in title_lower or 'antik' in title_lower:
                    reflections.append('Det ser ut att finnas sociala eller utflyktsbetonade aktiviteter, så det kan vara klokt att lämna lite luft runt omkring för att slippa stress med små barn.')
                if 'bvc' in title_lower or 'besök' in title_lower:
                    reflections.append('Vårdbesök och tider mitt på dagen brukar bli enklare om resten av dagen hålls ganska mjuk och förutsägbar.')
        if day['weekday'] in weekend:
            weekend[day['weekday']] = day

    first_events = [f"{title} på {wd}" for wd, title in names[:4]]

    if first_events:
        if len(first_events) == 1:
            intro = f"Vecka {get_next_monday().isocalendar()[1]} ser ganska lugn ut men har ändå en tydlig hållpunkt i form av {first_events[0]}."
        else:
            intro = 'Vecka ' + str(get_next_monday().isocalendar()[1]) + ' innehåller några fasta punkter, bland annat ' + ', '.join(first_events[:-1]) + ' och ' + first_events[-1] + '.'
    else:
        intro = 'Veckan ser ovanligt luftig ut just nu, med gott om plats för både familjeliv, hemmaprojekt och spontana planer.'

    middle = []
    busy_days = sum(1 for d in days_data if d['has_events'])
    free_days = sum(1 for d in days_data if not d['has_events'])
    if busy_days >= 5:
        middle.append('Det är en rätt innehållsrik vecka, så det vore klokt att skydda någon lugn stund för återhämtning – särskilt med två små barn och vanlig vardagslogistik.')
    elif free_days >= 3:
        middle.append('Det finns fortfarande öppna luckor, vilket ger fint utrymme både för en liten utflykt och för att komma framåt med huset eller stugan.')

    sat = weekend.get('lördag')
    sun = weekend.get('söndag')
    if sat and not sat['has_events']:
        if sun and sun['has_events']:
            sun_titles = ', '.join(e['title'] for e in sun['events'][:2])
            middle.append(f'Framåt helgen är lördagen fortfarande öppen, medan söndagen redan rymmer {sun_titles}.')
        else:
            middle.append('Helgen ser fortfarande ganska öppen ut, särskilt lördagen, vilket lämnar plats för något familjevänligt i närområdet eller bara en lugn dag hemma.')
    elif sat and sat['has_events'] and sun and not sun['has_events']:
        sat_titles = ', '.join(e['title'] for e in sat['events'][:2])
        middle.append(f'Lördagen har redan saker på gång, som {sat_titles}, medan söndagen ser lugnare ut och kan passa för återhämtning eller något enkelt tillsammans.')

    suggestion_line = ''
    for day in days_data:
        if not day['has_events'] and day['suggestions']:
            acts = [s['activity'] for s in day['suggestions'][:2]]
            if day['weekday'] == 'lördag':
                suggestion_line = (f"På lördagen skulle ni antingen kunna {acts[0].lower()} eller, om ni hellre vill ta det lugnt, {acts[1].lower()}." if len(acts) > 1 else f"På lördagen skulle ni kunna {acts[0].lower()}.")
                break
    if not suggestion_line:
        for day in days_data:
            if not day['has_events'] and day['suggestions']:
                acts = [s['activity'] for s in day['suggestions'][:2]]
                suggestion_line = (f"En av de lediga dagarna skulle kunna passa för att {acts[0].lower()} eller {acts[1].lower()}." if len(acts) > 1 else f"En av de lediga dagarna skulle kunna passa för att {acts[0].lower()}.")
                break

    parts = [intro]
    parts.extend(middle[:2])
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

    local_candidates = get_local_event_candidates()
    used = set()
    days_data = []

    for i in range(days):
        day = start + datetime.timedelta(days=i)
        dk = day.strftime('%Y-%m-%d')
        wd = WEEKDAY_SV.get(day.strftime('%A'), day.strftime('%A'))
        de = [e for e in evs if e['start'] and datetime.datetime.fromisoformat(e['start']).strftime('%Y-%m-%d') == dk]

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
        else:
            summary = f"{wd.capitalize()} {dk[-5:]} – ledig"

        suggestions = choose_suggestions({'weekday': wd, 'events': de}, local_candidates, used) if not de or classify_load(de) != 'busy' else choose_suggestions({'weekday': wd, 'events': de}, local_candidates, used)

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
    iso_week = start.isocalendar()[1]

    return {
        'generated_at': datetime.datetime.now().isoformat(),
        'publish_mode': 'next_calendar_week',
        'week_number': iso_week,
        'week_start': start.strftime('%Y-%m-%d'),
        'week_end': (start + datetime.timedelta(days=days-1)).strftime('%Y-%m-%d'),
        'days_covered': days,
        'busy_days': busy,
        'free_days': free,
        'total_events': len(evs),
        'family_profile': FAMILY_PROFILE,
        'local_event_sources': LOCAL_EVENT_SOURCES,
        'local_event_candidates': local_candidates,
        'week_overview': build_narrative(days_data),
        'days': days_data
    }


if __name__ == '__main__':
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    data = build(days)
    with open(OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(json.dumps({'status': 'ok', 'output': OUTPUT, 'busy': data.get('busy_days'), 'free': data.get('free_days'), 'overview': data.get('week_overview')}, ensure_ascii=False))
