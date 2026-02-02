from flask import Flask, render_template, request, jsonify
import requests
from datetime import datetime
from collections import Counter
import concurrent.futures
import numpy as np
from functools import lru_cache
import time

app = Flask(__name__)
API_KEY = "6b6c814eef8f484a2386fc70dac93027"

# Initialize Session for TCP Keep-Alive (Optimized for Mac M2 performance)
http = requests.Session()
http.params = {'api_key': API_KEY}

# In-memory storage
DETAILS_CACHE = {}

def get_detailed_info_fast(m_type, m_id):
    """Consolidated fetch: Details and Watch Providers in 1 call."""
    cache_key = f"{m_type}_{m_id}"
    if cache_key in DETAILS_CACHE: return DETAILS_CACHE[cache_key]
    
    url = f"https://api.themoviedb.org/3/{m_type}/{m_id}"
    params = {'append_to_response': 'watch/providers'}
    
    try:
        res = http.get(url, params=params, timeout=2).json()
        watch_data = res.get('watch/providers', {}).get('results', {}).get('IN', {})
        streaming = [p['provider_name'] for p in watch_data.get('flatrate', [])]
        watch_info = ", ".join(streaming) if streaming else "Not Available for Streaming"

        result = {
            'genres': [g['id'] for g in res.get('genres', [])],
            'vote_average': res.get('vote_average', 0),
            'overview': res.get('overview', 'No description available.'),
            'watch': watch_info
        }
        DETAILS_CACHE[cache_key] = result
        return result
    except:
        return None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/get_trending')
def get_trending():
    res = http.get("https://api.themoviedb.org/3/trending/all/day").json().get('results', [])[:18]
    trending = []
    for m in res:
        release = m.get('release_date') or m.get('first_air_date') or "2026"
        trending.append({
            "id": m['id'],
            "title": m.get('title') or m.get('name'),
            "type": m.get('media_type', 'movie'),
            "rating": m.get('vote_average', 0),
            "poster": f"https://image.tmdb.org/t/p/w500{m['poster_path']}",
            "year": release[:4],
            "overview": m.get('overview', '')
        })
    return jsonify(trending)

@app.route('/get_recommendations', methods=['POST'])
def get_recommendations():
    start_time = time.time()
    watched = request.json.get('watched_movies', [])
    watched_ids = {m['id'] for m in watched}
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        profiles = list(executor.map(lambda x: get_detailed_info_fast(x['type'], x['id']), watched))
    
    profiles = [p for p in profiles if p]
    genre_pref = Counter([g for p in profiles for g in p['genres']])

    candidate_pool = {}
    def fetch_neighbors(m):
        try:
            return http.get(f"https://api.themoviedb.org/3/{m['type']}/{m['id']}/recommendations").json().get('results', [])[:10]
        except: return []

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        results = executor.map(fetch_neighbors, watched[-5:])
        for batch in results:
            for c in batch:
                if c['id'] not in watched_ids and c.get('poster_path'):
                    candidate_pool[c['id']] = c

    def score_item(c_id):
        cand = candidate_pool[c_id]
        m_type = cand.get('media_type', 'movie')
        details = get_detailed_info_fast(m_type, c_id)
        if not details: return None
        
        score = (details['vote_average'] / 10) * 40
        overlap = set(details['genres']).intersection(set(genre_pref.keys()))
        score += len(overlap) * 15
        
        return {
            "id": c_id, "title": cand.get('title') or cand.get('name'),
            "type": m_type, "rating": cand.get('vote_average', 0),
            "poster": f"https://image.tmdb.org/t/p/w500{cand['poster_path']}",
            "year": (cand.get('release_date') or cand.get('first_air_date') or "2026")[:4],
            "overview": details['overview'], "watch": details['watch'], "score": min(100, score)
        }

    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        scored = list(executor.map(score_item, list(candidate_pool.keys())[:40]))
    
    final_recs = sorted([s for s in scored if s], key=lambda x: x['score'], reverse=True)[:18]
    return jsonify({"status": "success", "data": final_recs, "processing_time": f"{time.time() - start_time:.2f}s"})

@app.route('/search')
def search():
    query = request.args.get('q')
    if not query: return jsonify([])
    res = http.get("https://api.themoviedb.org/3/search/multi", params={'query': query}).json()
    results = []
    for m in res.get('results', []):
        if m.get('media_type') in ['movie', 'tv'] and m.get('poster_path'):
            results.append({
                "id": m['id'], 
                "title": m.get('title') or m.get('name'),
                "type": m.get('media_type'), 
                "banner": f"https://image.tmdb.org/t/p/w92{m['poster_path']}"
            })
    return jsonify(results[:5])

if __name__ == '__main__':
    app.run(debug=True, port=5001, threaded=True)
