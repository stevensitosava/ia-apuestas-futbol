# src/data_fetcher.py
import requests
from datetime import datetime, timedelta, timezone

def get_future_odds_from_api(api_key: str, league: str, regions: str, markets: str, hours_ahead: int):
    """Pide a The Odds API las cuotas para un rango de tiempo futuro."""
    time_now = datetime.now(timezone.utc)
    time_future = time_now + timedelta(hours=hours_ahead)
    commence_time_from = time_now.strftime('%Y-%m-%dT%H:%M:%SZ')
    commence_time_to = time_future.strftime('%Y-%m-%dT%H:%M:%SZ')

    uri = f"https://api.the-odds-api.com/v4/sports/{league}/odds"
    params = {'apiKey': api_key, 'regions': regions, 'markets': markets, 'oddsFormat': 'decimal', 'commenceTimeFrom': commence_time_from, 'commenceTimeTo': commence_time_to}
    
    try:
        response = requests.get(uri, params=params)
        response.raise_for_status()
        print(f"Peticiones restantes a The Odds API: {response.headers.get('x-requests-remaining')}")
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error al conectar con The Odds API (cuotas): {e}")
        return []

def get_recent_scores_from_api(api_key: str, league: str, days_ago: int = 3):
    """NUEVA FUNCIÓN: Pide a The Odds API los resultados de partidos recientes."""
    uri = f"https://api.the-odds-api.com/v4/sports/{league}/scores"
    params = {'apiKey': api_key, 'daysFrom': days_ago}
    
    try:
        response = requests.get(uri, params=params)
        response.raise_for_status()
        print(f"Peticiones restantes a The Odds API: {response.headers.get('x-requests-remaining')}")
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error al conectar con The Odds API (resultados): {e}")
        return []
    
