import json
import os
import time

# Simple cache to avoid hammering Google
_cache = {'data': None, 'ts': 0}
CACHE_SECONDS = 300  # 5 minutes

def get_trends(home_country, away_country):
    global _cache
    now = time.time()
    if _cache['data'] and (now - _cache['ts']) < CACHE_SECONDS:
        return _cache['data']
    try:
        from pytrends.request import TrendReq
        pytrends = TrendReq(hl='en-US', tz=0)
        # Search terms for each country
        terms = {
            'brazil': 'Brazil World Cup',
            'morocco': 'Morocco World Cup',
            'france': 'France World Cup',
            'germany': 'Germany World Cup',
            'spain': 'Spain World Cup',
            'england': 'England World Cup',
            'argentina': 'Argentina World Cup',
            'usa': 'USA World Cup',
            'japan': 'Japan World Cup',
            'southkorea': 'South Korea World Cup',
        }
        kw_list = [terms.get(home_country,''), terms.get(away_country,'')]
        kw_list = [k for k in kw_list if k][:5]
        if not kw_list:
            return {}
        pytrends.build_payload(kw_list, timeframe='now 1-H', geo='')
        df = pytrends.interest_by_region(resolution='COUNTRY', inc_low_vol=True)
        result = {}
        for kw in kw_list:
            if kw in df.columns:
                top = df[kw].nlargest(5)
                for country, val in top.items():
                    cid = country.lower().replace(' ','')
                    if cid not in result or result[cid] < val:
                        result[cid] = int(val)
        _cache = {'data': result, 'ts': now}
        return result
    except Exception as e:
        return {'_error': str(e)}

def handler(request):
    params = request.get('queryStringParameters') or {}
    home = params.get('home','brazil')
    away = params.get('away','morocco')
    result = get_trends(home, away)
    return {
        'statusCode': 200,
        'headers': {'Content-Type':'application/json','Access-Control-Allow-Origin':'*'},
        'body': json.dumps(result)
    }
