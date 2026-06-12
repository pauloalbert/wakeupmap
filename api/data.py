import json
import os
import urllib.request
from datetime import datetime, timezone

def handler(request):
    api_key = os.environ.get('FOOTBALL_API_KEY', '')
    result = {'match': None, 'trends': {}, 'ts': 0}
    
    if api_key:
        try:
            today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
            url = f'https://api.football-data.org/v4/competitions/2000/matches?dateFrom={today}&dateTo={today}&status=LIVE'
            req = urllib.request.Request(url, headers={'X-Auth-Token': api_key})
            with urllib.request.urlopen(req, timeout=5) as r:
                data = json.loads(r.read())
            matches = data.get('matches', [])
            if matches:
                m = matches[0]
                hs = (m.get('score',{}).get('fullTime',{}).get('home') or 0)
                as_ = (m.get('score',{}).get('fullTime',{}).get('away') or 0)
                result['match'] = {
                    'homeName': m['homeTeam']['name'],
                    'awayName': m['awayTeam']['name'],
                    'score': f"{hs} — {as_}",
                    'minute': m.get('minute', 0),
                    'status': m.get('status', 'TIMED')
                }
        except Exception as e:
            result['error'] = str(e)
    
    return {
        'status': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(result)
    }
