import json
import time
import sys
import os
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(__file__))
import match as match_module
import trends as trends_module

_cache = {'data': None, 'ts': 0}
CACHE_SECONDS = 60

class app(BaseHTTPRequestHandler):
    def do_GET(self):
        global _cache
        now = time.time()
        if _cache['data'] and (now - _cache['ts']) < CACHE_SECONDS:
            result = _cache['data']
        else:
            match_data = match_module.get_live_match()
            home = (match_data or {}).get('home', 'brazil')
            away = (match_data or {}).get('away', 'morocco')
            trends_data = trends_module.get_trends(home, away)
            result = {'match': match_data, 'trends': trends_data, 'ts': int(now)}
            _cache = {'data': result, 'ts': now}

        body = json.dumps(result).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'public, max-age=60')
        self.end_headers()
        self.wfile.write(body)
