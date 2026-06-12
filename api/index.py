import json
import os
import urllib.request
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler

API_KEY = os.environ.get('FOOTBALL_API_KEY', '')
WC_ID = 2000

TEAM_MAP = {
    'Brazil':'brazil','Morocco':'morocco','France':'france','Germany':'germany',
    'Spain':'spain','England':'england','Portugal':'portugal','Argentina':'argentina',
    'Netherlands':'netherlands','Belgium':'belgium','Croatia':'croatia',
    'Switzerland':'switzerland','Uruguay':'uruguay','Colombia':'colombia',
    'Mexico':'mexico','United States':'usa','Canada':'canada','Japan':'japan',
    'South Korea':'southkorea','Australia':'australia','Iran':'iran',
    'Saudi Arabia':'saudi','Qatar':'qatar','Senegal':'senegal','Ghana':'ghana',
    "Côte d'Ivoire":'ivory','Tunisia':'tunisia','Algeria':'algeria',
    'Egypt':'egypt','South Africa':'southafrica','Ecuador':'ecuador',
    'Paraguay':'paraguay','Panama':'panama','Haiti':'haiti',
    'Curaçao':'curacao','Cape Verde':'caboverde','Jordan':'jordan',
    'Uzbekistan':'uzbekistan','Scotland':'scotland','Turkey':'turkey',
    'Norway':'norway','Austria':'austria','Czech Republic':'czech',
    'Bosnia-Herzegovina':'bosnia','Sweden':'sweden','New Zealand':'newzealand',
}

FLAGS = {
    'brazil':'BR','morocco':'MA','france':'FR','germany':'DE',
    'spain':'ES','england':'GB-ENG','portugal':'PT','argentina':'AR',
    'netherlands':'NL','belgium':'BE','croatia':'HR','switzerland':'CH',
    'uruguay':'UY','colombia':'CO','mexico':'MX','usa':'US',
    'canada':'CA','japan':'JP','southkorea':'KR','australia':'AU',
    'iran':'IR','saudi':'SA','qatar':'QA','senegal':'SN',
    'ghana':'GH','ivory':'CI','tunisia':'TN','algeria':'DZ',
    'egypt':'EG','southafrica':'ZA','ecuador':'EC','paraguay':'PY',
    'panama':'PA','haiti':'HT','curacao':'CW','caboverde':'CV',
    'jordan':'JO','uzbekistan':'UZ','scotland':'GB-SCT','turkey':'TR',
    'norway':'NO','austria':'AT','czech':'CZ','bosnia':'BA',
    'sweden':'SE','newzealand':'NZ',
}

FLAG_EMOJI = {
    'brazil':'🇧🇷','morocco':'🇲🇦','france':'🇫🇷','germany':'🇩🇪',
    'spain':'🇪🇸','england':'🏴󠁧󠁢󠁥󠁮󠁧󠁿','portugal':'🇵🇹','argentina':'🇦🇷',
    'netherlands':'🇳🇱','belgium':'🇧🇪','croatia':'🇭🇷','switzerland':'🇨🇭',
    'uruguay':'🇺🇾','colombia':'🇨🇴','mexico':'🇲🇽','usa':'🇺🇸',
    'canada':'🇨🇦','japan':'🇯🇵','southkorea':'🇰🇷','australia':'🇦🇺',
    'iran':'🇮🇷','saudi':'🇸🇦','qatar':'🇶🇦','senegal':'🇸🇳',
    'ghana':'🇬🇭','ivory':'🇨🇮','tunisia':'🇹🇳','algeria':'🇩🇿',
    'egypt':'🇪🇬','southafrica':'🇿🇦','ecuador':'🇪🇨','paraguay':'🇵🇾',
    'panama':'🇵🇦','haiti':'🇭🇹','curacao':'🇨🇼','caboverde':'🇨🇻',
    'jordan':'🇯🇴','uzbekistan':'🇺🇿','scotland':'🏴󠁧󠁢󠁳󠁣󠁴󠁿','turkey':'🇹🇷',
    'norway':'🇳🇴','austria':'🇦🇹','czech':'🇨🇿','bosnia':'🇧🇦',
    'sweden':'🇸🇪','newzealand':'🇳🇿',
}

def get_match():
    if not API_KEY:
        return None
    try:
        # Try live first
        url = f'https://api.football-data.org/v4/competitions/{WC_ID}/matches?status=LIVE'
        req = urllib.request.Request(url, headers={'X-Auth-Token': API_KEY})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read())
        matches = data.get('matches', [])

        # If no live, get today's matches
        if not matches:
            today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
            url2 = f'https://api.football-data.org/v4/competitions/{WC_ID}/matches?dateFrom={today}&dateTo={today}'
            req2 = urllib.request.Request(url2, headers={'X-Auth-Token': API_KEY})
            with urllib.request.urlopen(req2, timeout=8) as r2:
                data2 = json.loads(r2.read())
            matches = data2.get('matches', [])

        if not matches:
            return None

        # Prefer live or in-play match
        live = [m for m in matches if m.get('status') in ('IN_PLAY','PAUSED')]
        m = live[0] if live else matches[0]

        home_name = m['homeTeam']['name']
        away_name = m['awayTeam']['name']
        home_id = TEAM_MAP.get(home_name, home_name.lower().replace(' ',''))
        away_id = TEAM_MAP.get(away_name, away_name.lower().replace(' ',''))

        score = m.get('score', {})
        ft = score.get('fullTime', {})
        ht = score.get('halfTime', {})
        home_score = ft.get('home') if ft.get('home') is not None else (ht.get('home') or 0)
        away_score = ft.get('away') if ft.get('away') is not None else (ht.get('away') or 0)
        minute = m.get('minute', 0) or 0
        status = m.get('status', 'TIMED')

        return {
            'home': home_id,
            'away': away_id,
            'homeName': home_name,
            'awayName': away_name,
            'homeFlag': FLAG_EMOJI.get(home_id, '🏳️'),
            'awayFlag': FLAG_EMOJI.get(away_id, '🏳️'),
            'score': f"{home_score} — {away_score}",
            'minute': minute,
            'status': status,
        }
    except Exception as e:
        return {'error': str(e)}

def get_trends(home, away):
    try:
        from pytrends.request import TrendReq
        pt = TrendReq(hl='en-US', tz=0, timeout=(5,10))

        name_map = {
            'brazil':'Brazil','morocco':'Morocco','france':'France',
            'germany':'Germany','spain':'Spain','england':'England',
            'argentina':'Argentina','usa':'United States','japan':'Japan',
            'southkorea':'South Korea','portugal':'Portugal','netherlands':'Netherlands',
            'mexico':'Mexico','colombia':'Colombia','canada':'Canada',
            'australia':'Australia','saudi':'Saudi Arabia','iran':'Iran',
            'senegal':'Senegal','ghana':'Ghana','ivory':'Ivory Coast',
            'southafrica':'South Africa','egypt':'Egypt','turkey':'Turkey',
            'croatia':'Croatia','belgium':'Belgium','switzerland':'Switzerland',
        }

        # Build keyword list: home + away + top others
        others = ['France','Germany','Spain','England','Argentina','Japan']
        kw = []
        h = name_map.get(home, home.title())
        a = name_map.get(away, away.title())
        for w in [h, a] + others:
            if w not in kw:
                kw.append(w)
        kw = kw[:5]

        pt.build_payload(kw, cat=20, timeframe='now 1-H', geo='')
        df = pt.interest_over_time()
        if df is None or df.empty:
            return {}

        # Get latest values
        latest = df.iloc[-1]
        result = {}
        rev_map = {v:k for k,v in name_map.items()}
        for col in kw:
            if col in latest:
                cid = rev_map.get(col, col.lower().replace(' ',''))
                result[cid] = int(latest[col])

        return result
    except Exception as e:
        return {'_error': str(e)}


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        match_data = get_match()
        home = (match_data or {}).get('home', 'brazil')
        away = (match_data or {}).get('away', 'morocco')
        trends_data = get_trends(home, away)

        result = {
            'match': match_data,
            'trends': trends_data,
        }

        body = json.dumps(result, ensure_ascii=False).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'public, max-age=60')
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass  # suppress logs
