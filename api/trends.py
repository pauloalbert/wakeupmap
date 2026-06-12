import json
import os
import urllib.request
import urllib.parse
from http.server import BaseHTTPRequestHandler

_cache = {}
CACHE_SECONDS = 300

def get_trends(home, away):
    import time
    cache_key = home + '_' + away
    now = time.time()
    if cache_key in _cache and (now - _cache[cache_key]['ts']) < CACHE_SECONDS:
        return _cache[cache_key]['data']

    kw_map = {
        'brazil':'Brazil','morocco':'Morocco','france':'France',
        'germany':'Germany','spain':'Spain','england':'England',
        'argentina':'Argentina','usa':'United States','japan':'Japan',
        'southkorea':'South Korea','portugal':'Portugal',
        'netherlands':'Netherlands','mexico':'Mexico','colombia':'Colombia',
        'turkey':'Turkey','australia':'Australia','czechia':'Czechia',
        'czech':'Czechia','senegal':'Senegal','ghana':'Ghana',
        'southafrica':'South Africa','algeria':'Algeria','egypt':'Egypt',
        'uruguay':'Uruguay','ecuador':'Ecuador','canada':'Canada',
        'croatia':'Croatia','italy':'Italy','serbia':'Serbia',
        'switzerland':'Switzerland','austria':'Austria','belgium':'Belgium',
        'norway':'Norway','sweden':'Sweden','iran':'Iran','saudi':'Saudi Arabia',
        'qatar':'Qatar','jordan':'Jordan','uzbekistan':'Uzbekistan',
        'haiti':'Haiti','curacao':'Curacao','caboverde':'Cape Verde',
        'scotland':'Scotland','panama':'Panama','paraguay':'Paraguay',
        'newzealand':'New Zealand','ivory':'Ivory Coast','tunisia':'Tunisia',
    }

    kw1 = kw_map.get(home, home.title())
    kw2 = kw_map.get(away, away.title())
    extras = [k for k in ['France','Germany','Spain','Argentina','Japan']
              if k != kw1 and k != kw2][:3]
    keywords = [kw1, kw2] + extras

    try:
        from pytrends.request import TrendReq
        pt = TrendReq(hl='en-US', tz=0, timeout=(8, 15),
                      requests_args={'verify': False})
        pt.build_payload(keywords, cat=20, timeframe='now 1-H', geo='')
        df = pt.interest_over_time()

        if df is None or df.empty:
            return {}

        latest = df.iloc[-1]
        result = {}
        rev = {v: k for k, v in kw_map.items()}
        for kw in keywords:
            if kw in latest:
                cid = rev.get(kw, kw.lower().replace(' ', ''))
                result[cid] = int(latest[kw])

        _cache[cache_key] = {'data': result, 'ts': now}
        return result

    except Exception as e:
        # Try alternative: Google Trends via direct HTTP
        try:
            result = get_trends_direct(kw1, kw2)
            if result:
                _cache[cache_key] = {'data': result, 'ts': now}
                return result
        except Exception:
            pass
        return {'_error': str(e)}


def get_trends_direct(kw1, kw2):
    """Fallback: call Google Trends explore API directly"""
    req_obj = json.dumps({
        'comparisonItem': [
            {'keyword': kw1, 'geo': '', 'time': 'now 1-H'},
            {'keyword': kw2, 'geo': '', 'time': 'now 1-H'},
            {'keyword': 'France', 'geo': '', 'time': 'now 1-H'},
            {'keyword': 'Germany', 'geo': '', 'time': 'now 1-H'},
            {'keyword': 'Spain', 'geo': '', 'time': 'now 1-H'},
        ],
        'category': 0,
        'property': ''
    })

    explore_url = ('https://trends.google.com/trends/api/explore'
                   '?hl=en-US&tz=-60&req=' + urllib.parse.quote(req_obj))

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://trends.google.com/trends/',
    }

    req = urllib.request.Request(explore_url, headers=headers)
    with urllib.request.urlopen(req, timeout=12) as r:
        text = r.read().decode('utf-8')

    # Strip )]}',\n prefix
    start = text.find('{')
    if start < 0:
        return {}

    data = json.loads(text[start:])
    widgets = data.get('widgets', [])
    ts_widget = next((w for w in widgets if w.get('id') == 'TIMESERIES'), None)
    if not ts_widget:
        return {}

    token = ts_widget['token']
    widget_req = json.dumps(ts_widget['request'])

    data_url = ('https://trends.google.com/trends/api/widgetdata/multiline'
                '?hl=en-US&tz=-60'
                '&req=' + urllib.parse.quote(widget_req) +
                '&token=' + urllib.parse.quote(token) +
                '&geo=')

    req2 = urllib.request.Request(data_url, headers=headers)
    with urllib.request.urlopen(req2, timeout=12) as r2:
        text2 = r2.read().decode('utf-8')

    start2 = text2.find('{')
    if start2 < 0:
        return {}

    tdata = json.loads(text2[start2:])
    lines = (tdata.get('default') or {}).get('timelineData', [])
    if not lines:
        return {}

    latest = lines[-1]
    values = latest.get('value', [])
    keywords_order = [kw1, kw2, 'France', 'Germany', 'Spain']

    kw_to_id = {
        kw1: kw1.lower().replace(' ', ''),
        kw2: kw2.lower().replace(' ', ''),
        'France': 'france', 'Germany': 'germany', 'Spain': 'spain',
    }

    result = {}
    for i, kw in enumerate(keywords_order[:len(values)]):
        cid = kw_to_id.get(kw, kw.lower().replace(' ', ''))
        result[cid] = int(values[i])

    return result


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        qs = {}
        if '?' in self.path:
            for p in self.path.split('?')[1].split('&'):
                if '=' in p:
                    k, v = p.split('=', 1)
                    qs[k] = v

        home = qs.get('home', 'brazil')
        away = qs.get('away', 'morocco')
        result = get_trends(home, away)

        body = json.dumps(result).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'public, max-age=300')
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass
