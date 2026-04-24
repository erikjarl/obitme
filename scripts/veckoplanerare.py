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
    parts = [d['summary'] for d in days_data]
    return {'generated_at':datetime.datetime.now().isoformat(),'week_start':start.strftime('%Y-%m-%d'),'week_end':(start+datetime.timedelta(days=days-1)).strftime('%Y-%m-%d'),'days_covered':days,'busy_days':busy,'free_days':free,'total_events':len(evs),'week_overview':' | '.join(parts),'days':days_data}

if __name__=='__main__':
    days = int(sys.argv[1]) if len(sys.argv)>1 else 14
    data = build(days)
    with open(OUTPUT,'w',encoding='utf-8') as f: json.dump(data,f,ensure_ascii=False,indent=2)
    print(json.dumps({'status':'ok','output':OUTPUT,'busy':data['busy_days'],'free':data['free_days'],'overview':data['week_overview']},ensure_ascii=False))
