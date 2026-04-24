#!/usr/bin/env python3
# Veckoplaneraren – macOS Calendar sync + week overview + suggestions
import sqlite3, json, datetime, os, sys, random

CAL_CACHE = os.path.expanduser("~/Library/Calendars/Calendar Cache")
CD_REF = datetime.datetime(2001, 1, 1, 0, 0, 0)
OUTPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'veckodata.json')

WEEKDAY_SV = {'Monday':'måndag','Tuesday':'tisdag','Wednesday':'onsdag','Thursday':'torsdag','Friday':'fredag','Saturday':'lördag','Sunday':'söndag'}
POOL = [
    ("Ta en promenad i skogen","ute","45 min"),("Åk till simhallen","aktivitet","1,5 h"),
    ("Städa ett rum i taget","hemma","30 min"),("Laga en nyttig middag","mat","1 h"),
    ("Läs en bok på balkongen","återhämtning","1 h"),("Boka in en massage","välmående","1 h"),
    ("Åk och handla veckans mat","ärenden","1,5 h"),("Rensa garderoben","hemma","2 h"),
    ("Gör rygg- och coreövningar","träning","20 min"),("Middag med vänner","socialt","3 h"),
    ("Spela ett brädspel","hemma","1 h"),("Testa ett nytt gympapass","träning","30 min"),
    ("Åk till återvinningsstationen","ärenden","30 min"),("Boka tid hos frisör","ärenden","15 min"),
    ("Gå på loppis","ute","1,5 h"),("Plantera om växter","ute","1 h"),
    ("Skriv en veckoplan för nästa vecka","planering","30 min"),("Bjud in någon på fika","socialt","1,5 h"),
    ("Testa ett nytt recept","mat","1 h"),("Åk till biblioteket","ute","1 h"),
    ("Gå en runda på stan","ute","1,5 h"),("Titta på en dokumentär","hemma","1 h"),
    ("Gör en ansiktsmask/hemmaspa","välmående","30 min"),("Åk och bada (sommar)","ute","3 h"),
    ("Plocka svamp/bär (höst)","ute","2 h"),
]

def cd2dt(ts):
    if not ts: return None
    return CD_REF + datetime.timedelta(seconds=ts)

def get_cal(days=14):
    if not os.path.exists(CAL_CACHE): return None, "Cache saknas"
    conn = sqlite3.connect(CAL_CACHE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT Z_PK,ZTITLE FROM ZNODE WHERE ZISEVENTCONTAINER=1 AND ZTITLE NOT NULL")
    cals = {r['Z_PK']:r['ZTITLE'] for r in cur.fetchall()}
    now = datetime.datetime.now()
    start_dt = now.replace(hour=0,minute=0,second=0,microsecond=0)
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


def build(days=14):
    evs, err = get_cal(days)
    if err: return {'error':err}
    now = datetime.datetime.now()
    start = now.replace(hour=0,minute=0,second=0,microsecond=0)
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
                suggestions.append({'activity':p[0],'category':p[1],'duration':p[2]})
                used.add(p[0])
        days_data.append({'date':dk,'weekday':wd,'events':de,'has_events':len(de)>0,'summary':summary,'suggestions':suggestions})
    busy = sum(1 for d in days_data if d['has_events']); free = days-busy
    return {'generated_at':datetime.datetime.now().isoformat(),'week_start':start.strftime('%Y-%m-%d'),'week_end':(start+datetime.timedelta(days=days-1)).strftime('%Y-%m-%d'),'days_covered':days,'busy_days':busy,'free_days':free,'total_events':len(evs),'week_overview':build_narrative(days_data),'days':days_data}

if __name__=='__main__':
    days = int(sys.argv[1]) if len(sys.argv)>1 else 14
    data = build(days)
    with open(OUTPUT,'w',encoding='utf-8') as f: json.dump(data,f,ensure_ascii=False,indent=2)
    print(json.dumps({'status':'ok','output':OUTPUT,'busy':data['busy_days'],'free':data['free_days'],'overview':data['week_overview']},ensure_ascii=False))
