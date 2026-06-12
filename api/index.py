import json
import os
import urllib.request
from datetime import datetime, timezone, timedelta
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
    "Cote d'Ivoire":'ivory',"Côte d'Ivoire":'ivory','Tunisia':'tunisia',
    'Algeria':'algeria','Egypt':'egypt','South Africa':'southafrica',
    'Ecuador':'ecuador','Paraguay':'paraguay','Panama':'panama',
    'Haiti':'haiti','Curacao':'curacao','Curaçao':'curacao',
    'Cape Verde':'caboverde','Jordan':'jordan','Uzbekistan':'uzbekistan',
    'Scotland':'scotland','Turkey':'turkey','Norway':'norway',
    'Austria':'austria','Czech Republic':'czech','Czechia':'czechia',
    'Bosnia-Herzegovina':'bosnia','Sweden':'sweden','New Zealand':'newzealand',
    'Colombia':'colombia','Chile':'chile','Peru':'peru','Serbia':'serbia',
    'Italy':'italy','Croatia':'croatia',
}

def fetch_json(url):
    req = urllib.request.Request(url, headers={'X-Auth-Token': API_KEY})
    with urllib.request.urlopen(req, timeout=8) as r:
        return json.loads(r.read())

def parse_match(m):
    home_name = m['homeTeam']['name']
    away_name = m['awayTeam']['name']
    home_id = TEAM_MAP.get(home_name, home_name.lower().replace(' ','').replace('-',''))
    away_id = TEAM_MAP.get(away_name, away_name.lower().replace(' ','').replace('-',''))
    score = m.get('score', {})
    ft = score.get('fullTime', {})
    hs = ft.get('home') if ft.get('home') is not None else 0
    as_ = ft.get('away') if ft.get('away') is not None else 0
    return {
        'home': home_id, 'away': away_id,
        'homeName': home_name, 'awayName': away_name,
        'score': str(hs) + ' - ' + str(as_),
        'minute': m.get('minute', 0) or 0,
        'status': m.get('status', 'TIMED'),
        'utcDate': m.get('utcDate',''),
    }

def get_matches():
    if not API_KEY:
        return None, None, None
    try:
        now = datetime.now(timezone.utc)
        today = now.strftime('%Y-%m-%d')
        tomorrow = (now + timedelta(days=1)).strftime('%Y-%m-%d')
        yesterday = (now - timedelta(days=1)).strftime('%Y-%m-%d')

        # Get live matches
        live_data = fetch_json('https://api.football-data.org/v4/competitions/'+str(WC_ID)+'/matches?status=LIVE')
        live_matches = live_data.get('matches', [])

        if live_matches:
            live = [m for m in live_matches if m.get('status') in ('IN_PLAY','PAUSED')]
            current = live[0] if live else live_matches[0]
            current_parsed = parse_match(current)

            # Get next scheduled
            next_data = fetch_json('https://api.football-data.org/v4/competitions/'+str(WC_ID)+'/matches?status=TIMED&dateFrom='+today+'&dateTo='+tomorrow)
            next_matches = next_data.get('matches', [])
            next_parsed = parse_match(next_matches[0]) if next_matches else None

            return current_parsed, None, next_parsed

        # No live match — get today's finished + upcoming
        range_data = fetch_json('https://api.football-data.org/v4/competitions/'+str(WC_ID)+'/matches?dateFrom='+yesterday+'&dateTo='+tomorrow)
        all_matches = range_data.get('matches', [])

        finished = [m for m in all_matches if m.get('status') == 'FINISHED']
        upcoming = [m for m in all_matches if m.get('status') in ('TIMED','SCHEDULED')]

        last = parse_match(finished[-1]) if finished else None
        next_m = parse_match(upcoming[0]) if upcoming else None

        # Return the most recent finished as "current" with FINISHED status
        if finished:
            current = parse_match(finished[-1])
            return current, last, next_m
        elif upcoming:
            current = parse_match(upcoming[0])
            return current, last, next_m

        return None, last, next_m

    except Exception as e:
        return {'error': str(e)}, None, None


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        current, last, next_match = get_matches()
        result = {
            'match': current,
            'last': last,
            'next': next_match,
        }
        body = json.dumps(result, ensure_ascii=False).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'public, max-age=30')
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass
