import json
import time
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
import match as match_module
import trends as trends_module

_cache = {'data': None, 'ts': 0}
CACHE_SECONDS = 60

def handler(request):
    global _cache
    now = time.time()
    if _cache['data'] and (now - _cache['ts']) < CACHE_SECONDS:
        return {
            'statusCode': 200,
            'headers': {'Content-Type':'application/json','Access-Control-Allow-Origin':'*','Cache-Control':'public, max-age=60'},
            'body': json.dumps(_cache['data'])
        }
    # Get live match
    match_data = match_module.get_live_match()
    home = (match_data or {}).get('home','brazil')
    away = (match_data or {}).get('away','morocco')
    # Get trends for those countries
    trends_data = trends_module.get_trends(home, away)
    result = {
        'match': match_data,
        'trends': trends_data,
        'ts': int(now)
    }
    _cache = {'data': result, 'ts': now}
    return {
        'statusCode': 200,
        'headers': {'Content-Type':'application/json','Access-Control-Allow-Origin':'*','Cache-Control':'public, max-age=60'},
        'body': json.dumps(result)
    }
