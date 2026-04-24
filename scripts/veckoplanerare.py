#!/usr/bin/env python3
# Veckoplaneraren – macOS Calendar sync + week overview + suggestions
import sqlite3, json, datetime, os, sys, random

CAL_CACHE = os.path.expanduser("~/Library/Calendars/Calendar Cache")
CD_REF = datetime.datetime(2001, 1, 1, 0, 0, 0)
OUTPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'veckodata.json')

WEEKDAY_SV = {'Monday':'måndag','Tuesday':'tisdag','Wednesday':'onsdag','Thursday':'torsdag','Friday':'fredag','Saturday':'lördag','Sunday':'söndag'}
POOL = [
    ("gå på loppis i trakten","loppis","1,5 h"),
    ("ta en familjeutflykt i naturen","natur","2 h"),
    ("leta upp en lekpark för en enkel utflykt","barnaktivitet","1 h"),
    ("gå på ett barnvänligt arrangemang i närområdet","barnaktivitet","2 h"),
    ("titta efter en liten utställning eller konstupplevelse","konst","1,5 h"),
    ("hitta någon musikupplevelse eller konsert i närheten","musik","2 h"),
    ("ta en promenad i skogen","natur","45 min"),
    ("åka till simhallen","aktivitet","1,5 h"),
    ("laga en nyttig middag tillsammans","mat","1 h"),
    ("läsa bok och ta det lugnt hemma","återhämtning","1 h"),
    ("åka och handla veckans mat i lugn takt","ärenden","1,5 h"),
    ("spela ett brädspel hemma","hemma","1 h"),
    ("testa ett nytt recept tillsammans","mat","1 h"),
    ("åka till biblioteket","barnaktivitet","1 h"),
    ("gå en runda på stan och fika","socialt","1,5 h"),
    ("göra hemmaspa eller lugn återhämtning hemma","välmående","30 min"),
    ("åka och bada om vädret tillåter","natur","3 h"),
    ("plocka svamp eller bär i säsong","natur","2 h")
]

LOCAL_EVENT_SOURCES = [
    {"name": "Visit Linköping", "url": "https://visitlinkoping.se/evenemang/", "area": "Linköping"},
    {"name": "Visit Kinda", "url": "https://www.visitkinda.se/evenemang", "area": "Kinda/Rimforsa/Kisa"}
]

def cd2dt(ts):
    if not ts: return None
    return CD_REF + datetime.timedelta(seconds=ts)

def get_next_monday(base_date=None):
    base = base_date or datetime.datetime.now()
    base = base.replace(hour=0, minute=0, second=0, microsecond=0)
    days_until_monday = (7 - base.weekday()) % 7
    if days_until_monday == 0:
        days_until_monday = 7
    return base + datetime.timedelta(days=days_until_monday)


def get_cal(days=7, start_dt=None):
    if not os.path.exists(CAL_CACHE): return None, "Cache saknas"
    conn = sqlite3.connect(CAL_CACHE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT Z_PK,ZTITLE FROM ZNODE WHERE ZISEVENTCONTAINER=1 AND ZTITLE NOT NULL")
    cals = {r['Z_PK']:r['ZTITLE'] for r in cur.fetchall()}
    start_dt = (start_dt or get_next_monday()).replace(hour=0,minute=0,second=0,microsecond=0)
    end_dt = start_dt + datetime.timedelta(days=days)
    scd = (start_dt-CD_REF).total_seconds(); ecd = (end_dt-CD_REF).total_seconds()
    cur.execute("SELECT Z_PK,ZTITLE,ZSTARTDATE,ZENDDATE,ZISALLDAY,ZCALENDAR,ZNOTES FROM ZCALENDARITEM WHERE ZENDDATE>=? AND ZSTARTDATE<=? ORDER BY ZSTARTDATE", (scd,ecd))
    rows = cur.fetchall(); conn.close()
    skip = {'Svenska helgdagar','Födelsedagar','Siri hittade i program','Hittade på naturligt språk','Nilsbot'}
    events = []
    for r in rows:
        cn = cals.get(r['ZCALENDAR'],'Okänd')
        if cn in skip: continue
        s = cd2dt(r['ZSTARTDATE']); e = cd2dt(r['ZENDDATE'])
        events.append({'title':r['ZTITLE'],'start':s.isoformat() if s else None,'end':e.isoformat() if e else None,'is_all_day':bool(r['ZISALLDAY']),'calendar':cn})
    return events, None

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
                    reflections.append('Det finns en punkt senare i perioden som kan må bra av lite lugn och återhämtning kvällen innan.')
                if 'kalas' in title_lower or 'marknad' in title_lower or 'antik' in title_lower:
                    reflections.append('Det ser ut att finnas sociala eller utflyktsbetonade aktiviteter, så det kan vara klokt att lämna lite luft runt omkring för att slippa stress.')
        if day['weekday'] in weekend:
            weekend[day['weekday']] = day

    first_events = []
    for wd, title in names[:4]:
        first_events.append(f"{title} på {wd}")

    intro = ''
    if first_events:
        if len(first_events) == 1:
            intro = f"Veckan ser ganska lugn ut men har ändå en tydlig hållpunkt i form av {first_events[0]}."
        else:
            intro = 'Veckan innehåller några fasta punkter, bland annat ' + ', '.join(first_events[:-1]) + ' och ' + first_events[-1] + '.'
    else:
        intro = 'Veckan ser ovanligt luftig ut just nu, med gott om plats för både återhämtning och spontana planer.'

    middle = []
    busy_days = sum(1 for d in days_data if d['has_events'])
    free_days = sum(1 for d in days_data if not d['has_events'])
    if busy_days >= 8:
        middle.append('Det är ganska mycket inbokat under perioden, så det vore klokt att skydda någon lugn stund för återhämtning.')
    elif free_days >= 6:
        middle.append('Det finns flera öppna dagar, vilket ger bra utrymme för både praktiska ärenden och något trevligt tillsammans.')

    sat = weekend.get('lördag')
    sun = weekend.get('söndag')
    if sat and not sat['has_events']:
        if sun and sun['has_events']:
            sun_titles = ', '.join(e['title'] for e in sun['events'][:2])
            middle.append(f'Framåt helgen är lördagen fortfarande öppen, medan söndagen redan rymmer {sun_titles}.')
        else:
            middle.append('Helgen ser fortfarande ganska öppen ut, särskilt lördagen, vilket lämnar plats för något spontant eller bara vila hemma.')
    elif sat and sat['has_events'] and sun and not sun['has_events']:
        sat_titles = ', '.join(e['title'] for e in sat['events'][:2])
        middle.append(f'Lördagen har redan saker på gång, som {sat_titles}, medan söndagen ser lugnare ut och kan passa för återhämtning.')

    suggestion_lines = []
    for day in days_data:
        if not day['has_events'] and day['suggestions']:
            acts = [s['activity'] for s in day['suggestions'][:2]]
            if day['weekday'] == 'lördag':
                suggestion_lines.append(f'På lördagen skulle ni antingen kunna {acts[0].lower()} eller, om ni hellre vill ta det lugnt, {acts[1].lower()}.' if len(acts) > 1 else f'På lördagen skulle ni kunna {acts[0].lower()}.')
                break
    if not suggestion_lines:
        for day in days_data:
            if not day['has_events'] and day['suggestions']:
                acts = [s['activity'] for s in day['suggestions'][:2]]
                suggestion_lines.append(f'En av de lediga dagarna skulle kunna passa för att {acts[0].lower()} eller {acts[1].lower()}.' if len(acts) > 1 else f'En av de lediga dagarna skulle kunna passa för att {acts[0].lower()}.')
                break

    seen = set()
    uniq_reflections = []
    for r in reflections:
        if r not in seen:
            uniq_reflections.append(r)
            seen.add(r)

    parts = [intro]
    parts.extend(middle[:2])
    parts.extend(suggestion_lines[:1])
    parts.extend(uniq_reflections[:2])
    return ' '.join(parts)


def build(days=7):
    start = get_next_monday()
    evs, err = get_cal(days, start)
    if err: return {'error':err}
    used = set(); days_data = []
    for i in range(days):
        day = start + datetime.timedelta(days=i)
        dk = day.strftime('%Y-%m-%d')
        wd = WEEKDAY_SV.get(day.strftime('%A'),day.strftime('%A'))
        de = [e for e in evs if e['start'] and datetime.datetime.fromisoformat(e['start']).strftime('%Y-%m-%d')==dk]
        if de:
            lines = []
            for e in de:
                ts = ''
                if not e['is_all_day'] and e['start'] and e['end']:
                    s=datetime.datetime.fromisoformat(e['start']); en=datetime.datetime.fromisoformat(e['end'])
                    ts=f" {s.strftime('%H:%M')}–{en.strftime('%H:%M')}"
                ct = f" [{e['calendar']}]" if e['calendar']!='Hem' else ''
                lines.append(f"{e['title']}{ts}{ct}")
            summary = f"{wd.capitalize()} {dk[-5:]} – {'; '.join(lines)}"
        else:
            summary = f"{wd.capitalize()} {dk[-5:]} – ledig"
        suggestions = []
        if not de:
            avail = [s for s in POOL if s[0] not in used]
            if len(avail)<3: used.clear(); avail=POOL
            picks = random.sample(avail,min(3,len(avail)))
            for p in picks:
                suggestions.append({'activity':p[0],'category':p[1],'duration':p[2], 'family_fit': 'familjevänligt'})
                used.add(p[0])
        days_data.append({'date':dk,'weekday':wd,'events':de,'has_events':len(de)>0,'summary':summary,'suggestions':suggestions})
    busy = sum(1 for d in days_data if d['has_events']); free = days-busy
    iso_week = start.isocalendar()[1]
    return {'generated_at':datetime.datetime.now().isoformat(),'publish_mode':'next_calendar_week','week_number':iso_week,'week_start':start.strftime('%Y-%m-%d'),'week_end':(start+datetime.timedelta(days=days-1)).strftime('%Y-%m-%d'),'days_covered':days,'busy_days':busy,'free_days':free,'total_events':len(evs),'family_profile':{'interests':['loppisar','naturupplevelser','lekparker','barnaktiviteter','konst','musik'],'areas':['Linköping','Rimforsa','Kisa']},'local_event_sources':LOCAL_EVENT_SOURCES,'week_overview':build_narrative(days_data),'days':days_data}

if __name__=='__main__':
    days = int(sys.argv[1]) if len(sys.argv)>1 else 7
    data = build(days)
    with open(OUTPUT,'w',encoding='utf-8') as f: json.dump(data,f,ensure_ascii=False,indent=2)
    print(json.dumps({'status':'ok','output':OUTPUT,'busy':data['busy_days'],'free':data['free_days'],'overview':data['week_overview']},ensure_ascii=False))
