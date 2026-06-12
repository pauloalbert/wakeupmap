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

def get_live_match():
    if not API_KEY:
        return None
    try:
        url = f'https://api.football-data.org/v4/competitions/{WC_ID}/matches?status=LIVE'
        req = urllib.request.Request(url, headers={'X-Auth-Token': API_KEY})
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read())
        matches = data.get('matches', [])
        if not matches:
            today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
            url2 = f'https://api.football-data.org/v4/competitions/{WC_ID}/matches?dateFrom={today}&dateTo={today}'
            req2 = urllib.request.Request(url2, headers={'X-Auth-Token': API_KEY})
            with urllib.request.urlopen(req2, timeout=5) as r2:
                data2 = json.loads(r2.read())
            matches = data2.get('matches', [])
        if not matches:
            return None
        m = matches[0]
        home_name = m['homeTeam']['name']
        away_name = m['awayTeam']['name']
        home_id = TEAM_MAP.get(home_name, home_name.lower().replace(' ',''))
        away_id = TEAM_MAP.get(away_name, away_name.lower().replace(' ',''))
        score = m.get('score', {})
        ft = score.get('fullTime', {})
        home_score = ft.get('home') or 0
        away_score = ft.get('away') or 0
        minute = m.get('minute', 0) or 0
        status = m.get('status', 'TIMED')
        return {
            'home': home_id, 'away': away_id,
            'homeName': home_name, 'awayName': away_name,
            'homeFlag': FLAGS.get(home_id, '🏳️'),
            'awayFlag': FLAGS.get(away_id, '🏳️'),
            'score': f"{home_score} — {away_score}",
            'minute': minute, 'status': status,
        }
    except Exception as e:
        return {'error': str(e)}

class app(BaseHTTPRequestHandler):
    def do_GET(self):
        result = get_live_match()
        body = json.dumps(result or {}).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)
