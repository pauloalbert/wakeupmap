import json
import time
import os
from http.server import BaseHTTPRequestHandler

_cache = {'data': None, 'ts': 0}
CACHE_SECONDS = 300

def get_trends(home_country, away_country):
    global _cache
    now = time.time()
    if _cache['data'] and (now - _cache['ts']) < CACHE_SECONDS:
        return _cache['data']
    try:
        from pytrends.request import TrendReq
        pytrends = TrendReq(hl='en-US', tz=0)
        terms = {
            'brazil':'Brazil World Cup','morocco':'Morocco World Cup',
            'france':'France World Cup','germany':'Germany World Cup',
            'spain':'Spain World Cup','england':'England World Cup',
            'argentina':'Argentina World Cup','usa':'USA World Cup',
            'japan':'Japan World Cup','southkorea':'South Korea World Cup',
            'portugal':'Portugal World Cup','netherlands':'Netherlands World Cup',
        }
        kw_list = list(filter(None, [terms.get(home_country,''), terms.get(away_country,'')]))[:5]
        if not kw_list:
            return {}
        pytrends.build_payload(kw_list, timeframe='now 1-H', geo='')
        df = pytrends.interest_by_region(resolution='COUNTRY', inc_low_vol=True)
        result = {}
        for kw in kw_list:
            if kw in df.columns:
                for country, val in df[kw].nlargest(5).items():
                    cid = country.lower().replace(' ','')
                    if cid not in result or result[cid] < val:
                        result[cid] = int(val)
        _cache = {'data': result, 'ts': now}
        return result
    except Exception as e:
        return {'_error': str(e)}

class app(BaseHTTPRequestHandler):
    def do_GET(self):
        qs = {}
        if '?' in self.path:
            for p in self.path.split('?')[1].split('&'):
                if '=' in p:
                    k,v = p.split('=',1)
                    qs[k]=v
        result = get_trends(qs.get('home','brazil'), qs.get('away','morocco'))
        body = json.dumps(result).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)
